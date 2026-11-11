"""Keep the crawler's TCP connections on public HTTP(S) destinations."""

import socket
from collections.abc import Iterable
from ipaddress import ip_address
from typing import Final

import anyio
import httpcore2
import httpx2

PUBLIC_WEB_PORTS: Final = frozenset({80, 443})
SocketOption = tuple[int, int, int | bytes]


class PublicNetworkBackend(httpcore2.AnyIOBackend):
    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[SocketOption] | None = None,
    ) -> httpcore2.AsyncNetworkStream:
        if port not in PUBLIC_WEB_PORTS:
            raise httpcore2.ConnectError("Crawler destination is not a public web port")
        try:
            with anyio.fail_after(timeout):
                addresses = await anyio.getaddrinfo(host, port, type=socket.SOCK_STREAM)
                targets = tuple(dict.fromkeys(address[4][0] for address in addresses))
                for target in targets:
                    ip = ip_address(target)
                    if not ip.is_global or ip.is_multicast:
                        continue
                    try:
                        # HTTP Core keeps the hostname for TLS and sends TCP to the checked IP.
                        return await super().connect_tcp(
                            target,
                            port,
                            timeout,
                            local_address,
                            socket_options,
                        )
                    except (httpcore2.ConnectError, httpcore2.ConnectTimeout):
                        continue
        except TimeoutError as exc:
            raise httpcore2.ConnectTimeout("Crawler connection timed out") from exc
        except OSError as exc:
            raise httpcore2.ConnectError("Crawler DNS lookup failed") from exc
        raise httpcore2.ConnectError("Crawler could not connect to a public address")


class PublicHTTPTransport(httpx2.AsyncHTTPTransport):
    def __init__(self, limits: httpx2.Limits) -> None:
        # HTTPX 2.9's transport delegates all I/O to this HTTP Core pool.
        self._pool = httpcore2.AsyncConnectionPool(
            ssl_context=httpx2.create_ssl_context(trust_env=False),
            http2=True,
            max_connections=limits.max_connections,
            max_keepalive_connections=limits.max_keepalive_connections,
            keepalive_expiry=limits.keepalive_expiry,
            network_backend=PublicNetworkBackend(),
            socket_options=[(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)],
        )
