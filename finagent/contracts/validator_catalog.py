"""Documentation metadata only; does not import services or validate business data."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ValidatorSpec:
    id: str
    symbol: str
    models: tuple[str, ...]
    rule: str
    scope: str = "pydantic"


SPECS = (
    ValidatorSpec(
        "integer.wire",
        "finagent.contracts.base.exact_integer",
        ("MonetaryValue", "CountValue"),
        "Reject bool/float and noncanonical strings; unsafe numeric integers require strings; "
        "precision38.",
    ),
    ValidatorSpec(
        "decimal.exact",
        "finagent.contracts.base.exact_decimal",
        (
            "DecimalValue",
            "ValidationIssue",
            "ConstantExpr",
            "RuleDefinition",
            "ThresholdBoundary",
            "PillarWeight",
            "AssessmentPolicy",
            "ProviderResult",
        ),
        "Reject float/bool/nonfinite/exponent text; precision and scale38; unsafe integer "
        "tokens denied.",
    ),
    ValidatorSpec(
        "integer.metadata",
        "finagent.contracts.base.safe_metadata_integer",
        (),
        "Metadata integers stay within the JSON safe range; narrower Field bounds remain in force.",
        "common",
    ),
    ValidatorSpec(
        "integer.schema_bounds",
        "finagent.contracts.base.Contract.__get_pydantic_json_schema__",
        (),
        "Normalize constrained integer keywords, then intersect safe bounds "
        "without widening fields.",
        "common",
    ),
    ValidatorSpec(
        "period.interval",
        "finagent.contracts.base.FlowPeriod.valid_interval",
        ("FlowPeriod",),
        "start<=end; fiscal_quarter required for quarter.",
    ),
    ValidatorSpec(
        "document.public_evidence",
        "finagent.store.models.Document.public_requires_evidence",
        ("Document",),
        "Public classification requires evidence refs; does not itself authenticate those refs.",
    ),
    ValidatorSpec(
        "bbox.ordered",
        "finagent.store.models.BoundingBox.ordered",
        ("BoundingBox",),
        "x2>x1 and y2>y1.",
    ),
    ValidatorSpec(
        "provenance.chosen",
        "finagent.store.models.Provenance.chosen_exists",
        ("Provenance",),
        "chosen_reading indexes an existing reading.",
    ),
    ValidatorSpec(
        "ratio.infer_scale",
        "finagent.store.models.DecimalValue.infer_scale",
        ("DecimalValue",),
        "Derive absent scale from the exact fraction without rounding or multiplying by100.",
    ),
    ValidatorSpec(
        "ratio.scale",
        "finagent.store.models.DecimalValue.scale_matches_fraction",
        ("DecimalValue",),
        "Declared scale equals fractional decimal places; percentage is display only.",
    ),
    ValidatorSpec(
        "line.presence",
        "finagent.store.models.LineItem.presence_matches_value",
        ("LineItem",),
        "Missing iff null; zero states require zero; derived_zero requires lineage.",
    ),
    ValidatorSpec(
        "statement.period_audit",
        "finagent.store.models.Statement.correct_period_kind",
        ("Statement",),
        "B01 stock; B02/B03 flow; audited/reviewed requires audit evidence.",
    ),
    ValidatorSpec(
        "intent.rewrite",
        "finagent.llm_gateway.contracts.ReadAction.rewrite_has_no_numbers",
        ("ReadAction",),
        "Rewrite contains letters/whitespace only; name checking remains a later local guard.",
    ),
    ValidatorSpec(
        "intent.selection",
        "finagent.llm_gateway.contracts.ReadAction.explicit_selectors_for_financial_actions",
        ("ReadAction",),
        "Financial actions need entity/scope/period; statement type and exactly two "
        "comparison periods where applicable.",
    ),
    ValidatorSpec(
        "intent.clarification",
        "finagent.llm_gateway.contracts.IntentPlan.unresolved_does_not_dispatch",
        ("IntentPlan",),
        "Clarification and dispatch are exclusive; an action or clarification is required.",
    ),
    ValidatorSpec(
        "compose.claim_refs",
        "finagent.llm_gateway.contracts.FinalAnswerPayload.unique_claims_and_known_relations",
        ("FinalAnswerPayload",),
        "Claim IDs unique; qualitative relation refs must exist.",
    ),
    ValidatorSpec(
        "draft.numeric_prose",
        "finagent.llm_gateway.contracts.ProseSegment.no_numeric_characters",
        ("ProseSegment",),
        "Reject Unicode numeric characters. Full name/number-word/semantic checks remain Phase4.",
    ),
    ValidatorSpec(
        "draft.manifest_refs",
        "finagent.llm_gateway.contracts.ReferenceManifest.required_refs_are_allowed",
        ("ReferenceManifest",),
        "Required claims/warnings/render slots are subsets of allowed refs; full draft "
        "binding is Phase4.",
    ),
    ValidatorSpec(
        "gateway.manifest",
        "finagent.llm_gateway.contracts.GatewayRequest.composition_requires_manifest",
        ("GatewayRequest",),
        "Composition requires a value-free reference manifest.",
    ),
    ValidatorSpec(
        "provider.task",
        "finagent.llm_gateway.contracts.ProviderRequest.task_matches_payload_and_schema",
        ("ProviderRequest",),
        "Request task, typed user payload and output-schema ref agree.",
    ),
    ValidatorSpec(
        "provider.result",
        "finagent.llm_gateway.contracts.ProviderResult.result_matches_task",
        ("ProviderResult",),
        "Intent task returns IntentPlan; compose task returns AnswerDraft.",
    ),
    ValidatorSpec(
        "permit.tier",
        "finagent.llm_gateway.contracts.EgressPermit.tier_allows_external",
        ("EgressPermit",),
        "Strict-private denied; private needs opt-in. Runtime model terms/deadlines/one-use "
        "checks are later controls.",
    ),
    ValidatorSpec(
        "model.evidence",
        "finagent.llm_gateway.model_registry.ModelCapability.verified_requires_evidence",
        ("ModelCapability",),
        "Verified capability needs dated evidence/probes; verified training/retention needs "
        "terms refs.",
    ),
    ValidatorSpec(
        "model.registry_refs",
        "finagent.llm_gateway.model_registry.ModelRegistry.references_exist",
        ("ModelRegistry",),
        "Evidence IDs/model account keys unique; every quota/probe/terms evidence ref resolves.",
    ),
    ValidatorSpec(
        "prompt.binding_hash",
        "finagent.llm_gateway.prompts.PromptDefinition.task_contract_matches",
        ("PromptDefinition",),
        "Task matches input/output schemas and template SHA256 matches exact UTF-8 bytes.",
    ),
    ValidatorSpec(
        "prompt.unique",
        "finagent.llm_gateway.prompts.PromptRegistry.unique_versions",
        ("PromptRegistry",),
        "Prompt ID/version/language keys unique.",
    ),
    ValidatorSpec(
        "ast.budget",
        "finagent.policy.expression_limits.guard_expression",
        ("RatioDefinition", "RuleDefinition"),
        "Iterative pre-validation: depth32, total1024 occurrences, fanout100; reject cycles.",
        "preflight",
    ),
    ValidatorSpec(
        "rule.combined_budget",
        "finagent.policy.contracts.RuleDefinition.combined_expression_budget",
        ("RuleDefinition",),
        "Node budget shared by both rule expression sides.",
    ),
    ValidatorSpec(
        "rule.tolerance",
        "finagent.policy.contracts.RuleDefinition.nonnegative_tolerance",
        ("RuleDefinition",),
        "Tolerance cannot be negative.",
    ),
    ValidatorSpec(
        "template.codes",
        "finagent.policy.contracts.TemplateDefinition.unique_codes",
        ("TemplateDefinition",),
        "Statement-type/code keys unique.",
    ),
    ValidatorSpec(
        "threshold.bounds",
        "finagent.policy.contracts.ThresholdBand.ordered_bounds",
        ("ThresholdBand",),
        "Bounds ordered; equal endpoints require both inclusive. Overlap/gap classification "
        "remains Phase3.",
    ),
    ValidatorSpec(
        "membership.scoring",
        "finagent.policy.contracts.RatioMembership.scoring_is_displayed",
        ("RatioMembership",),
        "Scoring pillar is displayed; scoring role and pillar presence agree.",
    ),
    ValidatorSpec(
        "assessment.owner_policy",
        "finagent.policy.contracts.AssessmentPolicy.profile_matches_owner_decision",
        ("AssessmentPolicy",),
        "Five distinct equal pillars, fixed ICR cap boundary; APPROVED requires corpus-run "
        "approval ref.",
    ),
    ValidatorSpec(
        "pack.memberships",
        "finagent.policy.contracts.SectorPack.single_scoring_membership",
        ("SectorPack",),
        "No duplicate ratio membership; OCF14 scores only at cashflow.",
    ),
    ValidatorSpec(
        "registry.bundle",
        "finagent.policy.registry.validate_bundle",
        (
            "TemplateDefinition",
            "RatioDefinition",
            "RuleDefinition",
            "SectorPack",
            "RoleDefinition",
            "ToolDefinition",
            "ApplicabilityDefinition",
        ),
        "Separate loader: unique/versioned entries, approved/source/test refs, known refs, "
        "compatible core/strategy, DAG, generic pack.",
        "loader",
    ),
    ValidatorSpec(
        "token.collision",
        "finagent.llm_gateway.tokens.RunTokenAllocator.allocate",
        ("GatewayReviewCatalog",),
        "Run-local random8 aliases; normalized query/used-suffix collision checks and bounded "
        "retries; IDs128 remain local.",
        "preflight",
    ),
)


def validator_catalog() -> list[dict[str, object]]:
    return [_json_record(spec) for spec in SPECS]


def _json_record(spec: ValidatorSpec) -> dict[str, object]:
    record = asdict(spec)
    record["models"] = list(spec.models)
    return record


def validators_for_schema(schema: dict[str, object]) -> list[dict[str, object]]:
    definitions = schema.get("$defs", {})
    names = set(definitions) if isinstance(definitions, dict) else set()
    names.add(str(schema.get("title", "")))
    return [
        _json_record(spec)
        for spec in SPECS
        if spec.scope == "common" or names.intersection(spec.models)
    ]
