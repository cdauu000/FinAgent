from typing import Literal, Protocol

from finagent.contracts.base import Contract, Identifier


class LocalModelRequest(Contract):
    task: Literal["ocr", "vlm", "embedding", "rerank", "classify"]
    artifact_refs: tuple[Identifier, ...]
    tenant_id: Identifier
    model_ref: Identifier


class LocalModelResult(Contract):
    task: Literal["ocr", "vlm", "embedding", "rerank", "classify"]
    artifact_refs: tuple[Identifier, ...]
    model_ref: Identifier
    status: Literal["available", "unavailable"]


class LocalModelPort(Protocol):
    def infer(self, request: LocalModelRequest) -> LocalModelResult: ...
