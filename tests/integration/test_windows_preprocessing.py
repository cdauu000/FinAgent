import hashlib
import io
import os
import struct
import zlib
from pathlib import Path

import pytest

from finagent.contracts.geometry import Affine
from finagent.extraction.media import WindowsMedia, png_dimensions
from finagent.extraction.preprocess import ImagePreprocessor
from finagent.ingestion.contracts import FileInput
from finagent.ingestion.service import LocalIngestionGateway
from finagent.jobs.memory import MemoryJobStore
from finagent.store.local_blob import LocalBlobStore
from finagent.store.models import BlobMetadata, BoundingBox


def png(width: int, height: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        )

    rows = []
    for y in range(height):
        row = bytes(
            0 if 25 < x < width - 25 and y % 20 in (9, 10, 11) else 255 for x in range(width)
        )
        rows.append(b"\x00" + row)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"".join(rows)))
        + chunk(b"IEND", b"")
    )


@pytest.mark.integration
def test_actual_windows_pdf_render_rotation_crop_geometry(tmp_path, processing_ctx) -> None:
    if os.name != "nt":
        pytest.skip("NOT_RUN: Windows.Data.Pdf unavailable on this platform")
    root = Path(__file__).resolve().parents[2]
    report = root / "data/public_reports/20260424_-_FPT_-_BCTC_rieng_Quy_1_nam_2026_1777344035.pdf"
    if not report.is_file():
        pytest.skip("NOT_RUN: supplied report absent")
    original = hashlib.sha256(report.read_bytes()).hexdigest()
    media = WindowsMedia(tmp_path / "work")
    info = media.inspect_path(report)
    assert info.page_count == 28 and info.pages[5].width_dip > info.pages[5].height_dip
    blobs = LocalBlobStore(tmp_path / "blobs", images=media)
    jobs = MemoryJobStore()
    ingestion = LocalIngestionGateway(blobs, jobs, media)
    receipt = ingestion.submit(
        report.read_bytes(),
        FileInput(
            filename="report.pdf", declared_mime="application/pdf", idempotency_key="supplied-fpt"
        ),
        processing_ctx,
    )
    assert receipt.sha256 == original and receipt.page_count == 28
    assert jobs.get(receipt.job_id, processing_ctx).state == "QUEUED"
    with blobs.open(receipt.blob_ref, processing_ctx) as stored:
        assert hashlib.sha256(stored.read()).hexdigest() == original
    page = ImagePreprocessor(media, tmp_path / "output").prepare(
        report, 5, processing_ctx, dpi=400, rotation=90, deskew_degrees=1.25
    )
    assert png_dimensions(tmp_path / "output" / page.processed_image) == (page.width, page.height)
    assert abs(page.original_width / page.source_width_dip * 96 - 400) < 1
    assert abs(page.original_height / page.source_height_dip * 96 - 400) < 1
    forward = Affine(*page.source_to_processed)
    inverse = Affine(*page.processed_to_source)
    assert inverse.point(*forward.point(200, 300)) == pytest.approx((200, 300))
    crop = tmp_path / "crop.png"
    media.crop(
        tmp_path / "output" / page.original_image,
        BoundingBox(x1=10.2, y1=20.2, x2=100.1, y2=80.1),
        crop,
    )
    assert png_dimensions(crop) == (91, 61)
    image_bytes = crop.read_bytes()
    image_ref = blobs.put(
        io.BytesIO(image_bytes),
        BlobMetadata(
            tenant_id=processing_ctx.tenant_id,
            source_tier=processing_ctx.source_tier,
            mime_type="image/png",
            sha256=hashlib.sha256(image_bytes).hexdigest(),
        ),
        processing_ctx,
    )
    crop_ref = blobs.crop(image_ref, BoundingBox(x1=1, y1=2, x2=20, y2=22), None, processing_ctx)
    with blobs.open(crop_ref.blob_ref, processing_ctx) as stored_crop:
        path = tmp_path / "stored-crop.png"
        path.write_bytes(stored_crop.read())
        assert png_dimensions(path) == (19, 20)
    assert (
        blobs.metadata(crop_ref.blob_ref, processing_ctx).source_tier == processing_ctx.source_tier
    )
    assert (
        page.source_tier == processing_ctx.source_tier
        and page.orientation_status == "USER_SELECTED"
    )
    assert hashlib.sha256(report.read_bytes()).hexdigest() == original


@pytest.mark.integration
def test_actual_skew_signal_on_synthetic_geometry_only(tmp_path) -> None:
    if os.name != "nt":
        pytest.skip("NOT_RUN: System.Drawing unavailable on this platform")
    source = tmp_path / "lines.png"
    source.write_bytes(png(500, 400))
    media = WindowsMedia(tmp_path / "work")
    rotated = tmp_path / "tilted.png"
    media.transform(source, rotated, deskew_degrees=2)
    signal = media.estimate_skew(rotated)
    assert signal.angle_degrees is not None and abs(signal.angle_degrees + 2) <= 0.5
    assert signal.ink_points and signal.projection_score
    corrected = tmp_path / "corrected.png"
    media.transform(rotated, corrected, deskew_degrees=signal.angle_degrees)
    assert abs(media.estimate_skew(corrected).angle_degrees or 0) <= 0.5
    # Geometric fixture is never registered as a report, gold label or OCR accuracy sample.
