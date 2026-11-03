"""Contracts only: runtime implementations and Redis reservations are Phase 5."""

from datetime import datetime
from typing import Protocol

from finagent.contracts.base import Identifier
from finagent.llm_gateway.contracts import (
    GatewayError,
    GatewayOutcome,
    GatewayRequest,
    ProviderRequest,
    ProviderResult,
)
from finagent.llm_gateway.model_registry import (
    ModelCapability,
    ProbeResult,
    QuotaBucketKey,
    QuotaDenied,
    QuotaReservation,
    SyntheticProbeRequest,
)


class ProviderAdapter(Protocol):
    async def call(self, request: ProviderRequest) -> ProviderResult: ...

    def capabilities(self) -> tuple[ModelCapability, ...]: ...

    def normalize_error(self, raw: object) -> GatewayError: ...

    async def probe(self, request: SyntheticProbeRequest) -> ProbeResult: ...


class LlmGateway(Protocol):
    async def parse_intent(self, request: GatewayRequest) -> GatewayOutcome: ...

    async def compose_answer(self, request: GatewayRequest) -> GatewayOutcome: ...


class QuotaStore(Protocol):
    async def reserve(
        self,
        bucket: QuotaBucketKey,
        tenant_id: Identifier,
        estimated_tokens: int,
        reservation_id: Identifier,
        deadline: datetime,
    ) -> QuotaReservation | QuotaDenied: ...

    async def reconcile(self, reservation_id: Identifier, actual_tokens: int) -> None: ...

    async def release(self, reservation_id: Identifier) -> None: ...
