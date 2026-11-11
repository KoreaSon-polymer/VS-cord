"""University recruitment discovery from the KCUE government data download."""

import hashlib
import re
from collections.abc import Iterable
from datetime import date
from typing import Final
from urllib.parse import urlencode, urlsplit, urlunsplit

import httpx2
from pydantic import BaseModel, ConfigDict, TypeAdapter

from .http_client import bounded_get
from .sources import Source

REGISTRY_URL: Final = "https://www.data.go.kr/data/15107736/standard.do"
REGISTRY_METADATA_URL: Final = (
    "https://www.data.go.kr/download/columList.json?pk=15107736&ext=CSV"
)
REGISTRY_DOWNLOAD_URL: Final = "https://www.data.go.kr/download/standard.json"
REGISTRY_FIELDS: Final = ("SCHL_NM", "HMPG_ADDR", "UNIV_SE_NM", "CRTR_YR")
DAILY_LIMIT: Final = 40


class RegistryMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    totalCount: int


class UniversityRow(BaseModel):
    model_config = ConfigDict(frozen=True)
    SCHL_NM: str = ""
    HMPG_ADDR: str | None = None
    UNIV_SE_NM: str = ""
    CRTR_YR: str = ""


UNIVERSITY_ROWS: Final = TypeAdapter(list[UniversityRow])


def _institution_key(name: str) -> str:
    name = re.sub(r"\s*\([A-Za-z -]+\)", "", name)
    return "".join(name.split()).casefold().removeprefix("국립")


def _home_url(value: str) -> str | None:
    value = value.strip()
    try:
        url = urlsplit(value if "://" in value else "https://" + value)
        host = url.hostname or ""
        if (
            url.scheme not in {"http", "https"}
            or url.username is not None
            or url.port not in (None, 80, 443)
            or not re.fullmatch(r"(?:[a-z0-9-]+\.)+(?:kr|edu|org|com|net)", host)
        ):
            return None
        return urlunsplit((url.scheme, url.netloc, url.path or "/", url.query, ""))
    except ValueError:
        return None


def university_sources(
    payload: bytes, existing: Iterable[Source]
) -> tuple[Source, ...]:
    """Return unregistered university and college homepages from the latest year."""
    rows = UNIVERSITY_ROWS.validate_json(payload)
    year = max((row.CRTR_YR for row in rows if row.CRTR_YR.isdecimal()), default="")
    names = {_institution_key(source.institution) for source in existing}
    homes: set[tuple[str, str, str]] = set()
    sources: list[Source] = []
    for row in sorted(rows, key=lambda row: (row.SCHL_NM, row.HMPG_ADDR or "")):
        if year != row.CRTR_YR or row.UNIV_SE_NM not in {"대학", "전문대학"}:
            continue
        key = _institution_key(row.SCHL_NM)
        url = _home_url(row.HMPG_ADDR or "")
        if not key or key in names or not url:
            continue
        parts = urlsplit(url)
        home = (
            (parts.hostname or "").removeprefix("www."),
            parts.path.rstrip("/"),
            parts.query,
        )
        if home in homes:
            continue
        names.add(key)
        homes.add(home)
        source_id = hashlib.sha256(key.encode()).hexdigest()[:12]
        name = " ".join(row.SCHL_NM.split())
        sources.append(
            Source(f"KCUE-registry-{source_id}", name, url, True, "university")
        )
    return tuple(sources)


def university_batch(
    sources: tuple[Source, ...], today: date, *, evening: bool
) -> tuple[Source, ...]:
    """Rotate through the full registry without concentrating a batch alphabetically."""
    batch_count = max(1, (len(sources) + DAILY_LIMIT - 1) // DAILY_LIMIT)
    batch = (today.toordinal() * 2 + evening) % batch_count
    return sources[batch::batch_count]


async def fetch_university_sources(
    client: httpx2.AsyncClient,
    existing: Iterable[Source],
) -> tuple[Source, ...]:
    metadata = await bounded_get(client, REGISTRY_METADATA_URL, 512_000)
    total = RegistryMetadata.model_validate_json(metadata.content).totalCount
    if not 0 < total <= 10000:
        return ()
    query = urlencode(
        {
            "publicDataPk": "15107736",
            "colNmList": REGISTRY_FIELDS,
            "totalCount": total,
            "svcTableNm": "tn_pubr_public_univ_info_svc",
            "perPage": 10000,
            "page": 1,
        },
        doseq=True,
    )
    response = await bounded_get(client, f"{REGISTRY_DOWNLOAD_URL}?{query}", 4_000_000)
    return university_sources(response.content, existing)
