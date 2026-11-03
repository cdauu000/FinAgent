"""Inventory only local supplied reports. No fetch, copying or synthetic expansion."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from finagent.corpus.contracts import CorpusManifest, DatasetEntry, GoldDocument, SplitManifest


def source_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def annotation_path(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to((root / "eval/datasets").resolve()):
        raise ValueError("GOLD_PATH_OUTSIDE_ANNOTATIONS")
    if not path.is_file():
        raise ValueError("GOLD_ANNOTATION_MISSING")
    return path


def cohort_hash(root: Path, manifest: CorpusManifest) -> str:
    document = manifest.model_dump(mode="json")
    annotations = {
        entry.id: source_hash(annotation_path(root, entry.gold_path))
        for entry in manifest.entries
        if entry.gold_path is not None
    }
    split_hash = (
        source_hash(annotation_path(root, manifest.split_path)) if manifest.split_path else None
    )
    content = json.dumps(
        {"manifest": document, "annotations": annotations, "split": split_hash}, sort_keys=True
    ).encode()
    return hashlib.sha256(content).hexdigest()


def validate_manifest(manifest: CorpusManifest, root: Path) -> None:
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    splits: dict[str, str] = {}
    allowed = (root / "data/public_reports").resolve()
    for entry in manifest.entries:
        path = (root / entry.local_path).resolve()
        if not path.is_relative_to(allowed) or not path.is_file():
            raise ValueError("CORPUS_PATH_OUTSIDE_SUPPLIED_REPORTS")
        if entry.id in seen_ids or entry.sha256 in seen_hashes:
            raise ValueError("DUPLICATE_CORPUS_REPORT")
        if source_hash(path) != entry.sha256:
            raise ValueError("CORPUS_HASH_MISMATCH")
        seen_ids.add(entry.id)
        seen_hashes.add(entry.sha256)
        if entry.gold_path is not None:
            annotation_path(root, entry.gold_path)
        if entry.split in {"train", "dev", "test"}:
            if entry.group_id is None:
                raise ValueError("ENTITY_GROUP_REQUIRED_FOR_SPLIT")
            previous = splits.setdefault(entry.group_id, entry.split)
            if previous != entry.split:
                raise ValueError("ENTITY_SPLIT_LEAKAGE")
        if entry.gold_approval_ref is not None:
            if entry.gold_path is None:
                raise ValueError("GOLD_ANNOTATION_REQUIRED")
            gold_path = annotation_path(root, entry.gold_path)
            gold = GoldDocument.model_validate_json(gold_path.read_text(encoding="utf-8"))
            validate_gold(gold, entry)
    if manifest.split_path is not None:
        split = SplitManifest.model_validate_json(
            annotation_path(root, manifest.split_path).read_text(encoding="utf-8")
        )
        validate_split(split, manifest)


def validate_split(split: SplitManifest, manifest: CorpusManifest) -> None:
    groups = {item.group_id: item.split for item in split.groups}
    if len(groups) != len(split.groups):
        raise ValueError("DUPLICATE_SPLIT_GROUP")
    for entry in manifest.entries:
        if entry.group_id is not None and groups.get(entry.group_id) != entry.split:
            raise ValueError("SPLIT_MANIFEST_MISMATCH")
    actual_holdout = {entry.entity_id for entry in manifest.entries if entry.split == "test"}
    if set(split.holdout_entities) != actual_holdout:
        raise ValueError("SPLIT_HOLDOUT_MISMATCH")


def validate_gold(gold: GoldDocument, entry: DatasetEntry) -> None:
    if gold.status != "approved" or gold.approver_ref != entry.gold_approval_ref:
        raise ValueError("GOLD_APPROVAL_MISMATCH")
    if gold.document_sha256 != entry.sha256 or not gold.cells:
        raise ValueError("GOLD_SOURCE_MISMATCH")
    for cell in gold.cells:
        if cell.bbox is None:
            raise ValueError("GOLD_CELL_GEOMETRY_REQUIRED")
        if cell.bbox.x2 <= cell.bbox.x1 or cell.bbox.y2 <= cell.bbox.y1:
            raise ValueError("GOLD_CELL_GEOMETRY_INVALID")


def inventory(root: Path, previous: CorpusManifest | None = None) -> CorpusManifest:
    supplied = root / "data/public_reports"
    known = {entry.local_path: entry for entry in previous.entries} if previous else {}
    entries: list[DatasetEntry] = []
    for path in sorted(supplied.iterdir()):
        # Reject links escaping the corpus before hashing or opening source bytes.
        if not path.resolve().is_relative_to(supplied.resolve()):
            raise ValueError("CORPUS_PATH_OUTSIDE_SUPPLIED_REPORTS")
        if not path.is_file() or path.suffix.lower() not in {".pdf", ".docx", ".xlsx", ".txt"}:
            continue
        relative = path.relative_to(root).as_posix()
        if relative in known:
            entries.append(known[relative])
        else:
            digest = source_hash(path)
            entries.append(
                DatasetEntry(
                    id="doc-" + digest[:16],
                    local_path=relative,
                    sha256=digest,
                    missing=("source_url", "source_date", "terms_review", "gold_approval"),
                )
            )
    manifest = CorpusManifest(
        entries=tuple(entries), split_path=previous.split_path if previous else None
    )
    validate_manifest(manifest, root)
    return manifest


def corpus_counts(manifest: CorpusManifest) -> dict[str, object]:
    complete = [
        entry
        for entry in manifest.entries
        if entry.source_url
        and entry.source_date
        and entry.source_evidence_ref
        and entry.terms_status == "permitted_verified"
        and entry.terms_evidence_ref
    ]
    gold = [entry for entry in complete if entry.gold_approval_ref and entry.gold_path]
    return {
        "unique_real_reports": len(manifest.entries),
        "complete_manifests": len(complete),
        "gold_approved": len(gold),
        "required_manifests": 30,
        "required_gold": 10,
        "status": "PASS" if len(complete) >= 30 and len(gold) >= 10 else "INSUFFICIENT_DATA",
        "scope_counts": dict(Counter(entry.scope or "unknown" for entry in manifest.entries)),
        "industry_counts": dict(Counter(entry.industry or "unknown" for entry in manifest.entries)),
    }
