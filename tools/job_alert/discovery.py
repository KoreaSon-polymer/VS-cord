"""Bounded discovery from institution-published recruitment links."""
import re
from urllib.parse import parse_qs, urljoin, urlsplit
from bs4 import BeautifulSoup, NavigableString, Tag
from tools.notice_utils import canonical_url
from .sources import Source
DIRECTORY = "https://audit.nst.re.kr/"
BOARD_WORDS = re.compile(r"교[수원]\s*초빙|교원\s*채용|교원\s*공채|채용|인재\s*채용|recruit|faculty|employment|vacanc", re.I)


def aggregate_link_title(source: Source, anchor: Tag, href: str) -> str:
    """Read real aggregate links, including JOB-ALIO's self-closing anchor."""
    if source.name.startswith(("JOB-ALIO", "NRC-")):
        target = urlsplit(urljoin(source.url, href))
        query = parse_qs(target.query)
        if source.name.startswith("JOB-ALIO") and not (
            target.hostname == "job.alio.go.kr" and target.path.lower().endswith("/recruitview.do")
            and query.get("idx", [""])[0].isdecimal()
        ):
            return ""
        if source.name.startswith("NRC-") and not query.get("list_no", [""])[0].isdecimal():
            return ""
        title = anchor.get("title")
        if isinstance(title, str) and title.strip():
            return title
    text = anchor.get_text(" ", strip=True)
    if not text and source.name.startswith("JOB-ALIO") and isinstance(anchor.next_sibling, NavigableString):
        return str(anchor.next_sibling).strip()
    return text


def nrc_fields(markup: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in BeautifulSoup(markup, "html.parser").select(".tstyle_view .head li"):
        label = item.find("strong")
        value = item.find("span")
        if label and value:
            fields[label.get_text(strip=True)] = value.get_text(" ", strip=True)
    return fields


def normalize_aggregate_text(source: Source, text: str) -> str:
    if source.name.startswith("JOB-ALIO"):
        return re.sub(r"(채용\s*기간\s+)(\d{2}\.\d{2}\.\d{2})(\s*[~∼]\s*)(\d{2}\.\d{2}\.\d{2})",
                      r"\g<1>20\g<2>\g<3>20\g<4>", text)
    return text

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
    if source.name.startswith("NRC-"):
        institution = nrc_fields(markup).get("채용기관")
        if institution:
            return institution
        match = re.search(r"\[([^\]]+(?:연구원|연구소|대학원))\]", title)
        if match:
            return match.group(1)
    if source.name == "ALIO" or source.name.startswith("JOB-ALIO"):
        soup = BeautifulSoup(markup, "html.parser")
        heading = soup.select_one("#contentRV .topInfo h2")
        if heading:
            return heading.get_text(" ", strip=True)
        for row in soup.select("tr"):
            cells = row.find_all(["th", "td"])
            for i, cell in enumerate(cells[:-1]):
                if cell.get_text(strip=True) in ("기관명", "공공기관명"):
                    return cells[i+1].get_text(" ", strip=True)
    return source.institution
