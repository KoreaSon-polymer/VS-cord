from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
import os
import re
import time
import anyio
import httpx2
from bs4 import BeautifulSoup
from pydantic import ValidationError
from tools.notice_utils import article_text, canonical_url
from tools.notice_documents import attachment_links, document_text, MAX_BYTES
from .filtering import EXCLUDED_ROLES, EXCLUDED_KEYWORDS
from .triage import role_title_excluded, is_recruitment_title
from .discovery import (DIRECTORY, aggregate_link_title, board_links, normalize_aggregate_text,
                        nrc_fields, nst_registry, notice_institution)
from .http_client import bounded_get, create_async_client, stream_public_page
from .models import RawPosting
from .national_registry import REGISTRY_URL, fetch_university_sources, university_batch
from .sources import SOURCES, Source

MAX_LINKS_PER_SOURCE = 50


def forwarded_notice(source, markup):
    """Follow the original notice when the council publishes a specific posting."""
    if source.name.startswith('NRC-'):
        fields = nrc_fields(markup)
        target = fields.get('URL', '')
        if target.startswith(('https://', 'http://')) and re.search(r'[?&]list_no=\d+|/\d{3,}(?:[?#]|$)', target):
            return fields.get('채용기관', source.institution), canonical_url(target)
    if not source.name.startswith('NST-'):
        return None
    soup = BeautifulSoup(markup, 'html.parser')
    institution, target = source.institution, None
    for row in soup.select('tr'):
        label = row.find('th')
        value = row.find('td')
        if not label or not value:
            continue
        if label.get_text(strip=True) == '소관기관':
            institution = value.get_text(' ', strip=True)
        if '주소' in label.get_text() and '링크' in label.get_text():
            a = value.find('a', href=True)
            match = re.search(r'https?://[^\s<>]+', value.get_text(' ', strip=True))
            target = a['href'] if a else match.group(0) if match else None
    if target and target.startswith(('https://', 'http://')):
        return institution, canonical_url(target)
    return None


@dataclass(frozen=True, slots=True)
class SourceResult:
    source_name: str
    postings: tuple[RawPosting, ...]
    error: str | None
    discovered: int = 0
    detail_errors: int = 0
    institution: str = ""
    url: str = ""
    kind: str = "institute"
    board_urls: tuple[str, ...] = ()
    scheduled_count: int = 0


def _candidate_links(source: Source, markup: str):
    soup = BeautifulSoup(markup, 'html.parser')
    # KFRI uses clickable table rows instead of anchors. Read literal paths
    # from this known board; do not execute JavaScript.
    if source.name == 'KFRI':
        for row in soup.select('tr[onclick]'):
            match = re.search(r"location\.href\s*=\s*['\"](/web/board/13/\d+)['\"]", row['onclick'])
            cell = row.select_one('.tit_td')
            if match and cell and not cell.find('a'):
                a = soup.new_tag('a', href=match.group(1))
                a.string = cell.get_text(' ', strip=True)
                cell.clear()
                cell.append(a)
    found, seen = [], set()
    for a in soup.select('a[href]'):
        href = a.get('href', '').strip()
        if not href or href.startswith(('javascript:', '#', 'mailto:')):
            continue
        title = re.sub(r'\s+', ' ', aggregate_link_title(source, a, href)).strip()
        # Do not borrow a sibling posting's title from the whole parent container.
        if len(title) < 8 or role_title_excluded(title) or any(k in title for k in EXCLUDED_KEYWORDS):
            continue
        if not is_recruitment_title(title):
            continue
        if title in ('교수초빙/직원채용', '교수초빙', '교수 초빙', '채용공고', '채용정보', '채용안내', '채용공고(온라인)'):
            continue
        url = canonical_url(urljoin(source.url, href))
        if not url.startswith(('https://', 'http://')) or url == canonical_url(source.url) or url in seen:
            continue
        seen.add(url)
        row = a.find_parent('tr') or a.find_parent('li') or a.parent
        found.append((title, url, row.get_text(' ', strip=True)[:1000]))
    # Relevant permanent positions are not hidden behind a dozen navigation links.
    found.sort(key=lambda x: not bool(re.search(r'전임|정규|정년|교수', x[0])))
    return tuple(found)


async def get_with_retry(client, url):
    """Retry transient failures only; never disable TLS certificate validation."""
    for attempt in range(3):
        try:
            return await bounded_get(client, url, 4_000_000)
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status not in (None, 408, 429, 500, 502, 503, 504) or attempt == 2:
                raise
            await anyio.sleep(0.5 * (2 ** attempt))

async def _collect_one(client, source):
    postings, errors, discovered, boards = [], [], 0, []
    seen_details, seen_pages = set(), set()
    queue = [(source.url, 0)]
    started = time.monotonic()
    try:
        while queue and len(seen_pages) < (6 if source.discover else 3):
            page_url, depth = queue.pop(0)
            if page_url in seen_pages:
                continue
            if time.monotonic() - started > 100:
                errors.append("source_time_budget_exceeded")
                break
            seen_pages.add(page_url)
            try:
                response = await get_with_retry(client, page_url)
            except Exception as exc:
                errors.append(type(exc).__name__)
                continue
            page = replace(source, url=str(response.url))
            links = _candidate_links(page, response.text)
            boards.append(str(response.url))
            if depth < 2 and (source.discover or not links):
                queue += [(u, depth+1) for u in board_links(response.text, str(response.url))
                          if u not in seen_pages]
            # Preserve list pagination. Identity canonicalization strips pageIndex.
            if not source.name.startswith(("KCUE-", "NST-", "NRC-", "JOB-ALIO")) and depth == 0:
                for a in BeautifulSoup(response.text, "html.parser").select("a[href]"):
                    if a.get_text(strip=True) in ("2", "3") and a.get("href") and not a["href"].startswith(("#", "javascript:")):
                        nxt = urljoin(str(response.url), a["href"])
                        if nxt not in seen_pages:
                            queue.append((nxt, 1))
            if len(links) > MAX_LINKS_PER_SOURCE:
                errors.append("candidate_limit_reached")
            for title, url, list_text in links[:MAX_LINKS_PER_SOURCE]:
                if url in seen_details:
                    continue
                seen_details.add(url)
                discovered += 1
                if time.monotonic() - started > 120:
                    postings.append(RawPosting(source.institution, title, url, list_text,
                                               review_notes=("수집 시간 제한: 상세 미확인",)))
                    errors.append("detail_time_budget_exceeded")
                    continue
                notes = []
                try:
                    detail = await get_with_retry(client, url)
                    url = str(detail.url)
                    institution = notice_institution(source, title, detail.text)
                    mirror_text = ''
                    forwarded = forwarded_notice(source, detail.text)
                    if source.name.startswith('NRC-'):
                        fields = nrc_fields(detail.text)
                        if fields.get('마감여부') in {'마감', '종료', '완료'}:
                            postings.append(RawPosting(institution, title, forwarded[1] if forwarded else url, '접수상태: 마감'))
                            continue
                        mirror_text = '채용기간 ' + fields.get('채용기간', '')
                    if forwarded:
                        target_institution, target_url = forwarded
                        try:
                            detail = await get_with_retry(client, target_url)
                            institution, url = target_institution, str(detail.url)
                        except httpx2.HTTPError:
                            notes.append('공식 원문 접근 미확인')
                    text = normalize_aggregate_text(source, article_text(detail.text)) + '\n' + mirror_text
                    attachments = attachment_links(detail.text, url)
                    for attachment in attachments:
                        try:
                            async with stream_public_page(client, attachment) as doc:
                                chunks, size = [], 0
                                async for chunk in doc.aiter_raw(chunk_size=65536):
                                    size += len(chunk)
                                    if size > MAX_BYTES:
                                        raise ValueError("Attachment too large")
                                    chunks.append(chunk)
                            extra = await anyio.to_thread.run_sync(document_text, b"".join(chunks))
                            if not extra.strip():
                                raise ValueError("Empty or scanned attachment")
                            text += "\n" + extra
                        except Exception as exc:
                            notes.append("첨부 미확인: "+type(exc).__name__)
                    if re.search(r"첨부\s*(?:파일|문서).*?(?:참조|확인)|붙임.*?공고문", text) and not attachments:
                        notes.append("첨부 링크 추출 여부 확인 필요")
                    if len(text.strip()) < 100:
                        notes.append("상세 본문 불충분")
                    postings.append(RawPosting(institution, title, url, text,
                                               review_notes=tuple(dict.fromkeys(notes))))
                    errors.extend(notes)
                except Exception as exc:
                    errors.append("detail:"+type(exc).__name__)
                    postings.append(RawPosting(source.institution, title, url,
                                               "상세 페이지 접근 실패\n"+list_text,
                                               review_notes=("상세 페이지 접근 실패",)))
        if queue:
            errors.append("page_budget_reached")
        if not discovered:
            errors.append("no_candidate_links: 게시판·동적 목록 확인 필요")
        return SourceResult(source.name, tuple(postings), "; ".join(dict.fromkeys(errors)) or None,
                            discovered, len(errors), source.institution, source.url, source.kind, tuple(boards))
    except Exception as exc:
        return SourceResult(source.name, tuple(postings), type(exc).__name__, discovered,
                            len(errors), source.institution, source.url, source.kind, tuple(boards))

async def _national_universities(client: httpx2.AsyncClient, sources: list[Source]) -> tuple[tuple[Source, ...], SourceResult]:
    count = 0
    scheduled: tuple[Source, ...] = ()
    error = None
    try:
        with anyio.fail_after(25):
            registry = await fetch_university_sources(client, sources)
        count = len(registry)
        today = datetime.now(timezone.utc).date()
        evening = os.environ.get('SEND_DIGEST', 'true').lower() == 'true'
        scheduled = university_batch(registry, today, evening=evening)
        if not count:
            error = "no_new_university_homepages"
    except (httpx2.HTTPError, TimeoutError, ValidationError) as exc:
        error = type(exc).__name__
    return scheduled, SourceResult("KCUE-national-registry", (), error, count, 0,
                                   "전국 대학·전문대학 명부", REGISTRY_URL, "registry",
                                   scheduled_count=len(scheduled))


async def collect_sources():
    results = []
    limiter = anyio.CapacityLimiter(8)
    async with create_async_client(public_only=True) as client:
        sources = list(SOURCES)
        try:
            directory = await get_with_retry(client, DIRECTORY)
            extras = nst_registry(directory.text, sources)
            sources.extend(extras)
            results.append(SourceResult("NST-registry", (), None, len(extras), 0,
                                        "NST 기관 명부", DIRECTORY, "registry"))
        except Exception as exc:
            results.append(SourceResult("NST-registry", (), type(exc).__name__, institution="NST 기관 명부",
                                        url=DIRECTORY, kind="registry"))
        university_batch, registry_result = await _national_universities(client, sources)
        results.append(registry_result)
        sources.extend(university_batch)
        async def one(source):
            async with limiter:
                budget = 45 if source.name.startswith("KCUE-registry-") else 180
                with anyio.move_on_after(budget) as scope:
                    result = await _collect_one(client, source)
                if scope.cancel_called:
                    result = SourceResult(source.name, (), "source_time_budget_exceeded",
                                          institution=source.institution, url=source.url, kind=source.kind)
                results.append(result)
        async with anyio.create_task_group() as group:
            for source in sources:
                group.start_soon(one, source)
    return tuple(sorted(results, key=lambda r:r.source_name))
