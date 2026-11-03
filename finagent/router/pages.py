from typing import Literal

from pydantic import Field

from finagent.contracts.base import Contract, ExecutionContext, Identifier, PageText, SafeInt
from finagent.security.permissions import authorize


class PageFeatures(Contract):
    document_ref: Identifier
    physical_index: SafeInt = Field(ge=0)
    native_text: PageText | None = None
    native_body_aligned: bool = False
    signature_only_text: bool = False
    image_area_fraction: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    orientation_degrees: Literal[0, 90, 180, 270] | None = None


class PagePlan(Contract):
    document_ref: Identifier
    physical_index: SafeInt
    route: Literal["text", "ocr", "hybrid"]
    page_kind: Literal["native", "scan", "hybrid", "unknown"]
    reasons: tuple[Identifier, ...]
    native_characters: SafeInt | None
    orientation_degrees: Literal[0, 90, 180, 270] | None


class DocumentRouter:
    def route(self, pages: tuple[PageFeatures, ...], ctx: ExecutionContext) -> tuple[PagePlan, ...]:
        authorize(ctx, "document:read")
        plans = []
        for page in pages:
            route: Literal["text", "ocr", "hybrid"]
            kind: Literal["native", "scan", "hybrid", "unknown"]
            reasons: tuple[str, ...]
            # TODO(verify): A64 generic triage signals, not fitted on FPT or measured OCR quality.
            text = page.native_text
            valid = text is not None and len(text.strip()) >= 80 and page.native_body_aligned
            valid = valid and not page.signature_only_text and "\ufffd" not in (text or "")
            if valid and page.image_area_fraction is not None and page.image_area_fraction < 0.2:
                route, kind, reasons = "text", "native", ("NATIVE_BODY_USABLE",)
            elif valid:
                route, kind, reasons = (
                    "hybrid",
                    "hybrid",
                    ("IMAGE_OR_ALIGNMENT_REQUIRES_LOCAL_READING",),
                )
            else:
                route = "ocr"
                kind = "unknown" if text is None else "scan"
                reasons = (
                    ("NATIVE_READER_UNAVAILABLE",)
                    if text is None
                    else (
                        "SIGNATURE_NOT_BODY"
                        if page.signature_only_text
                        else "NATIVE_BODY_UNUSABLE",
                    )
                )
            if page.orientation_degrees is None:
                reasons += ("ORIENTATION_REVIEW_REQUIRED",)
            plans.append(
                PagePlan(
                    document_ref=page.document_ref,
                    physical_index=page.physical_index,
                    route=route,
                    page_kind=kind,
                    reasons=reasons,
                    native_characters=len(text) if text is not None else None,
                    orientation_degrees=page.orientation_degrees,
                )
            )
        return tuple(plans)
