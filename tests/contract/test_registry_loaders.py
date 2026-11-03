import ast
import json
from pathlib import Path

import pytest

from finagent.policy import registry

ROOT = Path(__file__).resolve().parents[2]


class Rows:
    def __init__(self, content: str) -> None:
        self.content = content

    def read_registry_json(self, registry_id: str) -> str:
        assert registry_id == "registry-a"
        return self.content


def test_every_disk_and_database_business_load_calls_bundle_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "bundle.json"
    path.write_text("{}")
    calls = []

    def blocked(*args: object, **kwargs: object) -> None:
        calls.append(args)
        raise ValueError("GATE_SENTINEL")

    monkeypatch.setattr(registry, "validate_bundle", blocked)
    for load in (
        lambda: registry.load_bundle(path),
        lambda: registry.load_bundle_from_database(Rows("{}"), "registry-a"),
    ):
        with pytest.raises(ValueError, match="GATE_SENTINEL"):
            load()
    assert len(calls) == 2


@pytest.mark.parametrize("kind", ["prompt", "model"])
def test_gateway_disk_and_database_loads_cannot_skip_registry_bundle(
    kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "registry.json"
    path.write_text("{}")
    calls = []

    def blocked(*args: object, **kwargs: object) -> None:
        calls.append(args)
        raise ValueError("GATE_SENTINEL")

    monkeypatch.setattr(registry, "registry_bundle", blocked)
    for load in (
        lambda: registry.load_gateway_registry(path, kind),
        lambda: registry.load_gateway_registry_from_database(Rows("{}"), "registry-a", kind),
    ):
        with pytest.raises(ValueError, match="GATE_SENTINEL"):
            load()
    assert len(calls) == 2


def test_invalid_payload_is_rejected_on_both_business_sources(tmp_path: Path) -> None:
    invalid = json.dumps({"ratios": [{"id": "bad"}]})
    path = tmp_path / "registry.json"
    path.write_text(invalid)
    for load in (
        lambda: registry.load_bundle(path),
        lambda: registry.load_bundle_from_database(Rows(invalid), "registry-a"),
    ):
        with pytest.raises(ValueError):
            load()


def test_production_code_has_no_registry_deserialization_outside_bundle_gate() -> None:
    names = {
        "RegistryBundle",
        "ModelRegistry",
        "PromptRegistry",
        "RatioDefinition",
        "RuleDefinition",
        "TemplateDefinition",
        "SectorPack",
        "RoleDefinition",
        "ToolDefinition",
        "ApplicabilityDefinition",
    }
    for path in (ROOT / "finagent").rglob("*.py"):
        if path == ROOT / "finagent/policy/registry.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                target = node.func.value
                if isinstance(target, ast.Name) and target.id in names:
                    assert not node.func.attr.startswith(("model_validate", "model_construct")), (
                        path
                    )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in names, path


def test_pinned_core_bundle_has_fifteen_core_definitions_and_unapproved_assessment() -> None:
    bundle = registry.load_bundle(ROOT / "config/registries/core.json")
    assert len([ratio for ratio in bundle.ratios if ratio.definition_role == "core"]) == 15
    assert len({(ratio.id, ratio.version) for ratio in bundle.ratios}) == len(bundle.ratios)
    profile = bundle.packs[0].assessment_policy
    assert profile is not None and profile.validation_status == "POLICY_UNAPPROVED"
    assert bundle.packs[0].ratio_memberships[0].ratio_ref.id == "current_ratio"
    catalog = json.loads((ROOT / "config/registries/source-catalog.json").read_text())
    sources = {item["id"] for item in catalog["source_records"]}
    tests = {item["id"] for item in catalog["test_records"]}
    for entries in (
        bundle.ratios,
        bundle.templates,
        bundle.rules,
        bundle.packs,
        bundle.applicability,
    ):
        for entry in entries:
            assert set(entry.source_refs) <= sources
            assert set(entry.mandatory_test_refs) <= tests
    assert all((ROOT / item["path"]).is_file() for item in catalog["source_records"])
    assert all((ROOT / item["path"]).is_file() for item in catalog["test_records"])
