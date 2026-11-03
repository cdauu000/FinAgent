from typing import Generic, Literal, TypeVar

from finagent.contracts.base import (
    Contract,
    DomainError,
    ExportText,
    Identifier,
    Mode,
    Tier,
    Verdict,
    Warning,
)
from finagent.store.models import AnalysisRecord

T = TypeVar("T")


class ResultEnvelope(Contract, Generic[T]):
    schema_version: Literal["api/1"] = "api/1"
    run_id: Identifier
    effective_mode: Mode
    effective_tier: Tier
    policy_version: str
    snapshot_refs: tuple[Identifier, ...]
    verdict: Verdict
    data: T
    warnings: tuple[Warning, ...] = ()
    missing: tuple[Identifier, ...] = ()
    trace_ref: Identifier


class Health(Contract):
    status: Literal["alive"] = "alive"
    version: str


class Readiness(Contract):
    status: Literal["not_ready"] = "not_ready"
    reasons: tuple[Literal["SCHEMA_DRAFT", "PERSISTENCE_NOT_IMPLEMENTED"], ...]


class TextExportContent(Contract):
    artifact_id: Identifier
    format: Literal["md", "json"]
    content: ExportText
    verifier_receipt_ref: Identifier


class ApiCatalog(Contract):
    error: DomainError | None = None
    health: Health | None = None
    readiness: Readiness | None = None
    result: ResultEnvelope[AnalysisRecord] | None = None
    text_export: TextExportContent | None = None
