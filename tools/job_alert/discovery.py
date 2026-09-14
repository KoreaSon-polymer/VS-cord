"""Bounded discovery from institution-published recruitment links."""
import re
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from tools.notice_utils import canonical_url
from .sources import Source
DIRECTORY = "https://audit.nst.re.kr/"
BOARD_WORDS = re.compile(r"교[수원]\s*초빙|교원\s*채용|교원\s*공채|채용|인재\s*채용|recruit|faculty|employment|vacanc", re.I)

def board_links(markup, base):
    result = []
    for a in BeautifulSoup(markup, "html.parser").select("a[href]"):
        label = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
        href = a.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue
        if not BOARD_WORDS.search(label) or len(label) > 65:
            continue
        url = canonical_url(urljoin(base, href))
        if not urlsplit(url).hostname or not url.startswith(("http://", "https://")):
            continue
        if re.search(r"login|logout|sign.?up", url, re.I):
            continue
        if url != canonical_url(base) and url not in result:
            result.append(url)
    result.sort(key=lambda u: not re.search(r"faculty|prof|invite|recruit", u, re.I))
    return result[:5]

def nst_registry(markup, existing):
    known = {(urlsplit(s.url).hostname or "").removeprefix("www.") for s in existing}
    result, seen = [], set()
    for a in BeautifulSoup(markup, "html.parser").select("a[href]"):
        name = a.get_text(" ", strip=True)
        url = urljoin(DIRECTORY, a["href"])
        host = (urlsplit(url).hostname or "").removeprefix("www.")
        if not re.search(r"한국.*연구원|국가.*연구소|세계김치연구소", name):
            continue
        if not host.endswith(".re.kr") or host == "audit.nst.re.kr" or host in seen or host in known:
            continue
        seen.add(host)
        result.append(Source("NST-directory-"+host.split(".")[0], name, url, True, "institute"))
    return tuple(result)

def notice_institution(source, title, markup):
    if source.name.startswith("KCUE-"):
        match = re.search(r"\[([^\]]*(?:대학교|대학|과학기술원))\]", title)
        if match:
            return match.group(1)
    if source.name in ("ALIO", "JOB-ALIO"):
        for row in BeautifulSoup(markup, "html.parser").select("tr"):
            cells = row.find_all(["th", "td"])
            for i, cell in enumerate(cells[:-1]):
                if cell.get_text(strip=True) in ("기관명", "공공기관명"):
                    return cells[i+1].get_text(" ", strip=True)
    return source.institution
