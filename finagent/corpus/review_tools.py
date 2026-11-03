"""Read-only supplied-report tooling. Creates candidates/crops, never gold approval."""

import json
from pathlib import Path

from pydantic import Field

from finagent.contracts.base import Contract, ExecutionContext, SafeInt, Sha256
from finagent.corpus.contracts import CorpusManifest, GoldDocument, PageAnnotation
from finagent.corpus.inventory import inventory, source_hash
from finagent.extraction.media import WindowsMedia
from finagent.extraction.numbers import RawNumericCell, normalize
from finagent.extraction.preprocess import ImagePreprocessor, PreparedPage
from finagent.ingestion.errors import ProcessingError
from finagent.observability.profiling import OperationProfiler
from finagent.security.permissions import authorize


class ReferenceRaster(Contract):
    path: str
    sha256: Sha256
    width: SafeInt = Field(gt=0)
    height: SafeInt = Field(gt=0)


class ReferenceFrames(Contract):
    source_sha256: Sha256
    rasters: tuple[ReferenceRaster, ...]


def supplied_report(root: Path, relative_path: str) -> Path:
    allowed = (root / "data/public_reports").resolve()
    path = (root / relative_path).resolve()
    if not path.is_relative_to(allowed) or not path.is_file() or path.suffix.lower() != ".pdf":
        raise ProcessingError("SOURCE_OUTSIDE_SUPPLIED_REPORTS")
    return path


def runtime_output(root: Path, output: Path) -> Path:
    resolved = output.resolve()
    if not resolved.is_relative_to((root / "data/runtime").resolve()):
        raise ProcessingError("REVIEW_OUTPUT_OUTSIDE_RUNTIME")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def write_new(path: Path, content: str) -> None:
    with path.open("x", encoding="utf-8") as output:
        output.write(content + "\n")


def require_page_annotations(indices: tuple[int, ...], page_count: int) -> None:
    if len(set(indices)) != len(indices) or any(i < 0 or i >= page_count for i in indices):
        raise ProcessingError("PAGE_ANNOTATIONS_CONFLICT")


def build_manifest(
    root: Path, output: Path, media: WindowsMedia, previous: CorpusManifest | None = None
) -> CorpusManifest:
    destination = runtime_output(root, output)
    profiler = OperationProfiler(destination / "trace.jsonl")
    with profiler.measure("inventory"):
        manifest = inventory(root, previous)
    entries = []
    inspections: list[dict[str, object]] = []
    for entry in manifest.entries:
        if Path(entry.local_path).suffix.lower() != ".pdf":
            entries.append(entry)
            inspections.append(
                {"document_ref": entry.id, "status": "NOT_RUN", "reason": "PDF_TOOLING_ONLY"}
            )
            continue
        try:
            source = supplied_report(root, entry.local_path)
            with profiler.measure("pdf_inspect") as sample:
                details = media.inspect_path(source)
                sample.child_peak_working_set_bytes = details.peak_working_set_bytes
            if source_hash(source) != entry.sha256:
                raise ProcessingError("SOURCE_CHANGED_DURING_PROCESSING")
            require_page_annotations(
                tuple(p.physical_index for p in entry.pages), len(details.pages)
            )
            existing = {page.physical_index: page for page in entry.pages}
            pages = tuple(
                existing.get(page.physical_index)
                or PageAnnotation(physical_index=page.physical_index, content_label="unknown")
                for page in details.pages
            )
            entries.append(entry.model_copy(update={"pages": pages}))
            inspections.append(
                {
                    "document_ref": entry.id,
                    "status": "INSPECTED",
                    "native_reader_status": "NOT_RUN_NO_NATIVE_PDF_LIBRARY",
                    "pdf": details.model_dump(mode="json"),
                }
            )
        except ProcessingError as exc:
            entries.append(entry)
            inspections.append(
                {"document_ref": entry.id, "status": "NOT_RUN_OR_REJECTED", "reason": exc.code}
            )
    result = manifest.model_copy(update={"entries": tuple(entries)})
    write_new(destination / "manifest.json", result.model_dump_json(indent=2))
    write_new(destination / "inspection.json", json.dumps(inspections, indent=2))
    return result


def export_review_bundle(
    root: Path,
    relative_pdf: str,
    gold: GoldDocument,
    frames: ReferenceFrames,
    output: Path,
    ctx: ExecutionContext,
    media: WindowsMedia,
    *,
    dpi: int = 300,
) -> dict[str, object]:
    authorize(ctx, "review:read")
    source = supplied_report(root, relative_pdf)
    digest = source_hash(source)
    if digest != gold.document_sha256 or digest != frames.source_sha256:
        raise ProcessingError("CANDIDATE_SOURCE_MISMATCH")
    destination = runtime_output(root, output)
    processor = ImagePreprocessor(media, destination)
    profiler = OperationProfiler(destination / "trace.jsonl")
    raster_lookup = {Path(frame.path).name: frame for frame in frames.rasters}
    cached: dict[int, PreparedPage] = {}
    candidates: list[dict[str, object]] = []
    from finagent.store.models import BoundingBox

    for cell in gold.cells:
        row: dict[str, object] = {
            "candidate_id": cell.id,
            "code": cell.code,
            "physical_index": cell.physical_index,
            "raw_text": cell.raw_text,
            "supplied_value": str(cell.value),
            "status": "NEEDS_BBOX",
            "producer": "EXISTING_DRAFT_NOT_OCR",
            "gold_approved": False,
        }
        candidates.append(row)
        if cell.bbox is None:
            continue
        frame = raster_lookup.get(Path(cell.bbox.raster_ref).name)
        if frame is None:
            row["status"] = "NEEDS_REFERENCE_RASTER_DIMENSIONS"
            continue
        if cell.bbox.x2 > frame.width or cell.bbox.y2 > frame.height:
            row["status"] = "INVALID_REFERENCE_BBOX"
            continue
        if cell.physical_index not in cached:
            with profiler.measure("render_prepare") as sample:
                prepared = processor.prepare(source, cell.physical_index, ctx, dpi=dpi)
                sample.child_peak_working_set_bytes = prepared.peak_child_working_set_bytes
            cached[cell.physical_index] = prepared
        prepared = cached[cell.physical_index]
        box = BoundingBox(
            x1=cell.bbox.x1 * prepared.original_width / frame.width,
            y1=cell.bbox.y1 * prepared.original_height / frame.height,
            x2=cell.bbox.x2 * prepared.original_width / frame.width,
            y2=cell.bbox.y2 * prepared.original_height / frame.height,
        )
        crop_name = cell.id + "-candidate.png"
        with profiler.measure("crop_export") as sample:
            crop = media.crop(destination / prepared.original_image, box, destination / crop_name)
            sample.child_peak_working_set_bytes = crop.peak_working_set_bytes
        row.update(
            {
                "status": "CANDIDATE_UNVERIFIED",
                "crop": crop_name,
                "crop_sha256": source_hash(destination / crop_name),
                "reference_raster_sha256": frame.sha256,
                "reference_bbox": cell.bbox.model_dump(mode="json"),
                "rendered_bbox": box.model_dump(mode="json"),
                "requested_dpi": dpi,
            }
        )
        try:
            normalized = normalize(
                RawNumericCell(
                    cell_id=cell.id,
                    raw_text=cell.raw_text,
                    role="value",
                    currency="VND" if cell.unit == "VND" else None,
                    unit_scale=1,
                    measure="money" if cell.unit == "VND" else "count",
                )
            )
            row["normalized_candidate"] = normalized.model_dump(mode="json")
            if normalized.value is not None and normalized.value != cell.value:
                row["warning"] = "CANDIDATE_DIFFERS_FROM_EXISTING_DRAFT"
        except ProcessingError as exc:
            row["normalization_issue"] = exc.code
    if source_hash(source) != digest:
        raise ProcessingError("SOURCE_CHANGED_DURING_PROCESSING")
    bundle: dict[str, object] = {
        "schema_version": "review-export/1",
        "source_sha256": digest,
        "source_tier": ctx.source_tier,
        "status": "CANDIDATES_ONLY_NOT_GOLD",
        "source_conflicts": gold.source_conflicts,
        "candidates": candidates,
        "pages": [page.model_dump(mode="json") for page in cached.values()],
        "scope": "Crop export and local operation trace; no OCR, training, KPI or gold approval",
    }
    write_new(destination / "review.json", json.dumps(bundle, ensure_ascii=False, indent=2))
    return bundle
