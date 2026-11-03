"""SSRF-safe explicit HTTP adapter; no proxies, cookies, credentials or provider SDKs."""

import http.client
import ipaddress
import queue
import socket
import ssl
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from urllib.parse import urljoin, urlsplit, urlunsplit

from finagent.contracts.base import ExecutionContext
from finagent.ingestion.errors import ProcessingError
from finagent.security.permissions import authorize

MAX_URL_BYTES = 20 * 1024 * 1024
MAX_REDIRECTS = 3
FETCH_TIMEOUT = 15.0
_DNS_SLOTS = threading.BoundedSemaphore(
    8
)  # TODO(verify): A64 resource bound, not throughput target.


@dataclass(frozen=True)
class CheckedUrl:
    url: str
    scheme: str
    host: str
    port: int
    target: str
    addresses: tuple[str, ...]


def resolve_addresses(host: str, port: int) -> tuple[str, ...]:
    return tuple(
        sorted({str(row[4][0]) for row in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)})
    )


def resolve_before_deadline(
    resolver: Callable[[str, int], tuple[str, ...]], host: str, port: int, deadline: float
) -> tuple[str, ...]:
    remaining = deadline - time.monotonic()
    if remaining <= 0 or not _DNS_SLOTS.acquire(timeout=max(0, remaining)):
        raise ProcessingError("URL_DNS_TIMEOUT")
    outcome: queue.Queue[tuple[str, ...] | None] = queue.Queue(maxsize=1)

    def worker() -> None:
        try:
            outcome.put(resolver(host, port))
        except OSError:
            outcome.put(None)
        finally:
            _DNS_SLOTS.release()

    threading.Thread(target=worker, daemon=True, name="finagent-url-dns").start()
    try:
        addresses = outcome.get(timeout=max(0, deadline - time.monotonic()))
    except queue.Empty:
        raise ProcessingError("URL_DNS_TIMEOUT") from None
    if addresses is None:
        raise ProcessingError("URL_DNS_FAILED")
    return addresses


def check_url(
    url: str, resolver: Callable[[str, int], tuple[str, ...]] = resolve_addresses
) -> CheckedUrl:
    if len(url) > 4096 or any(ord(ch) < 33 or ch in "\\" for ch in url):
        raise ProcessingError("UNSAFE_URL")
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").encode("idna").decode("ascii").lower()
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except (ValueError, UnicodeError) as exc:
        raise ProcessingError("UNSAFE_URL") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or not host
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ProcessingError("UNSAFE_URL")
    if parsed.fragment or "%" in host or host.endswith(".") or port not in {80, 443}:
        raise ProcessingError("UNSAFE_URL")
    # Avoid resolver-specific octal/hex/single-integer IP spellings.
    addresses: tuple[str, ...]
    try:
        literal = ipaddress.ip_address(host)
        addresses = (str(literal),)
    except ValueError:
        if host[0].isdigit() and (
            host.isdigit()
            or host.lower().startswith("0x")
            or all(c in "0123456789.xabcdef" for c in host)
        ):
            raise ProcessingError("ALTERNATE_IP_LITERAL") from None
        try:
            addresses = resolver(host, port)
        except OSError as exc:
            raise ProcessingError("URL_DNS_FAILED") from exc
    if not addresses:
        raise ProcessingError("URL_DNS_FAILED")
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise ProcessingError("INVALID_RESOLVED_IP") from exc
        if (
            not ip.is_global
            or ip.is_multicast
            or ip.is_unspecified
            or (
                isinstance(ip, ipaddress.IPv6Address)
                and (
                    ip.ipv4_mapped is not None
                    or ip.sixtofour is not None
                    or ip.teredo is not None
                    or ip in ipaddress.ip_network("64:ff9b::/96")
                    or ip in ipaddress.ip_network("64:ff9b:1::/48")
                )
            )
        ):
            raise ProcessingError("SSRF_ADDRESS_BLOCKED")
    target = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
    return CheckedUrl(
        url=url, scheme=parsed.scheme, host=host, port=port, target=target, addresses=addresses
    )


class FetchResponse(Protocol):
    status: int

    def header(self, name: str) -> str | None: ...
    def chunks(self, deadline: float) -> Iterator[bytes]: ...
    def close(self) -> None: ...


class HttpTransport(Protocol):
    def get(self, target: CheckedUrl, deadline: float) -> FetchResponse: ...


def dial_pinned(ip: str, port: int, timeout: float) -> socket.socket:
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    connection = socket.socket(family, socket.SOCK_STREAM)
    try:
        connection.settimeout(timeout)
        connection.connect((ip, port))  # numeric IP only; DNS cannot rebind at connect
        return connection
    except OSError:
        connection.close()
        raise


class PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, target: CheckedUrl, timeout: float) -> None:
        super().__init__(target.host, target.port, timeout=timeout)
        self.target = target
        self.bound_timeout = timeout

    def connect(self) -> None:
        self.sock = dial_pinned(self.target.addresses[0], self.target.port, self.bound_timeout)


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, target: CheckedUrl, timeout: float) -> None:
        self.ssl_context = ssl.create_default_context()
        super().__init__(target.host, target.port, timeout=timeout, context=self.ssl_context)
        self.target = target
        self.bound_timeout = timeout

    def connect(self) -> None:
        raw = dial_pinned(self.target.addresses[0], self.target.port, self.bound_timeout)
        try:
            self.sock = self.ssl_context.wrap_socket(raw, server_hostname=self.target.host)
        except OSError:
            raw.close()
            raise


class LiveResponse:
    def __init__(
        self, connection: http.client.HTTPConnection, response: http.client.HTTPResponse
    ) -> None:
        self.connection, self.response, self.status = connection, response, response.status

    def header(self, name: str) -> str | None:
        return self.response.getheader(name)

    def chunks(self, deadline: float) -> Iterator[bytes]:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProcessingError("URL_TIMEOUT")
            if self.connection.sock is not None:
                self.connection.sock.settimeout(remaining)
            chunk = self.response.read(64 * 1024)
            if not chunk:
                return
            yield chunk

    def close(self) -> None:
        self.response.close()
        self.connection.close()


class PinnedHttpTransport:
    def get(self, target: CheckedUrl, deadline: float) -> FetchResponse:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ProcessingError("URL_TIMEOUT")
        connection = (
            PinnedHTTPSConnection(target, remaining)
            if target.scheme == "https"
            else PinnedHTTPConnection(target, remaining)
        )
        try:
            connection.request(
                "GET",
                target.target,
                headers={"Accept-Encoding": "identity", "User-Agent": "FinAgent-local-ingestion"},
            )
            return LiveResponse(connection, connection.getresponse())
        except (OSError, http.client.HTTPException):
            connection.close()
            raise


@dataclass(frozen=True)
class FetchedContent:
    content: bytes
    mime_type: str
    final_url: str


class SafeUrlFetcher:
    def __init__(
        self,
        transport: HttpTransport | None = None,
        resolver: Callable[[str, int], tuple[str, ...]] = resolve_addresses,
    ) -> None:
        self.transport = transport or PinnedHttpTransport()
        self.resolver = resolver

    def fetch(self, url: str, ctx: ExecutionContext) -> FetchedContent:
        authorize(ctx, "url:fetch")
        authorize(ctx, "document:write")
        deadline = time.monotonic() + min(
            FETCH_TIMEOUT, max(0, (ctx.deadline - datetime.now(UTC)).total_seconds())
        )
        try:
            for redirect in range(MAX_REDIRECTS + 1):
                target = check_url(
                    url,
                    lambda host, port: resolve_before_deadline(self.resolver, host, port, deadline),
                )
                if time.monotonic() >= deadline:
                    raise ProcessingError("URL_TIMEOUT")
                response = self.transport.get(target, deadline)
                try:
                    if response.status in {301, 302, 303, 307, 308}:
                        location = response.header("Location")
                        if not location or redirect == MAX_REDIRECTS:
                            raise ProcessingError("URL_REDIRECT_LIMIT")
                        following = urljoin(url, location)
                        if (
                            urlsplit(url).scheme == "https"
                            and urlsplit(following).scheme != "https"
                        ):
                            raise ProcessingError("URL_TLS_DOWNGRADE")
                        url = following
                        continue
                    if response.status != 200:
                        raise ProcessingError("URL_HTTP_STATUS")
                    if (response.header("Content-Encoding") or "identity").lower() != "identity":
                        raise ProcessingError("URL_CONTENT_ENCODING")
                    length = response.header("Content-Length")
                    if length is not None and (not length.isdigit() or int(length) > MAX_URL_BYTES):
                        raise ProcessingError("URL_BODY_LIMIT")
                    mime = (response.header("Content-Type") or "").split(";", 1)[0].strip().lower()
                    if mime not in {
                        "application/pdf",
                        "text/plain",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    }:
                        raise ProcessingError("URL_CONTENT_TYPE")
                    chunks: list[bytes] = []
                    total = 0
                    for chunk in response.chunks(deadline):
                        total += len(chunk)
                        if total > MAX_URL_BYTES or time.monotonic() > deadline:
                            raise ProcessingError("URL_BODY_LIMIT_OR_TIMEOUT")
                        chunks.append(chunk)
                    return FetchedContent(b"".join(chunks), mime, url)
                finally:
                    response.close()
        except (OSError, http.client.HTTPException) as exc:
            raise ProcessingError("URL_TRANSPORT_FAILED") from exc
        raise ProcessingError("URL_REDIRECT_LIMIT")
