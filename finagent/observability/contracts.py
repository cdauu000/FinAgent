from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from finagent.contracts.base import Contract, Identifier, Mode, SafeInt, Tier


class ProgressPayload(Contract):
    kind: Literal["progress"] = "progress"
    stage: Identifier
    status: Literal["queued", "running", "waiting_review", "completed", "failed"]
    message_key: Identifier


class VerifiedResultRef(Contract):
    kind: Literal["result_ref"] = "result_ref"
    result_ref: Identifier
    verifier_receipt_ref: Identifier


class EventEnvelope(Contract):
    schema_version: Literal["event/1"] = "event/1"
    event_id: Identifier
    seq: SafeInt = Field(ge=0)
    time_utc: datetime
    tenant_id: Identifier
    resource_id: Identifier
    run_id: Identifier | None = None
    trace_id: Identifier
    parent_trace_id: Identifier | None = None
    mode: Mode
    source_tier: Tier
    policy_version: str
    payload: Annotated[ProgressPayload | VerifiedResultRef, Field(discriminator="kind")]
