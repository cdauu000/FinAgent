import hashlib
import io
import json
import threading
from dataclasses import dataclass, field
from uuid import uuid4

from finagent.contracts.base import ExecutionContext, Tier
from finagent.ingestion.contracts import FileInput, FileScanner, IngestionReceipt, PdfInspector
from finagent.ingestion.errors import ProcessingError
from finagent.ingestion.file_safety import inspect_file
from finagent.ingestion.url_fetch import SafeUrlFetcher
from finagent.jobs.memory import MemoryJobStore
from finagent.security.permissions import authorize, require_tier
from finagent.store.models import BlobMetadata
from finagent.store.ports import BlobStore


def require_same_request(previous: str, current: str) -> None:
    if previous != current:
        raise ProcessingError("IDEMPOTENCY_BODY_CONFLICT")


@dataclass
class IngestionJournal:
    """Inject/share across memory workers. Restart loss is explicit; not a DB journal."""

    requests: dict[tuple[str, str], tuple[str, IngestionReceipt]] = field(default_factory=dict)
    documents: dict[tuple[str, str, str, Tier], IngestionReceipt] = field(default_factory=dict)
    urls: dict[tuple[str, str], tuple[str, IngestionReceipt]] = field(default_factory=dict)
    lock: threading.RLock = field(default_factory=threading.RLock)


class LocalIngestionGateway:
    def __init__(
        self,
        blobs: BlobStore,
        jobs: MemoryJobStore,
        inspector: PdfInspector,
        *,
        journal: IngestionJournal | None = None,
        scanner: FileScanner | None = None,
        scanner_required: bool = False,
    ) -> None:
        self.blobs, self.jobs, self.inspector = blobs, jobs, inspector
        self.journal = journal or IngestionJournal()
        self.scanner, self.scanner_required = scanner, scanner_required

    def submit(self, content: bytes, request: FileInput, ctx: ExecutionContext) -> IngestionReceipt:
        authorize(ctx, "document:write")
        tier = request.requested_tier or ctx.source_tier
        require_tier(ctx, tier)
        if tier == Tier.PUBLIC and not request.public_evidence_refs:
            raise ProcessingError("PUBLIC_EVIDENCE_REQUIRED")
        digest = hashlib.sha256(content).hexdigest()
        fingerprint = hashlib.sha256(
            json.dumps(
                {"sha256": digest, "request": request.model_dump(mode="json"), "tier": tier},
                sort_keys=True,
            ).encode()
        ).hexdigest()
        key = (ctx.tenant_id, request.idempotency_key)
        dedup_key = (ctx.tenant_id, digest, request.pipeline_version, tier)
        with self.journal.lock:
            previous = self.journal.requests.get(key)
            if previous:
                require_same_request(previous[0], fingerprint)
                return previous[1]
            inspection = inspect_file(
                content,
                request,
                self.inspector,
                self.scanner,
                scanner_required=self.scanner_required,
            )
            if dedup_key in self.journal.documents:
                result = self.journal.documents[dedup_key].model_copy(update={"dedup_hit": True})
            else:
                effective_ctx = ctx.model_copy(update={"source_tier": tier})
                blob_ref = self.blobs.put(
                    io.BytesIO(content),
                    BlobMetadata(
                        tenant_id=ctx.tenant_id,
                        source_tier=tier,
                        sha256=digest,
                        mime_type=inspection.mime_type,
                    ),
                    effective_ctx,
                )
                document_id = "doc-" + uuid4().hex
                job = self.jobs.enqueue(document_id, effective_ctx)
                result = IngestionReceipt(
                    document_id=document_id,
                    blob_ref=blob_ref,
                    job_id=job.job_id,
                    sha256=digest,
                    mime_type=inspection.mime_type,
                    page_count=inspection.page_count,
                    effective_tier=tier,
                    dedup_hit=False,
                    warnings=inspection.warnings,
                )
                self.journal.documents[dedup_key] = result
            self.journal.requests[key] = (fingerprint, result)
            return result

    def submit_url(
        self,
        url: str,
        request: FileInput,
        ctx: ExecutionContext,
        fetcher: SafeUrlFetcher | None = None,
    ) -> IngestionReceipt:
        authorize(ctx, "document:write")
        authorize(ctx, "url:fetch")
        fingerprint = hashlib.sha256(
            (url + "\0" + request.model_dump_json() + "\0" + ctx.source_tier).encode()
        ).hexdigest()
        key = (ctx.tenant_id, request.idempotency_key)
        with self.journal.lock:
            previous = self.journal.urls.get(key)
            if previous:
                require_same_request(previous[0], fingerprint)
                return previous[1]
            fetched = (fetcher or SafeUrlFetcher()).fetch(url, ctx)
            if fetched.mime_type != request.declared_mime:
                raise ProcessingError("MIME_MISMATCH")
            endpoint_key = (
                "url-store-" + hashlib.sha256((ctx.tenant_id + fingerprint).encode()).hexdigest()
            )
            result = self.submit(
                fetched.content, request.model_copy(update={"idempotency_key": endpoint_key}), ctx
            )
            self.journal.urls[key] = (fingerprint, result)
            return result
