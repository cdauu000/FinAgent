from decimal import Decimal

import pytest
from pydantic import ValidationError

from finagent.policy.contracts import (
    AssessmentPolicy,
    RatioDefinition,
    RegistryBundle,
    RoleDefinition,
    SectorPack,
)
from finagent.policy.registry import validate_bundle


def ratio(identifier: str, dependencies: list[dict[str, str]] | None = None) -> RatioDefinition:
    return RatioDefinition.model_validate(
        {
            "id": identifier,
            "version": "1",
            "source_refs": ["synthetic-source"],
            "mandatory_test_refs": ["synthetic-test"],
            "formula": {"kind": "fact", "concept_id": "assets", "period_role": "closing"},
            "input_concepts": ["assets"],
            "dependencies": dependencies or [],
            "measure_kind": "ratio",
            "period_basis": "stock",
            "display_kind": "decimal",
            "definition_role": "experimental",
        }
    )


def test_draft_registry_cannot_become_runtime_approved_by_loading() -> None:
    bundle = RegistryBundle(ratios=(ratio("synthetic"),))
    validate_bundle(bundle, require_approved=False)
    with pytest.raises(ValueError, match="DRAFT_NOT_RUNTIME_ELIGIBLE"):
        validate_bundle(bundle)
    with pytest.raises(ValueError, match="APPROVED_GENERIC_PACK_REQUIRED"):
        validate_bundle(RegistryBundle())


def test_dependency_cycles_duplicates_and_unknown_refs_rejected() -> None:
    a = ratio("ratio-a", [{"id": "ratio-b", "version": "1"}])
    b = ratio("ratio-b", [{"id": "ratio-a", "version": "1"}])
    with pytest.raises(ValueError, match="CYCLIC_RATIO_DEPENDENCY"):
        validate_bundle(RegistryBundle(ratios=(a, b)), require_approved=False)
    with pytest.raises(ValueError, match="UNKNOWN_RATIO_DEPENDENCY"):
        validate_bundle(RegistryBundle(ratios=(a,)), require_approved=False)
    with pytest.raises(ValueError, match="DUPLICATE_REGISTRY_ENTRY"):
        validate_bundle(RegistryBundle(ratios=(a, a)), require_approved=False)


@pytest.mark.parametrize(
    "formula",
    [
        {"kind": "python", "code": "__import__('os')"},
        {"kind": "binary", "op": "eval", "left": {}, "right": {}},
        {"kind": "fact", "concept_id": "assets", "period_role": "closing", "code": "eval('1')"},
    ],
)
def test_declarative_dsl_has_no_executable_escape(formula: object) -> None:
    data = ratio("synthetic").model_dump()
    with pytest.raises(ValidationError):
        RatioDefinition.model_validate({**data, "formula": formula})


def assessment() -> dict[str, object]:
    return {
        "basis_approval_ref": "owner-2026-11-02",
        "pillar_weights": [
            {"pillar_id": pillar, "weight": "0.2"}
            for pillar in ("liquidity", "leverage", "efficiency", "profitability", "cashflow")
        ],
    }


def test_assessment_basis_does_not_bypass_corpus_run_approval() -> None:
    profile = AssessmentPolicy.model_validate(assessment())
    assert profile.validation_status == "POLICY_UNAPPROVED"
    assert profile.low_icr_boundary == Decimal("1.5")
    assert profile.piotroski_weight == profile.trend_weight == 0
    assert profile.negative_equity_cap == "weak"
    assert profile.negative_ocf_and_low_icr_cap == "medium"
    with pytest.raises(ValidationError, match="CORPUS_RUN_APPROVAL_REQUIRED"):
        AssessmentPolicy.model_validate({**assessment(), "validation_status": "APPROVED"})


def test_ocf14_can_display_twice_but_score_only_at_cashflow() -> None:
    membership = {
        "ratio_ref": {"id": "ocf_current_liabilities", "version": "1"},
        "display_pillars": ["liquidity", "cashflow"],
        "scoring_pillar": "cashflow",
        "role": "scoring",
    }
    pack = {
        "id": "generic",
        "version": "1",
        "source_refs": ["source-a"],
        "mandatory_test_refs": ["test-a"],
        "min_core_version": "0.0.1",
        "template_refs": [],
        "ratio_memberships": [membership],
        "thresholds": [],
        "assessment_policy": assessment(),
    }
    assert SectorPack.model_validate(pack).ratio_memberships[0].scoring_pillar == "cashflow"
    with pytest.raises(ValidationError, match="OCF_SCORED_ONLY_IN_CASHFLOW"):
        SectorPack.model_validate(
            {**pack, "ratio_memberships": [{**membership, "scoring_pillar": "liquidity"}]}
        )
    with pytest.raises(ValidationError, match="DUPLICATE_RATIO_MEMBERSHIP"):
        SectorPack.model_validate({**pack, "ratio_memberships": [membership, membership]})


def test_pack_cannot_override_formula_or_require_future_core() -> None:
    data = {
        "id": "generic",
        "version": "1",
        "source_refs": ["source-a"],
        "mandatory_test_refs": ["test-a"],
        "min_core_version": "99.0.0",
        "template_refs": [],
        "ratio_memberships": [],
        "thresholds": [],
    }
    with pytest.raises(ValidationError):
        SectorPack.model_validate({**data, "formulas": {"current": "unsafe override"}})
    with pytest.raises(ValueError, match="INCOMPATIBLE_CORE_VERSION"):
        validate_bundle(
            RegistryBundle(packs=(SectorPack.model_validate(data),)), require_approved=False
        )


def test_strategy_extension_needs_registration_not_a_core_schema_change() -> None:
    role = RoleDefinition.model_validate(
        {
            "id": "fixture-role",
            "version": "1",
            "source_refs": ["synthetic-source"],
            "mandatory_test_refs": ["synthetic-test"],
            "purpose_key": "fixture.role",
            "allowed_tool_refs": [],
            "strategy": "fixture-strategy",
            "input_schema_ref": "FixtureInput",
            "output_schema_ref": "FixtureOutput",
            "max_tool_calls": 1,
            "max_tokens": 1,
            "deadline_seconds": 1,
        }
    )
    bundle = RegistryBundle(roles=(role,))
    with pytest.raises(ValueError, match="UNSUPPORTED_STRATEGY"):
        validate_bundle(bundle, require_approved=False)
    validate_bundle(
        bundle,
        require_approved=False,
        available_strategies=frozenset({"single", "fixture-strategy"}),
    )
