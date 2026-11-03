import json
import shutil
from pathlib import Path

import pytest

from finagent.contracts.compatibility import COMPAT_POLICY
from finagent.schema_catalog import check_frozen, freeze_schemas, write_drafts

ROOT = Path(__file__).resolve().parents[2]


def test_freeze_is_explicit_and_immutable_with_hash_and_approval(tmp_path: Path) -> None:
    draft = tmp_path / "schemas/draft"
    draft.mkdir(parents=True)
    write_drafts(draft)
    with pytest.raises(ValueError, match="EXPLICIT_FREEZE_REQUIRED"):
        freeze_schemas(tmp_path, approval="yes")
    freeze_schemas(tmp_path, approval="freeze")
    manifest = json.loads((tmp_path / "schemas/frozen/manifest.json").read_text())
    assert manifest["frozen"] and manifest["frozen_at"]
    assert manifest["git_commit"] is None  # isolated directory is not a Git checkout
    assert manifest["compat_policy"] == COMPAT_POLICY
    check_frozen(tmp_path)
    with pytest.raises(ValueError, match="FROZEN_BASELINE_ALREADY_EXISTS"):
        freeze_schemas(tmp_path, approval="freeze")
    with pytest.raises(ValueError, match="CANNOT_OVERWRITE_FROZEN"):
        write_drafts(draft)


def test_frozen_hash_tampering_and_closed_enum_change_are_detected(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "schemas", tmp_path / "schemas")
    target = tmp_path / "schemas/frozen/gateway-1.validation.json"
    schema = json.loads(target.read_text())
    schema["$defs"]["GatewayTask"]["enum"].append("embedding")
    target.write_text(json.dumps(schema), encoding="utf-8")
    with pytest.raises(ValueError, match="FROZEN_HASH_MISMATCH"):
        check_frozen(tmp_path)
    assert COMPAT_POLICY["enum_policy"]["extensible"] == []
