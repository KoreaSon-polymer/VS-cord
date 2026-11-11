from __future__ import annotations

import logging
import socket
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Final

import httpx2

from .public_network import PublicHTTPTransport

LOGGER: Final = logging.getLogger(__name__)
LIMITS: Final = httpx2.Limits(
    max_connections=200,
    max_keepalive_connections=40,
    keepalive_expiry=30.0,
)
TIMEOUT: Final = httpx2.Timeout(connect=10.0, read=20.0, write=10.0, pool=10.0)
SOCKET_OPTIONS: Final = [(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)]
REDIRECT_LIMIT: Final = 10


async def _log_request(request: httpx2.Request) -> None:
    request.extensions["request_start"] = time.perf_counter()


async def _log_response(response: httpx2.Response) -> None:
    started = response.request.extensions.get("request_start")
    elapsed = time.perf_counter() - started if isinstance(started, float) else 0.0
    LOGGER.info(
        "HTTP %s %s -> %d in %.2fs",
        response.request.method,
        response.request.url,
        response.status_code,
        elapsed,
    )


def create_async_client(*, public_only: bool = False) -> httpx2.AsyncClient:
    return httpx2.AsyncClient(
        limits=LIMITS,
        trust_env=not public_only,
        timeout=TIMEOUT,
        transport=PublicHTTPTransport(LIMITS) if public_only else None,
        headers={"User-Agent": "KoreanResearchMonitor/2.0"},
        event_hooks={"request": [_log_request], "response": [_log_response]},
        follow_redirects=not public_only,
    )


@asynccontextmanager
async def stream_public_page(client: httpx2.AsyncClient, url: str) -> AsyncIterator[httpx2.Response]:
    target = httpx2.URL(url)
    for _ in range(REDIRECT_LIMIT + 1):
        if target.username or target.password:
            raise httpx2.InvalidURL("Crawler does not use URL credentials")
        async with client.stream("GET", target, follow_redirects=False,
                                 headers={"Accept-Encoding": "identity"}) as response:
            if response.next_request is None:
                response.raise_for_status()
                if response.headers.get("content-encoding", "identity").lower() != "identity":
                    raise httpx2.ReadError("Crawler expected an uncompressed response", request=response.request)
                yield response
                return
            target = response.next_request.url
    raise httpx2.TooManyRedirects("Crawler redirect limit exceeded")


async def bounded_get(client: httpx2.AsyncClient, url: str, max_bytes: int) -> httpx2.Response:
    """Buffer one decoded page within a fixed response-size budget."""
    async with stream_public_page(client, url) as response:
        body = bytearray()
        async for chunk in response.aiter_raw(chunk_size=65536):
            if len(body) + len(chunk) > max_bytes:
                raise httpx2.ReadError("Crawler response exceeds size limit", request=response.request)
            body.extend(chunk)
        headers = response.headers.copy()
        headers.pop("content-encoding", None)
        headers.pop("content-length", None)
        return httpx2.Response(
            response.status_code, headers=headers, content=bytes(body), request=response.request,
        )
