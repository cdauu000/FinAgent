"""Prompt/1 schema; no provider prompt is shipped or activated in Phase 0."""

from typing import Literal, Self

from pydantic import Field, model_validator

from finagent.contracts.base import Contract, Identifier, NonEmpty, Sha256, Version
from finagent.llm_gateway.contracts import GatewayTask


class PromptDefinition(Contract):
    id: Identifier
    version: Version
    task: GatewayTask
    language: Literal["vi", "en"]
    status: Literal["draft", "approved", "deprecated"] = "draft"
    template: NonEmpty
    template_sha256: Sha256
    input_schema_ref: Literal["IntentPayload", "FinalAnswerPayload"]
    output_schema_ref: Literal["IntentPlan", "AnswerDraft"]
    mandatory_test_refs: tuple[Identifier, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def task_contract_matches(self) -> Self:
        if self.task == GatewayTask.INTENT:
            expected = ("IntentPayload", "IntentPlan")
        else:
            expected = ("FinalAnswerPayload", "AnswerDraft")
        if (self.input_schema_ref, self.output_schema_ref) != expected:
            raise ValueError("PROMPT_TASK_SCHEMA_MISMATCH")
        from hashlib import sha256

        if sha256(self.template.encode("utf-8")).hexdigest() != self.template_sha256:
            raise ValueError("PROMPT_HASH_MISMATCH")
        return self


class PromptRegistry(Contract):
    schema_version: Literal["prompt/1"] = "prompt/1"
    status: Literal["draft", "approved"] = "draft"
    entries: tuple[PromptDefinition, ...] = ()

    @model_validator(mode="after")
    def unique_versions(self) -> Self:
        keys = [(item.id, item.version, item.language) for item in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("DUPLICATE_PROMPT_VERSION")
        return self
