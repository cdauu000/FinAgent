"""Gateway/1 drafts. Financial values and local identity maps are absent by construction."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import Field, StringConstraints, field_validator, model_validator

from finagent.contracts.base import (
    Contract,
    ExactDecimal,
    ExecutionContext,
    Identifier,
    NonEmpty,
    RegistryRef,
    SafeInt,
    Scope,
    Sha256,
    Tier,
    Verdict,
)

# A61 approved run-local alias spelling; never tenant-stable by default.
EntityToken = Annotated[str, StringConstraints(pattern=r"^ent_[0-9abcdefghjkmnpqrstvwxyz]{8}$")]
NumberPlaceholder = Annotated[
    str, StringConstraints(pattern=r"^num_[0-9abcdefghjkmnpqrstvwxyz]{8}$")
]
ConceptLabel = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z_.]*$", max_length=160)]


class GatewayTask(StrEnum):
    INTENT = "intent_parse"
    COMPOSE = "answer_compose"


class Clarification(StrEnum):
    ENTITY = "ENTITY"
    PERIOD = "PERIOD"
    SCOPE = "SCOPE"
    RATIO = "RATIO"
    AMBIGUOUS_REQUEST = "AMBIGUOUS_REQUEST"


class SessionSelection(Contract):
    entity_token: EntityToken | None = None
    period_code: Identifier | None = None
    scope: Scope | None = None
    selection_revision: SafeInt = Field(ge=1)


class IntentPayload(Contract):
    task: Literal["intent_parse"] = "intent_parse"
    query: NonEmpty
    selection: SessionSelection
    number_placeholders: tuple[NumberPlaceholder, ...] = ()
    history: tuple[()] = ()
    language: Literal["vi", "en"] = "vi"


class ReadAction(Contract):
    action: Literal[
        "get_statement",
        "list_periods",
        "list_documents",
        "get_document_status",
        "compute_ratios",
        "compute_trend",
        "compare_periods",
        "compute_piotroski",
        "assess_health",
        "explain_ratio",
        "search_evidence",
        "get_note_table",
        "get_validation_report",
        "get_industry_context",
    ]
    entity_token: EntityToken | None = None
    period_codes: tuple[Identifier, ...] = ()
    scope: Scope | None = None
    ratio_ids: tuple[Identifier, ...] = ()
    concept_ids: tuple[Identifier, ...] = ()
    resource_refs: tuple[Identifier, ...] = ()
    statement_type: Literal["B01", "B02", "B03", "B09"] | None = None
    comparison_mode: Literal["annual_yoy", "same_quarter_yoy", "adjacent", "ttm"] | None = None
    cash_basis: Literal["cash_only", "cash_and_short_term_investments"] | None = None
    receivables_basis: Literal["customer_131", "total_130"] | None = None
    query_rewrite: str | None = None

    @field_validator("query_rewrite")
    @classmethod
    def rewrite_has_no_numbers(cls, value: str | None) -> str | None:
        if value is not None and not all(ch.isalpha() or ch.isspace() for ch in value):
            raise ValueError("REWRITE_LETTERS_ONLY")
        return value

    @model_validator(mode="after")
    def explicit_selectors_for_financial_actions(self) -> Self:
        needs_selection = {
            "get_statement",
            "compute_ratios",
            "compute_trend",
            "compare_periods",
            "compute_piotroski",
            "assess_health",
        }
        if self.action in needs_selection and (
            self.entity_token is None or self.scope is None or not self.period_codes
        ):
            raise ValueError("EXPLICIT_SELECTION_REQUIRED")
        if self.action == "get_statement" and self.statement_type is None:
            raise ValueError("STATEMENT_TYPE_REQUIRED")
        if self.action == "compare_periods" and len(self.period_codes) != 2:
            raise ValueError("TWO_PERIODS_REQUIRED")
        return self


class VerifyUserClaimAction(Contract):
    action: Literal["verify_user_claim"] = "verify_user_claim"
    placeholder_ref: NumberPlaceholder
    claim_kind: Identifier
    entity_token: EntityToken | None = None
    period_code: Identifier | None = None
    scope: Scope | None = None


class RequestExportAction(Contract):
    action: Literal["request_export"] = "request_export"
    format: Literal["json", "md", "xlsx"]
    purpose: Literal["interactive", "official"]


class DeclineAction(Contract):
    action: Literal["decline"] = "decline"
    reason: Literal["OUT_OF_DOMAIN_ADVICE", "FORECAST", "MARKET_PRICE", "UNSUPPORTED"]


IntentAction = Annotated[
    ReadAction | VerifyUserClaimAction | RequestExportAction | DeclineAction,
    Field(discriminator="action"),
]


class IntentPlan(Contract):
    actions: tuple[IntentAction, ...] = ()
    clarification: Clarification | None = None

    @model_validator(mode="after")
    def unresolved_does_not_dispatch(self) -> Self:
        if self.clarification is not None and self.actions:
            raise ValueError("CLARIFICATION_CANNOT_DISPATCH_ACTIONS")
        if self.clarification is None and not self.actions:
            raise ValueError("ACTION_OR_CLARIFICATION_REQUIRED")
        return self


class QualitativeRelation(Contract):
    other_claim_id: Identifier
    relation: Literal["higher", "lower", "equal", "increased", "decreased", "unchanged"]


class ClaimDescriptor(Contract):
    claim_id: Identifier
    concept_label: ConceptLabel
    status: Literal["NORMAL", "N_A", "NOT_MEANINGFUL", "UNAVAILABLE", "UNVERIFIED"]
    band: Literal["weak", "medium", "good", "unscored"] = "unscored"
    qualitative_relations: tuple[QualitativeRelation, ...] = ()
    warning_codes: tuple[Identifier, ...] = ()
    period_code: Identifier
    scope: Scope


class FinalAnswerPayload(Contract):
    task: Literal["answer_compose"] = "answer_compose"
    claims: tuple[ClaimDescriptor, ...]
    status: Verdict
    entity_tokens: tuple[EntityToken, ...] = ()
    language: Literal["vi", "en"] = "vi"

    @model_validator(mode="after")
    def unique_claims_and_known_relations(self) -> Self:
        ids = [claim.claim_id for claim in self.claims]
        if len(ids) != len(set(ids)):
            raise ValueError("DUPLICATE_CLAIM")
        if any(
            relation.other_claim_id not in ids
            for claim in self.claims
            for relation in claim.qualitative_relations
        ):
            raise ValueError("UNKNOWN_RELATED_CLAIM")
        return self


class ProseSegment(Contract):
    type: Literal["prose"] = "prose"
    text: NonEmpty

    @field_validator("text")
    @classmethod
    def no_numeric_characters(cls, text: str) -> str:
        if any(ch.isnumeric() for ch in text):
            raise ValueError("FORBIDDEN_PROSE_NUMBER")
        return text


class ClaimRefSegment(Contract):
    type: Literal["claim_ref"] = "claim_ref"
    claim_id: Identifier
    render: Literal["value", "label", "period", "scope", "status"]


class WarningRefSegment(Contract):
    type: Literal["warning_ref"] = "warning_ref"
    code: Identifier


class EntityRefSegment(Contract):
    type: Literal["entity_ref"] = "entity_ref"
    token: EntityToken


DraftSegment = Annotated[
    ProseSegment | ClaimRefSegment | WarningRefSegment | EntityRefSegment,
    Field(discriminator="type"),
]


class AnswerDraft(Contract):
    segments: tuple[DraftSegment, ...] = Field(min_length=1)


class RequiredClaimSlot(Contract):
    claim_id: Identifier
    render: Literal["value", "label", "period", "scope", "status"]


class ReferenceManifest(Contract):
    claim_ids: tuple[Identifier, ...]
    required_claim_ids: tuple[Identifier, ...]
    warning_codes: tuple[Identifier, ...]
    required_warning_codes: tuple[Identifier, ...]
    entity_tokens: tuple[EntityToken, ...]
    required_slots: tuple[RequiredClaimSlot, ...]
    version: str

    @model_validator(mode="after")
    def required_refs_are_allowed(self) -> Self:
        if not set(self.required_claim_ids) <= set(self.claim_ids):
            raise ValueError("UNKNOWN_REQUIRED_CLAIM")
        if not set(self.required_warning_codes) <= set(self.warning_codes):
            raise ValueError("UNKNOWN_REQUIRED_WARNING")
        if any(slot.claim_id not in self.claim_ids for slot in self.required_slots):
            raise ValueError("UNKNOWN_SLOT_CLAIM")
        return self


Payload = Annotated[IntentPayload | FinalAnswerPayload, Field(discriminator="task")]


class GatewayRequest(Contract):
    schema_version: Literal["gateway/1"] = "gateway/1"
    request_id: Identifier
    payload: Payload
    context: ExecutionContext
    reference_manifest: ReferenceManifest | None = None
    prompt_ref: RegistryRef
    registry_version: str
    idempotency_key: Identifier
    answer_set_hash: Sha256 | None = None

    @model_validator(mode="after")
    def composition_requires_manifest(self) -> Self:
        if isinstance(self.payload, FinalAnswerPayload) and self.reference_manifest is None:
            raise ValueError("REFERENCE_MANIFEST_REQUIRED")
        return self


class SystemMessage(Contract):
    """Content must come from PromptRegistry, never documents, tools or user history."""

    role: Literal["system"] = "system"
    content: NonEmpty
    prompt_hash: Sha256


class UserPayloadMessage(Contract):
    role: Literal["user"] = "user"
    payload: Payload


class ProviderRequest(Contract):
    """Closed message shapes; adapters may serialize but never append tool/history data."""

    provider: Identifier
    model: Identifier
    task: GatewayTask
    messages: tuple[SystemMessage, UserPayloadMessage]
    prompt_ref: RegistryRef
    output_schema_ref: Literal["IntentPlan", "AnswerDraft"]
    structured_strategy: Literal["native_schema", "tool_call_schema", "json_mode"]
    stream: Literal[False] = False
    hedging: Literal[False] = False
    timeout_seconds: float = Field(gt=0, allow_inf_nan=False)
    permit_id: Identifier

    @model_validator(mode="after")
    def task_matches_payload_and_schema(self) -> Self:
        if self.messages[1].payload.task != self.task:
            raise ValueError("TASK_PAYLOAD_MISMATCH")
        expected = "IntentPlan" if self.task == GatewayTask.INTENT else "AnswerDraft"
        if self.output_schema_ref != expected:
            raise ValueError("TASK_SCHEMA_MISMATCH")
        return self


class Usage(Contract):
    input_tokens: SafeInt = Field(ge=0)
    output_tokens: SafeInt = Field(ge=0)
    cached_tokens: SafeInt = Field(default=0, ge=0)


class GatewayError(Contract):
    code: Literal[
        "TIMEOUT",
        "UPSTREAM_5XX",
        "NETWORK_ERROR",
        "RATE_LIMITED",
        "AUTH_FAILED",
        "POLICY_DENIED",
        "SCHEMA_INVALID",
        "CONTENT_BLOCKED",
        "MODEL_UNAVAILABLE",
        "CONTEXT_TOO_LARGE",
        "BUDGET_EXCEEDED",
        "UNKNOWN_OUTCOME",
    ]
    retryable: bool
    trace_ref: Identifier


class ProviderResult(Contract):
    provider: Identifier
    model: Identifier
    task: GatewayTask
    candidate: IntentPlan | AnswerDraft
    usage: Usage
    latency_seconds: float = Field(ge=0, allow_inf_nan=False)
    estimated_cost: ExactDecimal | None = None
    price_evidence_ref: Identifier | None = None
    prompt_ref: RegistryRef
    registry_version: str
    schema_version: Literal["gateway/1"] = "gateway/1"

    @model_validator(mode="after")
    def result_matches_task(self) -> Self:
        if (self.task == GatewayTask.INTENT) != isinstance(self.candidate, IntentPlan):
            raise ValueError("TASK_RESULT_MISMATCH")
        return self


class GatewayOutcome(Contract):
    source: Literal["provider", "local"]
    result: IntentPlan | AnswerDraft
    degraded: bool
    fallback_reason: Identifier | None = None
    trace_ref: Identifier
    schema_version: Literal["gateway/1"] = "gateway/1"
    prompt_ref: RegistryRef
    registry_version: str


class EgressPermit(Contract):
    id: Identifier
    task: GatewayTask
    environment: Literal["runtime", "development"]
    tenant_id: Identifier
    source_tier: Tier
    tenant_opt_in: bool
    provider: Identifier
    model: Identifier
    payload_hash: Sha256
    policy_ref: RegistryRef
    expires_at: datetime
    max_tokens: SafeInt = Field(gt=0)

    @model_validator(mode="after")
    def tier_allows_external(self) -> Self:
        if self.source_tier == Tier.STRICT_PRIVATE:
            raise ValueError("STRICT_PRIVATE_EXTERNAL_FORBIDDEN")
        if self.source_tier == Tier.PRIVATE and not self.tenant_opt_in:
            raise ValueError("PRIVATE_OPT_IN_REQUIRED")
        return self


class GatewayCatalog(Contract):
    request: GatewayRequest | None = None
    provider_request: ProviderRequest | None = None
    provider_result: ProviderResult | None = None
    outcome: GatewayOutcome | None = None
    error: GatewayError | None = None
    draft: AnswerDraft | None = None
    manifest: ReferenceManifest | None = None
    permit: EgressPermit | None = None
