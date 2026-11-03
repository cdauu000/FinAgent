import math
import struct

import pytest

from finagent.contracts.geometry import Affine, crop_bounds, expanded_rotation
from finagent.extraction.media import png_dimensions
from finagent.ingestion.errors import ProcessingError
from finagent.router.pages import DocumentRouter, PageFeatures
from finagent.store.models import BoundingBox


@pytest.mark.parametrize("degrees", [0, 90, 180, 270, -3.25, 4.5])
def test_expanded_transform_round_trip_and_bounds(degrees) -> None:
    transform, w, h = expanded_rotation(700, 1000, degrees)
    for point in [(0, 0), (700, 1000), (315.25, 204.75)]:
        mapped = transform.point(*point)
        assert transform.inverse().point(*mapped) == pytest.approx(point)
        assert -1e-9 <= mapped[0] <= w and -1e-9 <= mapped[1] <= h
    if degrees in (90, 270):
        assert (w, h) == (1000, 700)
    assert Affine(a=2, d=3).then(transform).point(10, 10) == pytest.approx(transform.point(20, 30))


def test_bad_geometry_and_pixel_bombs_rejected(tmp_path) -> None:
    with pytest.raises(ProcessingError):
        Affine(a=0, d=0)
    with pytest.raises(ProcessingError):
        Affine(e=math.nan)
    with pytest.raises(ProcessingError, match="CROP_OUTSIDE_RASTER"):
        crop_bounds(BoundingBox(x1=0, y1=0, x2=101, y2=50), 100, 100)
    bomb = tmp_path / "bomb.png"
    bomb.write_bytes(
        b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 100000, 100000)
    )
    with pytest.raises(ProcessingError, match="RASTER_PIXEL_LIMIT"):
        png_dimensions(bomb)


def test_signature_does_not_make_whole_file_native_and_unknown_orientation_needs_review(
    processing_ctx,
) -> None:
    text = "Báo cáo tài chính. " * 10
    pages = (
        PageFeatures(
            document_ref="doc-a",
            physical_index=0,
            native_text=text,
            native_body_aligned=True,
            image_area_fraction=0.01,
            orientation_degrees=0,
        ),
        PageFeatures(
            document_ref="doc-a",
            physical_index=1,
            native_text=text,
            native_body_aligned=True,
            signature_only_text=True,
            image_area_fraction=1,
        ),
        PageFeatures(
            document_ref="doc-a",
            physical_index=2,
            native_text=text,
            native_body_aligned=True,
            image_area_fraction=0.9,
            orientation_degrees=180,
        ),
        PageFeatures(document_ref="doc-a", physical_index=3),
    )
    plans = DocumentRouter().route(pages, processing_ctx)
    assert [p.route for p in plans] == ["text", "ocr", "hybrid", "ocr"]
    assert plans[3].page_kind == "unknown" and "ORIENTATION_REVIEW_REQUIRED" in plans[3].reasons
    assert plans[2].orientation_degrees == 180
