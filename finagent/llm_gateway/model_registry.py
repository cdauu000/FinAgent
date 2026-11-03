"""Model-registry/1 drafts. No real model or quota is pre-populated."""

from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from finagent.contracts.base import Contract, Identifier, NonEmpty, SafeInt
from finagent.llm_gateway.contracts import GatewayTask


class EvidenceSource(Contract):
    id: Identifier
    official_url: NonEmpty
    checked_at: datetime
    account_scope: Identifier | None = None
    plan: str | None = None
    region: str | None = None
    artifact_ref: Identifier | None = None


class NoRetention(Contract):
    kind: Literal["none_verified"] = "none_verified"


class LimitedRetention(Contract):
    kind: Literal["limited"] = "limited"
    days: SafeInt = Field(ge=0, strict=True)


class IndefiniteRetention(Contract):
    kind: Literal["indefinite"] = "indefinite"


class UnknownRetention(Contract):
    kind: Literal["unknown"] = "unknown"


Retention = Annotated[
    NoRetention | LimitedRetention | IndefiniteRetention | UnknownRetention,
    Field(discriminator="kind"),
]


class QuotaBucketKey(Contract):
    provider: Identifier
    account_scope: Identifier
    model: Identifier


class QuotaRecord(Contract):
    dimension: Literal["rpm", "tpm", "rpd", "tpd", "input_tpm", "output_tpm", "concurrency"]
    limit: SafeInt = Field(gt=0, strict=True)
    source: Literal["manual_console", "probe", "header_hint"]
    checked_at: datetime
    evidence_ref: Identifier
    observed_at: datetime | None = None


class QuotaReservation(Contract):
    status: Literal["reserved"] = "reserved"
    reservation_id: Identifier
    bucket: QuotaBucketKey
    tenant_id: Identifier
    estimated_tokens: SafeInt = Field(ge=0, strict=True)
    deadline: datetime


class QuotaDenied(Contract):
    status: Literal["denied"] = "denied"
    reason: Literal["QUOTA_EXHAUSTED", "NO_TENANT_ALLOCATION", "BACKEND_UNAVAILABLE"]
    retry_after: datetime | None = None


class StructuredCapability(Contract):
    task: GatewayTask
    structured_strategy: Literal["native_schema", "tool_call_schema", "json_mode"]
    checked_at: datetime
    probe_evidence_ref: Identifier


class ModelCapability(Contract):
    provider: Identifier
    model: Identifier
    account_scope: Identifier
    status: Literal["unverified", "verified", "deprecated"] = "unverified"
    checked_at: datetime | None = None
    training_use: Literal["none_verified", "may_use", "unknown"] = "unknown"
    retention: Retention = UnknownRetention()
    terms_evidence_refs: tuple[Identifier, ...] = ()
    structured_capabilities: tuple[StructuredCapability, ...] = ()
    quota_records: tuple[QuotaRecord, ...] = ()
    context_tokens: SafeInt | None = Field(default=None, gt=0)
    evidence_refs: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def verified_requires_evidence(self) -> Self:
        if self.status == "verified" and (
            self.checked_at is None or not self.evidence_refs or not self.structured_capabilities
        ):
            raise ValueError("VERIFIED_CAPABILITY_EVIDENCE_REQUIRED")
        if (self.training_use == "none_verified" or self.retention.kind != "unknown") and (
            not self.terms_evidence_refs
        ):
            raise ValueError("TERMS_EVIDENCE_REQUIRED")
        return self


class ModelRegistry(Contract):
    schema_version: Literal["model-registry/1"] = "model-registry/1"
    status: Literal["draft", "approved"] = "draft"
    entries: tuple[ModelCapability, ...] = ()
    evidence: tuple[EvidenceSource, ...] = ()

    @model_validator(mode="after")
    def references_exist(self) -> Self:
        evidence_ids = {item.id for item in self.evidence}
        if len(evidence_ids) != len(self.evidence):
            raise ValueError("DUPLICATE_EVIDENCE")
        keys = [(item.provider, item.account_scope, item.model) for item in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("DUPLICATE_MODEL_SCOPE")
        for entry in self.entries:
            refs = (
                *entry.evidence_refs,
                *entry.terms_evidence_refs,
                *(item.evidence_ref for item in entry.quota_records),
                *(item.probe_evidence_ref for item in entry.structured_capabilities),
            )
            if not set(refs) <= evidence_ids:
                raise ValueError("UNKNOWN_MODEL_EVIDENCE")
        return self


class SyntheticProbeRequest(Contract):
    case: Literal["intent_schema", "compose_schema", "json_validation", "token_copy"]
    environment: Literal["development"] = "development"


class ProbeResult(Contract):
    checked_at: datetime
    capabilities: tuple[ModelCapability, ...]
    status: Literal["PASS", "FAIL", "NOT_RUN"]
    evidence_refs: tuple[Identifier, ...]
