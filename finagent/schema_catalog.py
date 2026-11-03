"""Manual draft-schema exporter/checker. It cannot freeze or approve a contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from finagent.api.contracts import ApiCatalog
from finagent.contracts.compatibility import COMPAT_POLICY, validate_frozen_index
from finagent.contracts.validator_catalog import validators_for_schema
from finagent.llm_gateway.contracts import GatewayCatalog
from finagent.llm_gateway.model_registry import (
    ModelRegistry,
    ProbeResult,
    QuotaDenied,
    QuotaReservation,
    SyntheticProbeRequest,
)
from finagent.llm_gateway.prompts import PromptRegistry
from finagent.observability.contracts import EventEnvelope
from finagent.policy.contracts import (
    ApplicabilityDefinition,
    PolicySnapshot,
    RatioDefinition,
    RoleCatalog,
    RuleDefinition,
    SectorPack,
    TemplateDefinition,
    ToolDefinition,
)
from finagent.schema_review import CASE_PATH, review_case_counts, validate_review_counts
from finagent.store.models import CanonicalCatalog


class GatewayReviewCatalog(GatewayCatalog):
    """Schema-only composition; Gateway runtime imports no business modules."""

    quota_reservation: QuotaReservation | None = None
    quota_denied: QuotaDenied | None = None
    synthetic_probe: SyntheticProbeRequest | None = None
    probe_result: ProbeResult | None = None


SCHEMAS: dict[str, type[BaseModel]] = {
    "canonical/1": CanonicalCatalog,
    "api/1": ApiCatalog,
    "event/1": EventEnvelope,
    "spack/1": SectorPack,
    "role/1": RoleCatalog,
    "tool/1": ToolDefinition,
    "template/1": TemplateDefinition,
    "ratio-def/1": RatioDefinition,
    "rule/1": RuleDefinition,
    "policy/1": PolicySnapshot,
    "applicability/1": ApplicabilityDefinition,
    "gateway/1": GatewayReviewCatalog,
    "prompt/1": PromptRegistry,
    "model-registry/1": ModelRegistry,
}


def draft_artifacts() -> dict[str, str]:
    artifacts: dict[str, str] = {}
    entries: list[dict[str, str]] = []
    counts = review_case_counts(SCHEMAS)
    for version, model in sorted(SCHEMAS.items()):
        for mode in ("validation", "serialization"):
            schema = model.model_json_schema(mode=mode)
            schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
            schema["x-finagent-version"] = version
            schema["x-finagent-status"] = "draft"
            schema["x-finagent-custom-validators"] = validators_for_schema(schema)
            content = json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            filename = version.replace("/", "-") + "." + mode + ".json"
            artifacts[filename] = content
            entries.append(
                {
                    "version": version,
                    "mode": mode,
                    "file": filename,
                    "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "status": "draft",
                }
            )
    artifacts["manifest.json"] = (
        json.dumps(
            {
                "status": "draft",
                "frozen": False,
                "owner_review_required": True,
                "schemas": entries,
                "compat_policy": {
                    "same_major": "optional_fields_only",
                    "breaking": "major_bump_with_ADR_migration_full_snapshot_suite",
                    "freeze_requires": "explicit user confirmation: freeze",
                },
                "case_catalog": {
                    "path": "tests/fixtures/schema_review_cases.json",
                    "sha256": hashlib.sha256(CASE_PATH.read_bytes()).hexdigest(),
                    "counting_unit": "one dedicated review-case row, validated once in JSON mode",
                    "groups": counts,
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return artifacts


def check_drafts(directory: Path) -> None:
    expected = draft_artifacts()
    actual_files = {path.name for path in directory.glob("*.json")}
    if actual_files != set(expected):
        raise ValueError("DRAFT_SCHEMA_FILE_SET_MISMATCH")
    for name, content in expected.items():
        if (directory / name).read_text(encoding="utf-8") != content:
            raise ValueError(f"DRAFT_SCHEMA_SNAPSHOT_MISMATCH: {name}")


def write_drafts(directory: Path) -> None:
    if directory.name != "draft":
        raise ValueError("ONLY_DRAFT_DIRECTORY_ALLOWED")
    if (directory.parent / "frozen/manifest.json").exists():
        raise ValueError("CANNOT_OVERWRITE_FROZEN_SCHEMAS")
    artifacts = draft_artifacts()
    if (directory / "manifest.json").exists():
        state = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if state.get("status") != "draft" or state.get("frozen") is not False:
            raise ValueError("CANNOT_OVERWRITE_FROZEN_SCHEMAS")
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in artifacts.items():
        (directory / name).write_text(content, encoding="utf-8", newline="\n")


def freeze_schemas(root: Path, *, approval: str) -> None:
    if approval != "freeze":
        raise ValueError("EXPLICIT_FREEZE_REQUIRED")
    directory = root / "schemas/frozen"
    if directory.exists():
        raise ValueError("FROZEN_BASELINE_ALREADY_EXISTS")
    check_drafts(root / "schemas/draft")
    manifest = json.loads((root / "schemas/draft/manifest.json").read_text(encoding="utf-8"))
    commit = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "rev-parse", "--verify", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    frozen_at = datetime.now(UTC).isoformat()
    archive = root / "schemas/reviews/at-freeze"
    archive.mkdir(parents=True)
    (archive / "schema_review_cases.json").write_bytes(CASE_PATH.read_bytes())
    directory.mkdir()
    for entry in manifest["schemas"]:
        source = root / "schemas/draft" / entry["file"]
        schema = json.loads(source.read_text(encoding="utf-8"))
        schema["x-finagent-status"] = "frozen"
        content = json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        entry["approved_draft_sha256"] = entry["sha256"]
        entry["sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
        entry["status"] = "frozen"
        (directory / entry["file"]).write_text(content, encoding="utf-8", newline="\n")
    manifest.update(
        {
            "status": "frozen",
            "frozen": True,
            "owner_review_required": False,
            "approved_by": "project_owner_explicit_freeze",
            "frozen_at": frozen_at,
            "git_commit": commit.stdout.strip() if commit.returncode == 0 else None,
            "git_commit_reason": None if commit.returncode == 0 else "NO_HEAD_COMMIT",
            "working_tree_committed": False,
            "compat_policy": COMPAT_POLICY,
        }
    )
    manifest["case_catalog"]["path"] = "schemas/reviews/at-freeze/schema_review_cases.json"
    (directory / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lifecycle = root / "schemas/lifecycle"
    lifecycle.mkdir(exist_ok=True)
    (lifecycle / "canonical-1.json").write_text(
        json.dumps(
            {
                "version": "canonical/1",
                "first_real_data_persisted_at": None,
                "first_write_event_ref": None,
                "window_open": True,
                "required_integration_point": "P2.01_before_first_real_canonical_write",
                "implementation_status": "P2_PERSISTENCE_NOT_IMPLEMENTED",
                "amendments": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def check_frozen(root: Path) -> None:
    directory = root / "schemas/frozen"
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if not manifest["frozen"] or manifest["status"] != "frozen":
        raise ValueError("INVALID_FROZEN_STATE")
    if manifest["compat_policy"] != COMPAT_POLICY:
        raise ValueError("FROZEN_COMPAT_POLICY_MISMATCH")
    if not manifest.get("frozen_at") or not manifest.get("approved_by"):
        raise ValueError("FREEZE_APPROVAL_EVIDENCE_REQUIRED")
    expected = draft_artifacts()
    validate_frozen_index(manifest)
    if {p.name for p in directory.glob("*.json")} != set(expected):
        raise ValueError("FROZEN_SCHEMA_FILE_SET_MISMATCH")
    for entry in manifest["schemas"]:
        content = (directory / entry["file"]).read_bytes()
        if hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise ValueError("FROZEN_HASH_MISMATCH")
        current = json.loads(expected[entry["file"]])
        current["x-finagent-status"] = "frozen"
        if json.loads(content) != current:
            raise ValueError(f"FROZEN_SCHEMA_CHANGE_REQUIRES_COMPAT_REVIEW: {entry['file']}")
    archive = root / manifest["case_catalog"]["path"]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["case_catalog"]["sha256"]:
        raise ValueError("FROZEN_CASE_ARCHIVE_HASH_MISMATCH")
    validate_review_counts(
        review_case_counts(SCHEMAS, case_path=archive), manifest["case_catalog"]["groups"]
    )
    # Current regressions grow independently of the immutable approval-time archive.
    review_case_counts(SCHEMAS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Schema snapshots; freeze requires owner approval")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-drafts", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--freeze", action="store_true")
    parser.add_argument("--approval")
    args = parser.parse_args()
    directory = Path("schemas/draft")
    root = Path.cwd()
    if args.freeze:
        freeze_schemas(root, approval=args.approval or "")
    elif args.write_drafts:
        write_drafts(directory)
    elif (root / "schemas/frozen/manifest.json").exists():
        check_frozen(root)
    else:
        check_drafts(directory)
    frozen = (root / "schemas/frozen/manifest.json").exists()
    print(f"Schemas: {len(SCHEMAS)} versions; frozen={str(frozen).lower()}")


if __name__ == "__main__":
    main()
