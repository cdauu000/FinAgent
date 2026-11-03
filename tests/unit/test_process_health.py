import asyncio
import socket

import httpx
import pytest

from finagent.api.app import create_app


def test_liveness_does_not_claim_frozen_contracts_mean_backend_is_ready(
    process_loop: asyncio.AbstractEventLoop,
) -> None:
    async def exercise_asgi() -> None:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            assert (await client.get("/health")).status_code == 200
            response = await client.get("/health/ready")
            assert response.status_code == 503
            assert response.json()["reasons"] == ["PERSISTENCE_NOT_IMPLEMENTED"]
            assert (await client.get("/docs")).status_code == 404

    process_loop.run_until_complete(exercise_asgi())


def test_offline_guard_still_blocks_real_connections() -> None:
    with pytest.raises(AssertionError, match="Outbound network forbidden"):
        socket.create_connection(("203.0.113.1", 443))
