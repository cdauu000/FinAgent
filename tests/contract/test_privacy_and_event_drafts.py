import pytest
from pydantic import ValidationError

from finagent.llm_gateway.contracts import EgressPermit
from finagent.llm_gateway.model_registry import ModelCapability, ModelRegistry
from finagent.observability.contracts import EventEnvelope


def test_permit_schema_rejects_strict_private_and_missing_private_opt_in() -> None:
    permit = {
        "id": "permit-a",
        "task": "answer_compose",
        "environment": "runtime",
        "tenant_id": "tenant-a",
        "source_tier": "strict_private",
        "tenant_opt_in": True,
        "provider": "synthetic",
        "model": "synthetic",
        "payload_hash": "a" * 64,
        "policy_ref": {"id": "policy", "version": "1"},
        "expires_at": "2026-11-02T00:00:00Z",
        "max_tokens": 1,
    }
    with pytest.raises(ValidationError, match="STRICT_PRIVATE_EXTERNAL_FORBIDDEN"):
        EgressPermit.model_validate(permit)
    with pytest.raises(ValidationError, match="PRIVATE_OPT_IN_REQUIRED"):
        EgressPermit.model_validate({**permit, "source_tier": "private", "tenant_opt_in": False})


def test_model_cannot_claim_no_training_or_retention_without_terms_evidence() -> None:
    data = {"provider": "synthetic", "model": "synthetic", "account_scope": "account-a"}
    with pytest.raises(ValidationError, match="TERMS_EVIDENCE_REQUIRED"):
        ModelCapability.model_validate({**data, "training_use": "none_verified"})
    with pytest.raises(ValidationError, match="TERMS_EVIDENCE_REQUIRED"):
        ModelCapability.model_validate({**data, "retention": {"kind": "limited", "days": 1}})
    with pytest.raises(ValidationError):
        ModelCapability.model_validate({**data, "data_use": "none"})
    assert ModelRegistry().entries == ()


def test_event_schema_carries_progress_or_verified_ref_never_answer_text() -> None:
    event = {
        "event_id": "event-a",
        "seq": 1,
        "time_utc": "2026-11-02T00:00:00Z",
        "tenant_id": "tenant-a",
        "resource_id": "run-a",
        "trace_id": "trace-a",
        "mode": "strict",
        "source_tier": "private",
        "policy_version": "1",
    }
    progress = {
        "kind": "progress",
        "stage": "validation",
        "status": "running",
        "message_key": "job.validation.running",
    }
    assert EventEnvelope.model_validate({**event, "payload": progress})
    with pytest.raises(ValidationError):
        EventEnvelope.model_validate({**event, "payload": {**progress, "answer": "CANARY 9384756"}})
    with pytest.raises(ValidationError):
        EventEnvelope.model_validate(
            {**event, "payload": {"kind": "result_ref", "result_ref": "result-a"}}
        )
    assert EventEnvelope.model_validate(
        {
            **event,
            "payload": {
                "kind": "result_ref",
                "result_ref": "result-a",
                "verifier_receipt_ref": "receipt-a",
            },
        }
    )
