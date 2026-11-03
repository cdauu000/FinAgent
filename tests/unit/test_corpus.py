from pathlib import Path

import pytest

from finagent.corpus.contracts import CorpusManifest, DatasetEntry, GoldDocument
from finagent.corpus.inventory import (
    cohort_hash,
    corpus_counts,
    inventory,
    source_hash,
    validate_gold,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[2]


def report(root: Path, name: str, content: bytes) -> DatasetEntry:
    path = root / "data/public_reports" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)  # isolated unit data, never counted in the actual corpus
    return DatasetEntry(
        id=name, local_path=path.relative_to(root).as_posix(), sha256=source_hash(path)
    )


def test_inventory_uses_only_supplied_files_and_never_promotes_missing_metadata() -> None:
    previous = CorpusManifest.model_validate_json(
        (ROOT / "eval/datasets/manifest.json").read_text()
    )
    manifest = inventory(ROOT, previous)
    counts = corpus_counts(manifest)
    assert counts["unique_real_reports"] == 1
    assert counts["complete_manifests"] == counts["gold_approved"] == 0
    assert counts["status"] == "INSUFFICIENT_DATA"
    gold = GoldDocument.model_validate_json((ROOT / manifest.entries[0].gold_path).read_text())
    assert gold.status == "draft" and gold.approver_ref is None
    assert len(gold.cells) == 80
    assert sum(cell.bbox is not None for cell in gold.cells) == 2
    assert next(c for c in gold.cells if c.id == "B02-23-current").value == 97623991644
    with pytest.raises(ValueError, match="GOLD_APPROVAL_MISMATCH"):
        validate_gold(gold, manifest.entries[0])


def test_duplicate_hashes_tampering_paths_and_group_leakage_fail(tmp_path: Path) -> None:
    first = report(tmp_path, "a.txt", b"unit-a")
    duplicate = report(tmp_path, "b.txt", b"unit-a")
    with pytest.raises(ValueError, match="DUPLICATE_CORPUS_REPORT"):
        validate_manifest(CorpusManifest(entries=(first, duplicate)), tmp_path)
    (tmp_path / first.local_path).write_bytes(b"changed")
    with pytest.raises(ValueError, match="CORPUS_HASH_MISMATCH"):
        validate_manifest(CorpusManifest(entries=(first,)), tmp_path)
    outside = first.model_copy(update={"local_path": "../outside.pdf"})
    with pytest.raises(ValueError, match="CORPUS_PATH_OUTSIDE"):
        validate_manifest(CorpusManifest(entries=(outside,)), tmp_path)
    first = report(tmp_path, "a.txt", b"unit-a").model_copy(
        update={"group_id": "same", "split": "train"}
    )
    second = report(tmp_path, "b.txt", b"unit-b").model_copy(
        update={"group_id": "same", "split": "test"}
    )
    with pytest.raises(ValueError, match="ENTITY_SPLIT_LEAKAGE"):
        validate_manifest(CorpusManifest(entries=(first, second)), tmp_path)


def test_cohort_binds_annotation_bytes_and_rejects_arbitrary_file_references(
    tmp_path: Path,
) -> None:
    entry = report(tmp_path, "unit.txt", b"unit-report")
    annotation = tmp_path / "eval/datasets/unit.json"
    annotation.parent.mkdir(parents=True)
    annotation.write_text('{"status":"draft"}')
    entry = entry.model_copy(update={"gold_path": "eval/datasets/unit.json"})
    manifest = CorpusManifest(entries=(entry,))
    before = cohort_hash(tmp_path, manifest)
    annotation.write_text('{"status":"draft","changed":true}')
    assert cohort_hash(tmp_path, manifest) != before
    escaped = entry.model_copy(update={"gold_path": ".env"})
    with pytest.raises(ValueError, match="GOLD_PATH_OUTSIDE_ANNOTATIONS"):
        validate_manifest(CorpusManifest(entries=(escaped,)), tmp_path)
