"""Policy, registry and safe-expression drafts for the P0.05 review gate."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BeforeValidator, Field, model_validator

from finagent.contracts.base import (
    Contract,
    ExactDecimal,
    Identifier,
    Mode,
    RegistryRef,
    SafeInt,
    Sha256,
    Tier,
    Version,
)
from finagent.policy.expression_limits import check_expression_roots, guard_expression


class ConstantExpr(Contract):
    kind: Literal["constant"] = "constant"
    value: ExactDecimal


class FactExpr(Contract):
    kind: Literal["fact"] = "fact"
    concept_id: Identifier
    period_role: Literal["selected", "opening", "closing", "prior_comparable"]


class BinaryExpr(Contract):
    kind: Literal["binary"] = "binary"
    op: Literal["add", "subtract", "multiply", "divide"]
    left: Expression
    right: Expression


class AggregateExpr(Contract):
    kind: Literal["aggregate"] = "aggregate"
    op: Literal["sum", "average"]
    # A61 approved aggregate-width bound; never discard real data to fit it.
    inputs: tuple[Expression, ...] = Field(min_length=1, max_length=100)


Expression = Annotated[
    ConstantExpr | FactExpr | BinaryExpr | AggregateExpr,
    Field(discriminator="kind"),
    BeforeValidator(guard_expression),
]
BinaryExpr.model_rebuild()
AggregateExpr.model_rebuild()


class RegistryDefinition(Contract):
    id: Identifier
    version: str = Field(pattern=r"^[0-9]+(?:\.[0-9]+){0,2}$")
    status: Literal["draft", "approved", "deprecated"] = "draft"
    source_refs: tuple[Identifier, ...]
    mandatory_test_refs: tuple[Identifier, ...]


class RatioDefinition(RegistryDefinition):
    schema_version: Literal["ratio-def/1"] = "ratio-def/1"
    formula: Expression
    input_concepts: tuple[Identifier, ...]
    dependencies: tuple[RegistryRef, ...] = ()
    measure_kind: Literal["ratio", "count", "money"]
    period_basis: Literal["stock", "quarter", "annual", "ytd", "ttm"]
    display_kind: Literal["decimal", "percent", "count", "money"]
    definition_role: Literal["core", "variant", "reference", "experimental"]
    base_definition_ref: RegistryRef | None = None
    rounding: Literal["ROUND_HALF_UP"] = "ROUND_HALF_UP"
    decimal_precision: Literal[38] = 38


class RuleDefinition(RegistryDefinition):
    schema_version: Literal["rule/1"] = "rule/1"
    template_ref: RegistryRef
    group: Literal["A", "B", "C", "D", "E", "F"]
    severity: Literal["BLOCK", "WARN", "INFO"]
    left: Expression
    right: Expression
    comparison: Literal["equal", "less_equal", "greater_equal"]
    tolerance: ExactDecimal

    @model_validator(mode="before")
    @classmethod
    def combined_expression_budget(cls, data: object) -> object:
        if isinstance(data, dict):
            check_expression_roots((data.get("left"), data.get("right")))
        return data

    @model_validator(mode="after")
    def nonnegative_tolerance(self) -> Self:
        if self.tolerance < 0:
            raise ValueError("NEGATIVE_TOLERANCE")
        return self


class TemplateMapping(Contract):
    statement_type: Literal["B01", "B02", "B03", "B09"]
    code: str = Field(pattern=r"^[0-9]+[a-z]?$")
    concept_id: Identifier
    is_memo: bool = False


class TemplateDefinition(RegistryDefinition):
    schema_version: Literal["template/1"] = "template/1"
    statement_family: Identifier
    observed_source_hashes: tuple[Sha256, ...]
    mappings: tuple[TemplateMapping, ...]
    required_total_codes: tuple[str, ...]

    @model_validator(mode="after")
    def unique_codes(self) -> Self:
        keys = [(item.statement_type, item.code) for item in self.mappings]
        if len(keys) != len(set(keys)):
            raise ValueError("DUPLICATE_TEMPLATE_CODE")
        return self


class ThresholdBoundary(Contract):
    value: ExactDecimal
    inclusive: bool


class ThresholdBand(Contract):
    ratio_ref: RegistryRef
    label: Literal["good", "medium", "weak"]
    lower: ThresholdBoundary | None = None
    upper: ThresholdBoundary | None = None
    period_basis: Literal["stock", "quarter", "annual", "ytd", "ttm"]
    source_ref: Identifier
    status: Literal["draft", "approved"] = "draft"

    @model_validator(mode="after")
    def ordered_bounds(self) -> Self:
        if self.lower is not None and self.upper is not None:
            if self.lower.value > self.upper.value:
                raise ValueError("REVERSED_THRESHOLD_BOUNDS")
            if self.lower.value == self.upper.value and not (
                self.lower.inclusive and self.upper.inclusive
            ):
                raise ValueError("EMPTY_THRESHOLD_INTERVAL")
        return self


class RatioMembership(Contract):
    ratio_ref: RegistryRef
    display_pillars: tuple[Identifier, ...] = Field(min_length=1)
    scoring_pillar: Identifier | None = None
    role: Literal["scoring", "reference", "hidden"]

    @model_validator(mode="after")
    def scoring_is_displayed(self) -> Self:
        if self.scoring_pillar is not None and self.scoring_pillar not in self.display_pillars:
            raise ValueError("SCORING_PILLAR_NOT_DISPLAYED")
        if (self.role == "scoring") != (self.scoring_pillar is not None):
            raise ValueError("SCORING_MEMBERSHIP_REQUIRED")
        return self


class PillarWeight(Contract):
    pillar_id: Identifier
    weight: ExactDecimal


class AssessmentPolicy(Contract):
    profile_id: Literal["generic-score/0"] = "generic-score/0"
    basis_approval_ref: Identifier
    validation_status: Literal["POLICY_UNAPPROVED", "APPROVED"] = "POLICY_UNAPPROVED"
    corpus_run_approval_ref: Identifier | None = None
    good_points: Literal[100] = 100
    medium_points: Literal[50] = 50
    weak_points: Literal[0] = 0
    good_grade_from: Literal[75] = 75
    medium_grade_from: Literal[50] = 50
    pillar_weights: tuple[PillarWeight, ...] = Field(min_length=5, max_length=5)
    ocf_ratio_id: Identifier = "ocf_current_liabilities"
    ocf_scoring_pillar: Literal["cashflow"] = "cashflow"
    piotroski_weight: Literal[0] = 0
    trend_weight: Literal[0] = 0
    unclassified_action: Literal["exclude_from_score"] = "exclude_from_score"
    negative_equity_cap: Literal["weak"] = "weak"
    negative_ocf_and_low_icr_cap: Literal["medium"] = "medium"
    low_icr_boundary: ExactDecimal = Decimal("1.5")
    requires_verified: Literal[True] = True
    requires_coverage: Literal[True] = True
    disclaimer_key: Literal["assessment.convention_unvalidated_not_investment_advice"] = (
        "assessment.convention_unvalidated_not_investment_advice"
    )

    @model_validator(mode="after")
    def profile_matches_owner_decision(self) -> Self:
        if len({item.pillar_id for item in self.pillar_weights}) != 5:
            raise ValueError("FIVE_DISTINCT_PILLARS_REQUIRED")
        if any(item.weight != Decimal("0.2") for item in self.pillar_weights):
            raise ValueError("GENERIC_PILLAR_WEIGHT_MUST_BE_ONE_FIFTH")
        if self.low_icr_boundary != Decimal("1.5"):
            raise ValueError("GENERIC_ICR_CAP_BOUNDARY_FIXED")
        if self.validation_status == "APPROVED" and self.corpus_run_approval_ref is None:
            raise ValueError("CORPUS_RUN_APPROVAL_REQUIRED")
        return self


class SectorPack(RegistryDefinition):
    schema_version: Literal["spack/1"] = "spack/1"
    min_core_version: Version
    template_refs: tuple[RegistryRef, ...]
    ratio_memberships: tuple[RatioMembership, ...]
    thresholds: tuple[ThresholdBand, ...]
    assessment_policy: AssessmentPolicy | None = None
    applicability_refs: tuple[RegistryRef, ...] = ()
    piotroski_policy: Literal["standard", "variant", "not_applicable"] = "standard"
    forbidden_claim_keys: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def single_scoring_membership(self) -> Self:
        keys = [(item.ratio_ref.id, item.ratio_ref.version) for item in self.ratio_memberships]
        if len(keys) != len(set(keys)):
            raise ValueError("DUPLICATE_RATIO_MEMBERSHIP")
        if self.assessment_policy is not None:
            for member in self.ratio_memberships:
                if member.ratio_ref.id == self.assessment_policy.ocf_ratio_id and (
                    member.scoring_pillar not in {None, "cashflow"}
                ):
                    raise ValueError("OCF_SCORED_ONLY_IN_CASHFLOW")
        return self


class ToolDefinition(RegistryDefinition):
    schema_version: Literal["tool/1"] = "tool/1"
    input_schema_ref: Identifier
    output_schema_ref: Identifier
    permissions: tuple[Identifier, ...]
    side_effect: bool
    budget_class: Identifier


class RoleDefinition(RegistryDefinition):
    schema_version: Literal["role/1"] = "role/1"
    purpose_key: Identifier
    allowed_tool_refs: tuple[RegistryRef, ...]
    strategy: Identifier = "single"
    input_schema_ref: Identifier
    output_schema_ref: Identifier
    max_tool_calls: SafeInt = Field(gt=0)
    max_tokens: SafeInt = Field(gt=0)
    deadline_seconds: float = Field(gt=0, allow_inf_nan=False)
    model_task_route_refs: tuple[RegistryRef, ...] = ()


class RoleMessage(Contract):
    message_id: Identifier
    run_id: Identifier
    parent_id: Identifier | None = None
    from_role: Identifier
    to_role: Identifier
    purpose: Identifier
    input_ref: Identifier
    output_ref: Identifier | None = None
    evidence_ids: tuple[Identifier, ...]
    policy_ref: RegistryRef
    source_tier: Tier
    mode: Mode
    consumed_steps: SafeInt = Field(ge=0)
    consumed_tokens: SafeInt = Field(ge=0)
    trace_parent: Identifier | None = None


class RoleCatalog(Contract):
    definition: RoleDefinition | None = None
    message: RoleMessage | None = None


class ApplicabilityDefinition(RegistryDefinition):
    schema_version: Literal["applicability/1"] = "applicability/1"
    condition_refs: tuple[Identifier, ...]
    required_evidence_concepts: tuple[Identifier, ...]
    effect: Literal["APPLICABLE", "N_A", "NOT_MEANINGFUL"]
    warning_codes: tuple[Identifier, ...]


class PrivatePolicy(Contract):
    opt_in: bool = False
    max_retention_days: SafeInt | None = Field(default=None, ge=0, strict=True)
    artifact_retention_days: Literal[30] = 30


class Limits(Contract):
    file_bytes: Literal[52428800] = 52428800
    pages: Literal[300] = 300
    url_body_bytes: Literal[20971520] = 20971520
    url_redirects: Literal[3] = 3
    url_timeout_seconds: Literal[15] = 15
    archive_expansion_ratio: Literal[100] = 100
    archive_expanded_bytes: Literal[209715200] = 209715200


class PolicySnapshot(Contract):
    schema_version: Literal["policy/1"] = "policy/1"
    policy_ref: RegistryRef
    mode: Mode
    source_tier: Tier = Tier.PRIVATE
    paid_fallback: bool = False
    private: PrivatePolicy = PrivatePolicy()
    limits: Limits = Limits()
    registry_refs: tuple[RegistryRef, ...]
    content_hash: Sha256
    resolved_at: datetime


class RegistryBundle(Contract):
    templates: tuple[TemplateDefinition, ...] = ()
    ratios: tuple[RatioDefinition, ...] = ()
    rules: tuple[RuleDefinition, ...] = ()
    packs: tuple[SectorPack, ...] = ()
    tools: tuple[ToolDefinition, ...] = ()
    roles: tuple[RoleDefinition, ...] = ()
    applicability: tuple[ApplicabilityDefinition, ...] = ()
