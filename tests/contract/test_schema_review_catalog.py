import ast
import json
from pathlib import Path

import pytest

from finagent.api.app import create_app
from finagent.contracts.validator_catalog import SPECS
from finagent.schema_catalog import SCHEMAS
from finagent.schema_review import (
    ReviewCase,
    check_review_case,
    load_review_cases,
    review_case_counts,
)

ROOT = Path(__file__).resolve().parents[2]
CASES = load_review_cases()


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.id)
def test_review_case_acceptance_and_rejection(case: ReviewCase) -> None:
    passed, observed = check_review_case(case, SCHEMAS[case.group])
    assert passed, (case.id, case.expect, observed)


def test_manifest_counts_and_hashes_are_reproducible_measured_results() -> None:
    import hashlib

    manifest = json.loads((ROOT / "schemas/frozen/manifest.json").read_text(encoding="utf-8"))
    review_case_counts(SCHEMAS)
    assert manifest["compat_policy"]["same_major"] == "optional_fields_and_new_DTOs_only"
    assert (
        manifest["compat_policy"]["breaking"] == "major_bump_with_ADR_migration_full_snapshot_suite"
    )
    for item in manifest["schemas"]:
        assert (
            hashlib.sha256((ROOT / "schemas/frozen" / item["file"]).read_bytes()).hexdigest()
            == item["sha256"]
        )
    for count in manifest["case_catalog"]["groups"].values():
        assert count["positive_cases"] > 0 and count["negative_cases"] > 0
        assert count["failed"] == 0
    assert manifest["frozen"] is True
    archive = ROOT / manifest["case_catalog"]["path"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest["case_catalog"]["sha256"]


def test_custom_validator_inventory_covers_every_decorated_project_validator() -> None:
    expected: set[str] = set()
    for path in (ROOT / "finagent").rglob("*.py"):
        module = ".".join(path.relative_to(ROOT).with_suffix("").parts)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.ClassDef):
                continue
            for method in node.body:
                if not isinstance(method, ast.FunctionDef):
                    continue
                for decorator in method.decorator_list:
                    if (
                        isinstance(decorator, ast.Call)
                        and isinstance(decorator.func, ast.Name)
                        and decorator.func.id in {"model_validator", "field_validator"}
                    ):
                        expected.add(f"{module}.{node.name}.{method.name}")
    documented = {spec.symbol for spec in SPECS}
    assert expected <= documented, expected - documented


def test_openapi_publishes_inventory_and_draft_scope_without_business_routes() -> None:
    schema = create_app().openapi()
    assert {item["id"] for item in schema["x-finagent-custom-validators"]} == {s.id for s in SPECS}
    assert schema["x-finagent-schema-review"]["frozen"] is True
    assert set(schema["paths"]) == {"/health", "/health/ready"}
    persisted = json.loads((ROOT / "docs/openapi.json").read_text(encoding="utf-8"))
    assert persisted == schema


def test_every_draft_integer_schema_has_safe_bounds_without_widening_field_bounds() -> None:
    def inspect(value: object) -> None:
        if isinstance(value, dict):
            if value.get("type") == "integer":
                assert value["minimum"] >= -(2**53 - 1)
                assert value["maximum"] <= 2**53 - 1
                assert not {"ge", "le", "gt", "lt"}.intersection(value)
            for child in value.values():
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)

    for model in SCHEMAS.values():
        inspect(model.model_json_schema())
    schema = SCHEMAS["policy/1"].model_json_schema()
    days = schema["$defs"]["PrivatePolicy"]["properties"]["max_retention_days"]["anyOf"][0]
    assert days["minimum"] == 0
    context = SCHEMAS["model-registry/1"].model_json_schema()["$defs"]["ModelCapability"]
    assert context["properties"]["context_tokens"]["anyOf"][0]["exclusiveMinimum"] == 0
