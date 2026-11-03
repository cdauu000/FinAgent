"""Windows PDF/image adapter. No OCR, network or package installation."""

import base64
import json
import math
import os
import shutil
import struct
import subprocess
import tempfile
from dataclasses import asdict
from pathlib import Path

from pydantic import Field

from finagent.contracts.base import Contract, SafeInt
from finagent.extraction.geometry import Affine, crop_bounds, expanded_rotation
from finagent.ingestion.contracts import PdfInspection
from finagent.ingestion.errors import ProcessingError
from finagent.store.models import BoundingBox

MAX_RASTER_PIXELS = 100_000_000


def png_dimensions(source: Path) -> tuple[int, int]:
    with source.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ProcessingError("INVALID_PNG_HEADER")
    width, height = struct.unpack(">II", header[16:24])
    if not width or not height or width * height > MAX_RASTER_PIXELS:
        raise ProcessingError("RASTER_PIXEL_LIMIT")
    return width, height


class MediaResult(Contract):
    ok: bool
    code: str | None = None
    page_count: SafeInt | None = None
    password_protected: bool = False
    pages: tuple["PdfPageInfo", ...] = ()
    width: SafeInt | None = None
    height: SafeInt | None = None
    width_dip: float | None = None
    height_dip: float | None = None
    intrinsic_rotation: SafeInt | None = None
    logical_dpi: float | None = None
    requested_width: SafeInt | None = None
    requested_height: SafeInt | None = None
    actual_matrix: tuple[float, ...] = ()
    angle_degrees: float | None = None
    projection_score: float | None = None
    runner_up_score: float | None = None
    ink_points: SafeInt | None = None
    peak_working_set_bytes: SafeInt = Field(ge=0)


class PdfPageInfo(Contract):
    physical_index: SafeInt
    width_dip: float
    height_dip: float
    intrinsic_rotation: SafeInt


MediaResult.model_rebuild()


def parse_media_result(content: bytes) -> MediaResult:
    try:
        result = MediaResult.model_validate_json(content.decode("utf-8-sig"))
    except (ValueError, UnicodeError):
        raise ProcessingError("WINDOWS_MEDIA_PROTOCOL_ERROR") from None
    if not result.ok:
        raise ProcessingError("WINDOWS_MEDIA_FAILED")
    return result


def bind_raster_dimensions(result: MediaResult, width: int, height: int) -> MediaResult:
    if (
        result.logical_dpi is None
        or not math.isfinite(result.logical_dpi)
        or result.logical_dpi <= 0
    ):
        raise ProcessingError("INVALID_LOGICAL_DPI")
    tolerance = math.ceil(result.logical_dpi / 96 / 2)
    if (
        result.width is None
        or result.height is None
        or (abs(result.width - width) > tolerance or abs(result.height - height) > tolerance)
    ):
        raise ProcessingError("RASTER_DIMENSION_MISMATCH")
    return result.model_copy(
        update={
            "width": width,
            "height": height,
            "requested_width": result.width,
            "requested_height": result.height,
        }
    )


class WindowsMedia:
    def __init__(self, workdir: Path) -> None:
        self.workdir = workdir.resolve()
        self.workdir.mkdir(parents=True, exist_ok=True)

    def call(self, request: dict[str, object]) -> MediaResult:
        executable = shutil.which("powershell")
        if os.name != "nt" or executable is None:
            raise ProcessingError("WINDOWS_MEDIA_UNAVAILABLE")
        with tempfile.TemporaryDirectory(dir=self.workdir) as directory:
            request_path = Path(directory) / "request.json"
            request_path.write_text(json.dumps(request), encoding="utf-8")
            script = Path(__file__).with_name("windows_media.ps1").read_text(encoding="utf-8")
            encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
            environment = {
                key: value
                for key, value in os.environ.items()
                if key.upper()
                in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "USERPROFILE", "LOCALAPPDATA"}
            }
            environment["FINAGENT_MEDIA_REQUEST"] = str(request_path)
            try:
                result = subprocess.run(
                    [executable, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                    capture_output=True,
                    timeout=90,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    env=environment,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise ProcessingError("WINDOWS_MEDIA_UNAVAILABLE_OR_TIMEOUT") from exc
            if result.returncode:
                raise ProcessingError("WINDOWS_MEDIA_FAILED")
            return parse_media_result(result.stdout)

    def inspect_pdf(self, content: bytes) -> PdfInspection:
        with tempfile.TemporaryDirectory(dir=self.workdir) as directory:
            source = Path(directory) / "source.pdf"
            source.write_bytes(content)
            result = self.inspect_path(source)
            if result.page_count is None:
                raise ProcessingError("PDF_INSPECTION_INCOMPLETE")
            return PdfInspection(
                page_count=result.page_count, password_protected=result.password_protected
            )

    def inspect_path(self, source: Path) -> MediaResult:
        return self.call({"action": "inspect_pdf", "input_path": str(source.resolve())})

    def render(
        self, source: Path, page_index: int, destination: Path, *, dpi: int = 300
    ) -> MediaResult:
        if page_index < 0 or dpi not in {300, 400} or destination.exists():
            raise ProcessingError("INVALID_RENDER_REQUEST")
        destination.parent.mkdir(parents=True, exist_ok=True)
        result = self.call(
            {
                "action": "render_pdf",
                "input_path": str(source.resolve()),
                "output_path": str(destination.resolve()),
                "page_index": page_index,
                "dpi": dpi,
            }
        )
        width, height = png_dimensions(destination)
        return bind_raster_dimensions(result, width, height)

    def transform(
        self, source: Path, destination: Path, *, rotation: int = 0, deskew_degrees: float = 0
    ) -> tuple[MediaResult, Affine]:
        if (
            rotation not in {0, 90, 180, 270}
            or not -5 <= deskew_degrees <= 5
            or destination.exists()
        ):
            raise ProcessingError("INVALID_IMAGE_TRANSFORM")
        source_width, source_height = png_dimensions(source)
        matrix, width, height = expanded_rotation(
            source_width, source_height, rotation + deskew_degrees
        )
        if width * height > MAX_RASTER_PIXELS:
            raise ProcessingError("RASTER_PIXEL_LIMIT")
        destination.parent.mkdir(parents=True, exist_ok=True)
        result = self.call(
            {
                "action": "transform",
                "input_path": str(source.resolve()),
                "output_path": str(destination.resolve()),
                "matrix": asdict(matrix),
                "width": width,
                "height": height,
            }
        )
        if png_dimensions(destination) != (width, height):
            raise ProcessingError("RASTER_DIMENSION_MISMATCH")
        actual = Affine(*result.actual_matrix)
        return result, actual

    def crop(self, source: Path, bbox: BoundingBox, destination: Path) -> MediaResult:
        if destination.exists():
            raise ProcessingError("OUTPUT_ALREADY_EXISTS")
        width, height = png_dimensions(source)
        x1, y1, x2, y2 = crop_bounds(bbox, width, height)
        destination.parent.mkdir(parents=True, exist_ok=True)
        return self.call(
            {
                "action": "crop",
                "input_path": str(source.resolve()),
                "output_path": str(destination.resolve()),
                "x": x1,
                "y": y1,
                "width": x2 - x1,
                "height": y2 - y1,
            }
        )

    def crop_bytes(self, content: bytes, bbox: BoundingBox) -> bytes:
        with tempfile.TemporaryDirectory(dir=self.workdir) as directory:
            source = Path(directory) / "source.png"
            destination = Path(directory) / "crop.png"
            source.write_bytes(content)
            self.crop(source, bbox, destination)
            return destination.read_bytes()

    def estimate_skew(self, source: Path) -> MediaResult:
        png_dimensions(source)
        return self.call({"action": "estimate_skew", "input_path": str(source.resolve())})
