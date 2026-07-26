from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from urllib.parse import urljoin

import anyio
import httpx2
from anyio.streams.memory import MemoryObjectSendStream
from bs4 import BeautifulSoup

from .filtering import POSITION_KEYWORDS
from .http_client import create_async_client
from .models import RawPosting
from .sources import SOURCES, Source

MIN_TITLE_LENGTH: Final = 5
MAX_LINKS_PER_SOURCE: Final = 12
DISCOVERY_KEYWORDS: Final = (
    *POSITION_KEYWORDS,
    "채용",
    "모집",
    "recruit",
    "career",
)


@dataclass(frozen=True, slots=True)
class SourceResult:
    source_name: str
    postings: tuple[RawPosting, ...]
    error: str | None


def _candidate_links(source: Source, html: str) -> tuple[tuple[str, str, str], ...]:
    soup = BeautifulSoup(html, "html.parser")
    found: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href", "")).strip()
        if not href or href.startswith(("javascript:", "#", "mailto:")):
            continue
        parent_text = anchor.parent.get_text(" ", strip=True) if anchor.parent else ""
        anchor_text = anchor.get_text(" ", strip=True)
        combined = f"{anchor_text} {parent_text}".strip()
        if not any(
            keyword.casefold() in combined.casefold() for keyword in DISCOVERY_KEYWORDS
        ):
            continue
        url = urljoin(source.url, href)
        if url in seen:
            continue
        seen.add(url)
        title = (
            anchor_text if len(anchor_text) >= MIN_TITLE_LENGTH else parent_text[:180]
        )
        found.append((title, url, combined))
        if len(found) >= MAX_LINKS_PER_SOURCE:
            break
    return tuple(found)


async def _fetch_source(
    client: httpx2.AsyncClient,
    source: Source,
    sender: MemoryObjectSendStream[SourceResult],
) -> None:
    async with sender:
        try:
            response = await client.get(source.url)
            _ = response.raise_for_status()
            links = _candidate_links(source, response.text)
            postings: list[RawPosting] = []
            for title, url, list_text in links:
                detail_text = list_text
                try:
                    detail = await client.get(url)
                    _ = detail.raise_for_status()
                    detail_text = BeautifulSoup(detail.text, "html.parser").get_text(
                        " ", strip=True
                    )
                except httpx2.HTTPError as error:
                    detail_text = (
                        f"{list_text} 상세 페이지 접근 실패: {type(error).__name__}"
                    )
                postings.append(
                    RawPosting(source.institution, title, url, detail_text[:12000])
                )
            await sender.send(SourceResult(source.name, tuple(postings), None))
        except httpx2.HTTPError as error:
            await sender.send(
                SourceResult(source.name, (), f"{type(error).__name__}: {error}")
            )


async def collect_sources() -> tuple[SourceResult, ...]:
    send, receive = anyio.create_memory_object_stream[SourceResult](
        max_buffer_size=len(SOURCES)
    )
    results: list[SourceResult] = []
    async with create_async_client() as client, anyio.create_task_group() as group:
        for source in SOURCES:
            group.start_soon(_fetch_source, client, source, send.clone())
        await send.aclose()
        async with receive:
            async for result in receive:
                results.append(result)
    return tuple(sorted(results, key=lambda item: item.source_name))
