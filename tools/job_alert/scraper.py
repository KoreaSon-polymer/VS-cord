from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit
import re
import time
import anyio
import httpx2
from bs4 import BeautifulSoup
from tools.notice_utils import article_text, canonical_url
from tools.notice_documents import attachment_links, document_text, MAX_BYTES
from .filtering import EXCLUDED_ROLES, EXCLUDED_KEYWORDS
from .http_client import create_async_client
from .models import RawPosting
from .sources import SOURCES, Source

MAX_LINKS_PER_SOURCE = 25


@dataclass(frozen=True, slots=True)
class SourceResult:
    source_name: str
    postings: tuple[RawPosting, ...]
    error: str | None
    discovered: int = 0
    detail_errors: int = 0


def _candidate_links(source: Source, markup: str):
    soup = BeautifulSoup(markup, 'html.parser')
    found, seen = [], set()
    for a in soup.select('a[href]'):
        href = a.get('href', '').strip()
        if not href or href.startswith(('javascript:', '#', 'mailto:')):
            continue
        title = re.sub(r'\s+', ' ', a.get_text(' ', strip=True)).strip()
        # Do not borrow a sibling posting's title from the whole parent container.
        if len(title) < 8 or EXCLUDED_ROLES.search(title) or any(k in title for k in EXCLUDED_KEYWORDS):
            continue
        if not re.search(r'채용|초빙|임용|모집|recruit|vacan|faculty', title, re.I):
            continue
        if title in ('교수초빙/직원채용', '교수초빙', '교수 초빙', '채용공고', '채용정보', '채용안내'):
            continue
        url = canonical_url(urljoin(source.url, href))
        if not url.startswith(('https://', 'http://')) or url == canonical_url(source.url) or url in seen:
            continue
        seen.add(url)
        row = a.find_parent('tr') or a.find_parent('li') or a.parent
        found.append((title, url, row.get_text(' ', strip=True)[:1000]))
    # Relevant permanent positions are not hidden behind a dozen navigation links.
    found.sort(key=lambda x: not bool(re.search(r'전임|정규|정년|교수', x[0])))
    return tuple(found[:MAX_LINKS_PER_SOURCE])


async def _collect_one(client, source):
    try:
        response = await client.get(source.url)
        response.raise_for_status()
        links = _candidate_links(source, response.text)
        postings, detail_errors = [], 0
        started = time.monotonic()
        for title, url, list_text in links:
            if time.monotonic() - started > 75:
                detail_errors += len(links) - len(postings)
                break
            try:
                detail = await client.get(url)
                detail.raise_for_status()
                text = article_text(detail.text)
                if re.search(r'전임|교원|교수|정규|연구직', title):
                    for attachment in attachment_links(detail.text, url):
                        try:
                            async with client.stream('GET', attachment) as doc:
                                doc.raise_for_status()
                                chunks, size = [], 0
                                async for chunk in doc.aiter_bytes():
                                    size += len(chunk)
                                    if size > MAX_BYTES:
                                        raise ValueError('Attachment too large')
                                    chunks.append(chunk)
                            extra = await anyio.to_thread.run_sync(document_text, b''.join(chunks))
                            text += '\n' + extra
                        except Exception:
                            detail_errors += 1
                postings.append(RawPosting(source.institution, title, url, text))
            except Exception:
                detail_errors += 1
        error = 'no_candidate_links: 게시판·동적 목록 확인 필요' if not links else None
        if detail_errors:
            error = (error + '; ' if error else '') + f'detail_or_attachment_failures={detail_errors}'
        return SourceResult(source.name, tuple(postings), error, len(links), detail_errors)
    except Exception as e:
        return SourceResult(source.name, (), type(e).__name__)


async def collect_sources():
    results = []
    limiter = anyio.CapacityLimiter(6)
    async with create_async_client() as client:
        async def one(source):
            async with limiter:
                with anyio.move_on_after(240) as scope:
                    result = await _collect_one(client, source)
                if scope.cancel_called:
                    result = SourceResult(source.name, (), 'source_time_budget_exceeded')
                results.append(result)
        async with anyio.create_task_group() as group:
            for source in SOURCES:
                group.start_soon(one, source)
    return tuple(sorted(results, key=lambda r:r.source_name))
