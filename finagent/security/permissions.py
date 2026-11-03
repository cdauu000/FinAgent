from datetime import UTC, datetime

from finagent.contracts.base import ExecutionContext, Tier
from finagent.contracts.errors import ProcessingError

TIER_ORDER = {Tier.PUBLIC: 0, Tier.PRIVATE: 1, Tier.STRICT_PRIVATE: 2}


def authorize(ctx: ExecutionContext, permission: str, tenant_id: str | None = None) -> None:
    if ctx.deadline.tzinfo is None or ctx.deadline <= datetime.now(UTC):
        raise ProcessingError("DEADLINE_EXCEEDED")
    if permission not in ctx.permissions:
        raise ProcessingError("PERMISSION_DENIED")
    if tenant_id is not None and tenant_id != ctx.tenant_id:
        raise ProcessingError("RESOURCE_NOT_FOUND")


def require_tier(ctx: ExecutionContext, tier: Tier) -> None:
    if TIER_ORDER[tier] < TIER_ORDER[ctx.source_tier]:
        raise ProcessingError("TIER_DOWNGRADE_FORBIDDEN")
