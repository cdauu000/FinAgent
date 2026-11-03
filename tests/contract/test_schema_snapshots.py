import json
from pathlib import Path

import pytest

from finagent.schema_catalog import SCHEMAS, check_frozen, write_drafts

ROOT = Path(__file__).resolve().parents[2]


def test_all_declared_contracts_match_owner_approved_frozen_snapshots() -> None:
    check_frozen(ROOT)
    manifest = json.loads((ROOT / "schemas/frozen/manifest.json").read_text(encoding="utf-8"))
    assert manifest["frozen"] is True
    assert manifest["owner_review_required"] is False
    assert {item["version"] for item in manifest["schemas"]} == set(SCHEMAS)
    assert {item["mode"] for item in manifest["schemas"]} == {"validation", "serialization"}


def test_draft_writer_cannot_mark_or_overwrite_frozen_contracts(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="ONLY_DRAFT_DIRECTORY_ALLOWED"):
        write_drafts(tmp_path / "frozen")
    directory = tmp_path / "draft"
    directory.mkdir()
    (directory / "manifest.json").write_text('{"status":"frozen","frozen":true}', encoding="utf-8")
    with pytest.raises(ValueError, match="CANNOT_OVERWRITE_FROZEN_SCHEMAS"):
        write_drafts(directory)
