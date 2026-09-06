"""Conservative extraction shared by the funding and permanent-career monitors."""
from __future__ import annotations

import re
from datetime import date
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup


def canonical_url(url: str) -> str:
    url = re.sub(r"(?:;|%3[bB])jsessionid(?:=|%3[dD])[^?&#/]+", "", url, flags=re.I)
    parts = urlsplit(url)
    ignored = {"jsessionid", "sessionid", "phpsessid", "gotopage", "pageindex",
               "pagenumber", "pagenum", "cpage", "searchtxt", "searchopt", "title"}
    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if k.lower() not in ignored and not k.lower().startswith("utm_")]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path,
                       urlencode(sorted(pairs)), ""))


def matches(text: str, terms) -> tuple[str, ...]:
    """Avoid English substring matches such as HER in 'other' or PI in 'topic'."""
    return tuple(t for t in terms if re.search(
        (r"(?<![a-zA-Z])" + re.escape(t) + r"(?![a-zA-Z])")
        if re.search(r"[a-zA-Z]", t) else re.escape(t), text, re.I))


def article_text(markup: str) -> str:
    soup = BeautifulSoup(markup, "html.parser")
    for node in soup.select("script, style, nav, header, footer, noscript, svg, .paginate, .pagination"):
        node.decompose()
    for selector in (".board-view", ".board_view", ".board-view-wrap", ".board_view_wrap",
                     ".board-view-content", ".board_view_con", ".view_cont", ".view-content",
                     ".view_con", ".bbs_view", ".b-view-box", "article", "#contents", "#content", "main"):
        node = soup.select_one(selector)
        if node and len(node.get_text(strip=True)) > 80:
            soup = node
            break
    # Keep table rows together, so the application label and period stay adjacent.
    for row in soup.select("tr"):
        row.replace_with("\n" + row.get_text(" ", strip=True) + "\n")
    text = soup.get_text("\n", strip=True)
    text = re.split(r"\n(?:이전글|다음글|이전 글|다음 글)\s*\n", text)[0]
    return text[:90000]


DATE = r"(20\d{2})\s*[./년-]\s*(\d{1,2})\s*[./월-]\s*(\d{1,2})"
DATE_RE = re.compile(DATE)
PERIOD_RE = re.compile(DATE + r"[.일]?\s*(?:\([^)]{1,5}\))?\s*(?:\d{1,2}:\d{2}(?::\d{2})?)?\s*[~∼～–-]\s*(?:(20\d{2})\s*[./년-]\s*)?(\d{1,2})\s*[./월-]\s*(\d{1,2})")
MARKER_RE = re.compile(r"(?:연구책임자\s*)?(?:접수\s*기간|신청\s*기간|지원\s*기간|모집\s*기간|원서\s*접수|온라인\s*접수|접수\s*마감|신청\s*마감|마감일|제출\s*기한|deadline|application\s*period)", re.I)


def dates(text: str) -> tuple[date, ...]:
    result = []
    for match in DATE_RE.finditer(text):
        try:
            result.append(date(*map(int, match.groups())))
        except ValueError:
            pass
    return tuple(result)


def application_period(text: str, title: str = "") -> tuple[date | None, date | None, str]:
    """Use labeled application dates, never a publication or appointment date."""
    compact = re.sub(r"\s+", " ", text)
    windows = [compact[m.start():m.start() + 180] for m in MARKER_RE.finditer(compact)]
    # A complete range in the title is explicit enough to disqualify an expired notice.
    if PERIOD_RE.search(title):
        windows.insert(0, title)
    for window in windows:
        # Don't consume a later interview or appointment date as the deadline.
        window = re.split(r"(?:임용예정|임용일|면접일|합격자\s*발표|기관\s*승인)", window)[0]
        match = PERIOD_RE.search(window)
        if match:
            y, m, d, ey, em, ed = match.groups()
            try:
                start = date(int(y), int(m), int(d))
                end = date(int(ey or y), int(em), int(ed))
                if not ey and end < start and start.month == 12:
                    end = end.replace(year=start.year + 1)
                if end >= start:
                    return start, end, window[:match.end()]
            except ValueError:
                pass
        ds = dates(window)
        if len(ds) >= 2:
            return ds[0], ds[1], window
        if ds and re.search(r"마감|기한|deadline|까지", window, re.I):
            return None, ds[0], window
    return None, None, ""


CORE_FIELDS = ("유기반도체", "유기 반도체", "organic semiconductor", "고분자", "polymer",
               "유기합성", "유기 합성", "organic synthesis", "광촉매", "photocatalysis", "photocatalytic",
               "전기화학", "electrochemistry", "electrochemical", "광전", "optoelectronic",
               "유기전자", "organic electronics", "OMIEC", "OECT", "수소생산", "수소 생산",
               "수소 발생", "hydrogen evolution", "수소 센서", "계면", "interface", "전하전달",
               "self-assembled", "n-type SAM")
ADJACENT_FIELDS = ("재료화학", "화학", "화공", "화학공학", "신소재", "에너지소재", "에너지 소재",
                   "첨단소재", "반도체", "나노소재", "센서", "chemistry", "chemical engineering",
                   "materials science", "semiconductor", "sensor", "energy materials")


def research_matches(text: str) -> tuple[str, ...]:
    return matches(text, CORE_FIELDS + ADJACENT_FIELDS)
