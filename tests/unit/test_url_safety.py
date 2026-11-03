from collections.abc import Iterator

import pytest

from finagent.ingestion.errors import ProcessingError
from finagent.ingestion.url_fetch import CheckedUrl, SafeUrlFetcher, check_url


def public_dns(host: str, port: int) -> tuple[str, ...]:
    return ("93.184.216.34",)


@pytest.mark.parametrize(
    "url",
    [
        "file:///x",
        "http://localhost/x",
        "http://169.254.169.254/x",
        "http://127.0.0.1",
        "http://2130706433/",
        "http://0177.0.0.1/",
        "http://0x7f000001/",
        "https://user:pass@example.com/",
        "https://example.com:1234/",
        "http://[::1]/",
        "http://[::ffff:127.0.0.1]/",
        "http://[64:ff9b::7f00:1]/",
        "https://example.com/#fragment",
        "https://example.com\\@localhost/",
    ],
)
def test_unsafe_urls_rejected_before_transport(url) -> None:
    with pytest.raises(ProcessingError):
        check_url(url, lambda host, port: ("127.0.0.1",))


def test_all_dns_answers_must_be_public_and_are_pinned() -> None:
    with pytest.raises(ProcessingError, match="SSRF_ADDRESS_BLOCKED"):
        check_url("https://example.com", lambda h, p: ("93.184.216.34", "10.0.0.1"))
    target = check_url("https://example.com/report?q=a", public_dns)
    assert target.addresses == ("93.184.216.34",) and target.target == "/report?q=a"


class Response:
    def __init__(self, status=200, headers=None, body=b"report"):
        self.status, self.headers, self.body, self.closed = (
            status,
            headers or {"Content-Type": "text/plain"},
            body,
            False,
        )

    def header(self, name: str) -> str | None:
        return self.headers.get(name)

    def chunks(self, deadline: float) -> Iterator[bytes]:
        yield self.body

    def close(self) -> None:
        self.closed = True


class Transport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.targets: list[CheckedUrl] = []

    def get(self, target: CheckedUrl, deadline: float) -> Response:
        self.targets.append(target)
        return self.responses.pop(0)


def test_redirect_rechecks_dns_and_always_closes(processing_ctx) -> None:
    response = Response(302, {"Location": "http://127.0.0.1/secret"})
    transport = Transport(response)
    with pytest.raises(ProcessingError, match="SSRF_ADDRESS_BLOCKED"):
        SafeUrlFetcher(transport, public_dns).fetch("http://example.com", processing_ctx)
    assert response.closed and len(transport.targets) == 1


@pytest.mark.parametrize(
    "response,code",
    [
        (Response(302, {"Location": "http://example.com"}), "URL_TLS_DOWNGRADE"),
        (
            Response(headers={"Content-Type": "text/plain", "Content-Length": "999999999"}),
            "URL_BODY_LIMIT",
        ),
        (
            Response(headers={"Content-Type": "text/plain", "Content-Encoding": "gzip"}),
            "URL_CONTENT_ENCODING",
        ),
        (Response(headers={"Content-Type": "text/html"}), "URL_CONTENT_TYPE"),
    ],
)
def test_url_response_guards(response, code, processing_ctx) -> None:
    with pytest.raises(ProcessingError, match=code):
        SafeUrlFetcher(Transport(response), public_dns).fetch("https://example.com", processing_ctx)
    assert response.closed


def test_rebinding_cannot_change_connected_ip_and_tls_uses_original_name(monkeypatch) -> None:
    from finagent.ingestion.url_fetch import PinnedHTTPConnection, PinnedHTTPSConnection

    target = check_url("https://example.com/report", public_dns)
    raw = object()
    calls = []
    monkeypatch.setattr(
        "finagent.ingestion.url_fetch.dial_pinned",
        lambda ip, port, timeout: calls.append((ip, port)) or raw,
    )
    plain = PinnedHTTPConnection(target, 1)
    plain.connect()
    assert plain.sock is raw

    class Context:
        def wrap_socket(self, sock, server_hostname):
            assert sock is raw and server_hostname == "example.com"
            return raw

    monkeypatch.setattr("finagent.ingestion.url_fetch.ssl.create_default_context", Context)
    tls = PinnedHTTPSConnection(target, 1)
    tls.connect()
    assert tls.sock is raw and calls == [("93.184.216.34", 443)] * 2


def test_url_idempotency_binds_url_before_fetch(tmp_path, processing_ctx) -> None:
    from finagent.ingestion.contracts import FileInput
    from finagent.ingestion.service import LocalIngestionGateway
    from finagent.jobs.memory import MemoryJobStore
    from finagent.store.local_blob import LocalBlobStore
    from tests.unit.test_ingestion_memory import Inspector

    response = Response()
    transport = Transport(response)
    gateway = LocalIngestionGateway(LocalBlobStore(tmp_path), MemoryJobStore(), Inspector())
    request = FileInput(filename="report.txt", declared_mime="text/plain", idempotency_key="url-a")
    fetcher = SafeUrlFetcher(transport, public_dns)
    first = gateway.submit_url("https://example.com/a", request, processing_ctx, fetcher)
    assert gateway.submit_url("https://example.com/a", request, processing_ctx, fetcher) == first
    with pytest.raises(ProcessingError, match="IDEMPOTENCY_BODY_CONFLICT"):
        gateway.submit_url("https://example.com/b", request, processing_ctx, fetcher)
    assert len(transport.targets) == 1


def test_dns_deadline_is_enforced_without_transport(processing_ctx, monkeypatch) -> None:
    import threading
    import time

    from finagent.ingestion.url_fetch import resolve_before_deadline

    finished = threading.Event()

    def blocked(host, port):
        finished.wait(2)
        return ("93.184.216.34",)

    try:
        with pytest.raises(ProcessingError, match="URL_DNS_TIMEOUT"):
            resolve_before_deadline(blocked, "example.com", 443, time.monotonic() + 0.01)
    finally:
        finished.set()
