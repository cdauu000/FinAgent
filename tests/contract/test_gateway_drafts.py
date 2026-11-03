import json

import pytest
from pydantic import TypeAdapter, ValidationError

from finagent.llm_gateway.contracts import (
    AnswerDraft,
    ClaimDescriptor,
    FinalAnswerPayload,
    IntentPayload,
    IntentPlan,
    ProviderRequest,
    ReferenceManifest,
)
from finagent.llm_gateway.model_registry import (
    ModelCapability,
    QuotaBucketKey,
    QuotaRecord,
    Retention,
)


def descriptor() -> dict[str, object]:
    return {
        "claim_id": "claim-a",
        "concept_label": "ratios.current",
        "status": "NORMAL",
        "period_code": "q1_2026",
        "scope": "separate",
    }


@pytest.mark.parametrize(
    "key", ["value", "amount", "ratio", "unit", "inputs", "citation", "raw_table"]
)
def test_compose_schema_rejects_value_and_document_channels(key: str) -> None:
    with pytest.raises(ValidationError):
        ClaimDescriptor.model_validate({**descriptor(), key: "SECRET_9384756"})
    payload = FinalAnswerPayload.model_validate({"claims": [descriptor()], "status": "ANSWER"})
    assert "SECRET_9384756" not in payload.model_dump_json()
    assert set(json.loads(payload.model_dump_json())["claims"][0]) == {
        "claim_id",
        "concept_label",
        "status",
        "band",
        "qualitative_relations",
        "warning_codes",
        "period_code",
        "scope",
    }


@pytest.mark.parametrize("text", ["Có 12", "Có １２", "Có ²", "Có Ⅳ"])
def test_draft_schema_rejects_numeric_prose(text: str) -> None:
    with pytest.raises(ValidationError, match="FORBIDDEN_PROSE_NUMBER"):
        AnswerDraft.model_validate({"segments": [{"type": "prose", "text": text}]})


@pytest.mark.parametrize("reason", ["ENTITY", "PERIOD", "SCOPE", "RATIO", "AMBIGUOUS_REQUEST"])
def test_clarification_is_enum_not_model_wording(reason: str) -> None:
    assert IntentPlan.model_validate({"clarification": reason}).clarification == reason
    with pytest.raises(ValidationError):
        IntentPlan.model_validate({"clarification": "Bạn muốn kỳ nào?"})


def test_user_claim_accepts_only_placeholder_and_history_is_empty() -> None:
    action = {
        "action": "verify_user_claim",
        "placeholder_ref": "num_" + "a" * 8,
        "claim_kind": "revenue",
    }
    assert IntentPlan.model_validate({"actions": [action]}).actions[0].action == "verify_user_claim"
    with pytest.raises(ValidationError):
        IntentPlan.model_validate({"actions": [{**action, "value": "9384756"}]})
    payload = {"query": "Doanh thu", "selection": {"selection_revision": 1}}
    assert IntentPayload.model_validate(payload).history == ()
    with pytest.raises(ValidationError):
        IntentPayload.model_validate({**payload, "history": ["old answer 9384756"]})


def test_side_effect_tools_cannot_be_intent_actions() -> None:
    for action in ["request_review", "export_result", "resolve_review"]:
        with pytest.raises(ValidationError):
            IntentPlan.model_validate({"actions": [{"action": action}]})


def test_provider_cannot_stream_hedge_or_accept_wrong_task_schema() -> None:
    body = {
        "provider": "synthetic",
        "model": "synthetic",
        "task": "intent_parse",
        "messages": [
            {"content": "Static prompt", "prompt_hash": "a" * 64},
            {
                "payload": {
                    "task": "intent_parse",
                    "query": "Doanh thu",
                    "selection": {"selection_revision": 1},
                }
            },
        ],
        "prompt_ref": {"id": "intent", "version": "1"},
        "output_schema_ref": "IntentPlan",
        "structured_strategy": "native_schema",
        "timeout_seconds": 1,
        "permit_id": "permit-a",
    }
    assert ProviderRequest.model_validate(body).stream is False
    for key in ["stream", "hedging"]:
        with pytest.raises(ValidationError):
            ProviderRequest.model_validate({**body, key: True})
    with pytest.raises(ValidationError, match="TASK_SCHEMA_MISMATCH"):
        ProviderRequest.model_validate({**body, "output_schema_ref": "AnswerDraft"})


def test_retention_unknown_and_training_unknown_are_defaults_without_fake_verification() -> None:
    model = ModelCapability(provider="synthetic", model="synthetic", account_scope="account-a")
    assert model.training_use == "unknown"
    assert model.retention.kind == "unknown"
    with pytest.raises(ValidationError):
        ModelCapability(
            provider="synthetic", model="synthetic", account_scope="account-a", status="verified"
        )
    with pytest.raises(ValidationError):
        TypeAdapter(Retention).validate_python({"kind": "limited", "days": -1})
    with pytest.raises(ValidationError):
        TypeAdapter(Retention).validate_python({"kind": "unknown", "days": 30})
    assert TypeAdapter(Retention).validate_python({"kind": "limited", "days": 30}).kind == "limited"


def test_quota_is_scoped_to_account_and_has_mandatory_provenance() -> None:
    assert QuotaBucketKey(provider="synthetic", account_scope="account-a", model="synthetic")
    with pytest.raises(ValidationError):
        QuotaBucketKey.model_validate(
            {"provider": "synthetic", "model": "synthetic", "key": "secret"}
        )
    with pytest.raises(ValidationError):
        QuotaRecord.model_validate({"dimension": "rpm", "limit": 1})


def test_reference_manifest_requires_known_required_claims() -> None:
    with pytest.raises(ValidationError, match="UNKNOWN_REQUIRED_CLAIM"):
        ReferenceManifest.model_validate(
            {
                "claim_ids": [],
                "required_claim_ids": ["unknown"],
                "warning_codes": [],
                "required_warning_codes": [],
                "entity_tokens": [],
                "required_slots": [],
                "version": "draft",
            }
        )


def test_compute_intent_cannot_silently_choose_missing_scope_entity_or_period() -> None:
    with pytest.raises(ValidationError, match="EXPLICIT_SELECTION_REQUIRED"):
        IntentPlan.model_validate({"actions": [{"action": "compute_ratios"}]})
    action = {
        "action": "compute_ratios",
        "entity_token": "ent_" + "a" * 8,
        "scope": "separate",
        "period_codes": ["q1_2026"],
    }
    assert IntentPlan.model_validate({"actions": [action]}).actions[0].action == "compute_ratios"
    with pytest.raises(ValidationError):
        IntentPlan.model_validate({"actions": [action], "clarification": "PERIOD"})
