from concurrent.futures import ThreadPoolExecutor

import pytest

from finagent.ingestion.errors import ProcessingError
from finagent.jobs.memory import MemoryJobStore


def test_checkpoint_lease_retry_cancel_and_tenant(processing_ctx, monkeypatch) -> None:
    clock = [10.0]
    monkeypatch.setattr("finagent.jobs.memory.time.monotonic", lambda: clock[0])
    store = MemoryJobStore(max_attempts=2)
    job = store.enqueue("doc-a", processing_ctx)
    running = store.claim(job.job_id, processing_ctx, lease_seconds=5)
    token = running.lease_token
    store.checkpoint(job.job_id, token, "S1", "checkpoint-a", processing_ctx)
    with pytest.raises(ProcessingError, match="RESOURCE_NOT_FOUND"):
        store.get(job.job_id, processing_ctx.model_copy(update={"tenant_id": "tenant-b"}))
    clock[0] = 16
    with pytest.raises(ProcessingError, match="STALE_JOB_LEASE"):
        store.checkpoint(job.job_id, token, "S2", "checkpoint-b", processing_ctx)
    next_run = store.claim(job.job_id, processing_ctx)
    assert next_run.checkpoint_ref == "checkpoint-a" and next_run.lease_token != token
    completed = store.finish(job.job_id, next_run.lease_token, "COMPLETED", processing_ctx)
    assert completed.state == "COMPLETED" and store.events(job.job_id, 0, processing_ctx)
    with pytest.raises(ProcessingError, match="JOB_NOT_CLAIMABLE"):
        store.claim(job.job_id, processing_ctx)
    assert not MemoryJobStore()._jobs


def test_only_one_worker_can_claim_and_cancellation_invalidates_lease(processing_ctx) -> None:
    store = MemoryJobStore()
    job = store.enqueue("doc-a", processing_ctx)

    def claim():
        try:
            return store.claim(job.job_id, processing_ctx)
        except ProcessingError:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: claim(), range(8)))
    valid = [r for r in results if r is not None]
    assert len(valid) == 1
    store.cancel(job.job_id, processing_ctx)
    with pytest.raises(ProcessingError, match="STALE_JOB_LEASE"):
        store.finish(job.job_id, valid[0].lease_token, "COMPLETED", processing_ctx)


def test_invalid_checkpoint_does_not_mutate_job(processing_ctx) -> None:
    store = MemoryJobStore()
    job = store.enqueue("doc-a", processing_ctx)
    running = store.claim(job.job_id, processing_ctx)
    with pytest.raises(ProcessingError, match="INVALID_CHECKPOINT_REFERENCE"):
        store.checkpoint(job.job_id, running.lease_token, "S1", "../../secret", processing_ctx)
    assert store.get(job.job_id, processing_ctx) == running
