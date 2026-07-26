from __future__ import annotations

import logging
import socket
import time
from typing import Final

import httpx2

LOGGER: Final = logging.getLogger(__name__)
LIMITS: Final = httpx2.Limits(
    max_connections=200,
    max_keepalive_connections=40,
    keepalive_expiry=30.0,
)
TIMEOUT: Final = httpx2.Timeout(connect=5.0, read=30.0, write=10.0, pool=10.0)
SOCKET_OPTIONS: Final = [(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)]


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


def create_async_client() -> httpx2.AsyncClient:
    transport = httpx2.AsyncHTTPTransport(
        http2=True,
        retries=3,
        limits=LIMITS,
        socket_options=SOCKET_OPTIONS,
    )
    return httpx2.AsyncClient(
        transport=transport,
        timeout=TIMEOUT,
        headers={"User-Agent": "KoreanResearchJobAlert/1.0"},
        event_hooks={"request": [_log_request], "response": [_log_response]},
        follow_redirects=True,
    )
