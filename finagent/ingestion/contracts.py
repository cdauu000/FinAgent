from typing import Literal, Protocol

from pydantic import Field

from finagent.contracts.base import Contract, ExecutionContext, Identifier, SafeInt, Sha256, Tier


class FileInput(Contract):
    filename: str
    declared_mime: str
    requested_tier: Tier | None = None
    public_evidence_refs: tuple[Identifier, ...] = ()
    pipeline_version: Identifier = "ingestion-1a"
    idempotency_key: Identifier


class IngestionReceipt(Contract):
    document_id: Identifier
    blob_ref: Identifier
    job_id: Identifier
    sha256: Sha256
    mime_type: str
    page_count: SafeInt | None = None
    effective_tier: Tier
    dedup_hit: bool
    warnings: tuple[Identifier, ...] = ()


class FileInspection(Contract):
    mime_type: str
    size: SafeInt = Field(gt=0)
    page_count: SafeInt | None = None
    scanner_status: Literal["CLEAN", "REJECTED", "UNAVAILABLE"]
    warnings: tuple[Identifier, ...] = ()


class PdfInspection(Contract):
    page_count: SafeInt = Field(gt=0)
    password_protected: bool = False


class PdfInspector(Protocol):
    def inspect_pdf(self, content: bytes) -> PdfInspection: ...


class FileScanner(Protocol):
    def scan(self, content: bytes) -> Literal["CLEAN", "REJECTED", "UNAVAILABLE"]: ...


class IngestionGateway(Protocol):
    def submit(
        self, content: bytes, request: FileInput, ctx: ExecutionContext
    ) -> IngestionReceipt: ...
