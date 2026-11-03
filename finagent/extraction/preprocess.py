import hashlib
from pathlib import Path
from typing import Literal
from uuid import uuid4

from finagent.contracts.base import Contract, ExecutionContext, Identifier, SafeInt, Sha256, Tier
from finagent.contracts.geometry import Affine
from finagent.extraction.media import MediaResult, WindowsMedia
from finagent.ingestion.errors import ProcessingError
from finagent.security.permissions import authorize


class PreparedPage(Contract):
    page_ref: Identifier
    source_sha256: Sha256
    physical_index: SafeInt
    source_tier: Tier
    source_coordinate_space: Literal["upright_pdf_dip"] = "upright_pdf_dip"
    original_image: str
    processed_image: str
    width: SafeInt
    height: SafeInt
    original_width: SafeInt
    original_height: SafeInt
    source_width_dip: float
    source_height_dip: float
    source_intrinsic_rotation: SafeInt
    additional_rotation: SafeInt
    deskew_degrees: float
    source_to_processed: tuple[float, ...]
    processed_to_source: tuple[float, ...]
    requested_dpi: SafeInt
    orientation_status: str
    peak_child_working_set_bytes: SafeInt


class ImagePreprocessor:
    def __init__(self, media: WindowsMedia, output: Path) -> None:
        self.media, self.output = media, output.resolve()
        self.output.mkdir(parents=True, exist_ok=True)

    def prepare(
        self,
        source: Path,
        page_index: int,
        ctx: ExecutionContext,
        *,
        dpi: int = 300,
        rotation: int | None = None,
        deskew_degrees: float = 0,
    ) -> PreparedPage:
        authorize(ctx, "document:read")
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        page_ref = "page-" + uuid4().hex
        original = self.output / (page_ref + "-original.png")
        processed = self.output / (page_ref + "-processed.png")
        rendered = self.media.render(source, page_index, original, dpi=dpi)
        if (
            rendered.width is None
            or rendered.height is None
            or not rendered.width_dip
            or not rendered.height_dip
        ):
            raise ProcessingError("RASTER_DIMENSIONS_REQUIRED")
        changed, affine = self.media.transform(
            original, processed, rotation=rotation or 0, deskew_degrees=deskew_degrees
        )
        if changed.width is None or changed.height is None:
            raise ProcessingError("RASTER_DIMENSIONS_REQUIRED")
        if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
            raise ProcessingError("SOURCE_CHANGED_DURING_PROCESSING")
        scaling = Affine(
            a=rendered.width / rendered.width_dip, d=rendered.height / rendered.height_dip
        )
        forward = scaling.then(affine)
        from dataclasses import astuple

        return PreparedPage(
            page_ref=page_ref,
            source_sha256=source_hash,
            physical_index=page_index,
            source_tier=ctx.source_tier,
            original_image=original.name,
            processed_image=processed.name,
            width=changed.width,
            height=changed.height,
            original_width=rendered.width,
            original_height=rendered.height,
            source_width_dip=rendered.width_dip,
            source_height_dip=rendered.height_dip,
            source_intrinsic_rotation=rendered.intrinsic_rotation or 0,
            additional_rotation=rotation or 0,
            deskew_degrees=deskew_degrees,
            source_to_processed=astuple(forward),
            processed_to_source=astuple(forward.inverse()),
            requested_dpi=dpi,
            orientation_status="USER_SELECTED"
            if rotation is not None
            else "INTRINSIC_ONLY_UNVERIFIED",
            peak_child_working_set_bytes=max(
                rendered.peak_working_set_bytes, changed.peak_working_set_bytes
            ),
        )

    def estimate_skew(self, page: PreparedPage, ctx: ExecutionContext) -> MediaResult:
        authorize(ctx, "document:read")
        return self.media.estimate_skew(self.output / page.original_image)
