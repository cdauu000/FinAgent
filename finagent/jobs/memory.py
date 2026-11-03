"""Single-process job queue with leases/checkpoints; restart loses all state."""

import threading
import time
from typing import Literal
from uuid import uuid4

from pydantic import Field, ValidationError

from finagent.contracts.base import Contract, ExecutionContext, Identifier, SafeInt, Tier
from finagent.ingestion.errors import ProcessingError
from finagent.security.permissions import authorize

JobState = Literal[
    "QUEUED", "RUNNING", "WAITING_REVIEW", "COMPLETED", "PARTIAL", "FAILED", "CANCELLED"
]


class JobEvent(Contract):
    seq: SafeInt = Field(ge=0)
    state: JobState
    stage: Identifier


class JobRecord(Contract):
    job_id: Identifier
    document_id: Identifier
    tenant_id: Identifier
    source_tier: Tier
    state: JobState = "QUEUED"
    stage: Identifier = "S0"
    checkpoint_ref: Identifier | None = None
    lease_token: Identifier | None = None
    lease_deadline: float | None = None
    attempts: SafeInt = Field(default=0, ge=0)
    events: tuple[JobEvent, ...] = ()


class MemoryJobStore:
    def __init__(self, *, max_attempts: int = 3) -> None:
        if max_attempts < 1:
            raise ProcessingError("INVALID_RETRY_BUDGET")
        self.max_attempts = max_attempts
        self._jobs: dict[str, JobRecord] = {}
        self._lock = threading.RLock()

    def enqueue(self, document_id: str, ctx: ExecutionContext) -> JobRecord:
        authorize(ctx, "document:write")
        with self._lock:
            job = JobRecord(
                job_id="job-" + uuid4().hex,
                document_id=document_id,
                tenant_id=ctx.tenant_id,
                source_tier=ctx.source_tier,
                events=(JobEvent(seq=0, state="QUEUED", stage="S0"),),
            )
            self._jobs[job.job_id] = job
            return job

    def get(self, job_id: str, ctx: ExecutionContext) -> JobRecord:
        authorize(ctx, "job:read")
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.tenant_id != ctx.tenant_id:
                raise ProcessingError("RESOURCE_NOT_FOUND")
            return job

    def _owned(self, job_id: str, lease_token: str, ctx: ExecutionContext) -> JobRecord:
        authorize(ctx, "job:work")
        job = self.get(job_id, ctx)
        if (
            job.state != "RUNNING"
            or job.lease_token != lease_token
            or job.lease_deadline is None
            or job.lease_deadline <= time.monotonic()
        ):
            raise ProcessingError("STALE_JOB_LEASE")
        return job

    def claim(self, job_id: str, ctx: ExecutionContext, *, lease_seconds: float = 60) -> JobRecord:
        authorize(ctx, "job:work")
        if not 0 < lease_seconds <= 3600:
            raise ProcessingError("INVALID_LEASE")
        with self._lock:
            job = self.get(job_id, ctx)
            expired = job.state == "RUNNING" and (job.lease_deadline or 0) <= time.monotonic()
            if job.state != "QUEUED" and not expired:
                raise ProcessingError("JOB_NOT_CLAIMABLE")
            if job.attempts >= self.max_attempts:
                raise ProcessingError("JOB_RETRY_BUDGET_EXHAUSTED")
            claimed = job.model_copy(
                update={
                    "state": "RUNNING",
                    "lease_token": "lease-" + uuid4().hex,
                    "lease_deadline": time.monotonic() + lease_seconds,
                    "attempts": job.attempts + 1,
                    "events": (
                        *job.events,
                        JobEvent(seq=len(job.events), state="RUNNING", stage=job.stage),
                    ),
                }
            )
            self._jobs[job_id] = claimed
            return claimed

    def checkpoint(
        self, job_id: str, lease_token: str, stage: str, checkpoint_ref: str, ctx: ExecutionContext
    ) -> JobRecord:
        if stage not in {f"S{i}" for i in range(11)}:
            raise ProcessingError("UNKNOWN_JOB_STAGE")
        with self._lock:
            job = self._owned(job_id, lease_token, ctx)
            try:
                updated = JobRecord.model_validate(
                    {
                        **job.model_dump(),
                        "stage": stage,
                        "checkpoint_ref": checkpoint_ref,
                        "events": (
                            *job.events,
                            JobEvent(seq=len(job.events), state="RUNNING", stage=stage),
                        ),
                    }
                )
            except ValidationError as exc:
                raise ProcessingError("INVALID_CHECKPOINT_REFERENCE") from exc
            self._jobs[job_id] = updated
            return updated

    def heartbeat(
        self, job_id: str, lease_token: str, ctx: ExecutionContext, *, lease_seconds: float = 60
    ) -> JobRecord:
        if not 0 < lease_seconds <= 3600:
            raise ProcessingError("INVALID_LEASE")
        with self._lock:
            job = self._owned(job_id, lease_token, ctx)
            updated = job.model_copy(update={"lease_deadline": time.monotonic() + lease_seconds})
            self._jobs[job_id] = updated
            return updated

    def finish(
        self,
        job_id: str,
        lease_token: str,
        state: Literal["COMPLETED", "PARTIAL", "FAILED", "WAITING_REVIEW"],
        ctx: ExecutionContext,
    ) -> JobRecord:
        if state not in {"COMPLETED", "PARTIAL", "FAILED", "WAITING_REVIEW"}:
            raise ProcessingError("INVALID_JOB_TRANSITION")
        with self._lock:
            job = self._owned(job_id, lease_token, ctx)
            updated = job.model_copy(
                update={
                    "state": state,
                    "lease_token": None,
                    "lease_deadline": None,
                    "events": (
                        *job.events,
                        JobEvent(seq=len(job.events), state=state, stage=job.stage),
                    ),
                }
            )
            self._jobs[job_id] = updated
            return updated

    def retry(self, job_id: str, ctx: ExecutionContext) -> JobRecord:
        authorize(ctx, "job:work")
        with self._lock:
            job = self.get(job_id, ctx)
            if job.state not in {"FAILED", "WAITING_REVIEW"} or job.attempts >= self.max_attempts:
                raise ProcessingError("JOB_NOT_RETRYABLE")
            updated = job.model_copy(
                update={
                    "state": "QUEUED",
                    "lease_token": None,
                    "lease_deadline": None,
                    "events": (
                        *job.events,
                        JobEvent(seq=len(job.events), state="QUEUED", stage=job.stage),
                    ),
                }
            )
            self._jobs[job_id] = updated
            return updated

    def cancel(self, job_id: str, ctx: ExecutionContext) -> JobRecord:
        authorize(ctx, "job:cancel")
        with self._lock:
            job = self.get(job_id, ctx)
            if job.state in {"COMPLETED", "PARTIAL", "CANCELLED"}:
                raise ProcessingError("INVALID_JOB_TRANSITION")
            updated = job.model_copy(
                update={
                    "state": "CANCELLED",
                    "lease_token": None,
                    "lease_deadline": None,
                    "events": (
                        *job.events,
                        JobEvent(seq=len(job.events), state="CANCELLED", stage=job.stage),
                    ),
                }
            )
            self._jobs[job_id] = updated
            return updated

    def events(self, job_id: str, after_seq: int, ctx: ExecutionContext) -> tuple[JobEvent, ...]:
        if after_seq < -1:
            raise ProcessingError("INVALID_EVENT_CURSOR")
        return tuple(event for event in self.get(job_id, ctx).events if event.seq > after_seq)
