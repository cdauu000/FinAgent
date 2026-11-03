"""Offline by default: a hidden HTTP call must fail, rather than silently reach a provider."""

import asyncio
import socket
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest

from finagent.contracts.base import ExecutionContext, Mode, RegistryRef, Tier


@pytest.fixture
def processing_ctx() -> ExecutionContext:
    return ExecutionContext(
        tenant_id="tenant-a",
        principal_id="unit-user",
        permissions=(
            "document:write",
            "document:read",
            "document:delete",
            "review:read",
            "job:read",
            "job:work",
            "job:cancel",
            "url:fetch",
        ),
        request_id="request-a",
        trace_id="trace-a",
        policy_ref=RegistryRef(id="unit-policy", version="1"),
        mode=Mode.STRICT,
        source_tier=Tier.PRIVATE,
        deadline=datetime.now(UTC) + timedelta(hours=1),
    )


@pytest.fixture(autouse=True)
def deny_outbound(monkeypatch: pytest.MonkeyPatch, process_loop: asyncio.AbstractEventLoop) -> None:
    def denied(*args: object, **kwargs: object) -> None:
        raise AssertionError("Outbound network forbidden during offline tests")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


@pytest.fixture(scope="session")
def process_loop() -> Iterator[asyncio.AbstractEventLoop]:
    # Windows creates its own loopback socketpair for the event-loop wakeup pipe.
    # Create only that IPC pair before the guard; all test connections stay denied.
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
