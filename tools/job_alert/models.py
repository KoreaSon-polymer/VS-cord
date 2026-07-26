from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Final

_SPACE_RE: Final = re.compile(r"\s+")


def normalized(value: str) -> str:
    return _SPACE_RE.sub(" ", value).strip().casefold()


@dataclass(frozen=True, slots=True)
class RawPosting:
    institution: str
    title: str
    url: str
    text: str


@dataclass(frozen=True, slots=True)
class JobPosting:
    institution: str
    title: str
    position: str
    employment_type: str
    research_fields: tuple[str, ...]
    qualifications: str
    location: str
    start_date: date | None
    deadline: date | None
    url: str
    first_seen: date
    previously_notified: bool
    fit_score: int
    fit_reasons: tuple[str, ...]
    change_note: str | None

    @property
    def url_key(self) -> str:
        return normalized(self.url).rstrip("/")

    @property
    def auxiliary_key(self) -> str:
        period = f"{self.start_date or ''}|{self.deadline or ''}"
        raw = f"{self.institution}|{self.title}|{period}"
        return hashlib.sha256(normalized(raw).encode()).hexdigest()[:20]

    @property
    def content_hash(self) -> str:
        raw = "|".join(
            (
                self.institution,
                self.title,
                self.position,
                self.employment_type,
                ",".join(self.research_fields),
                self.qualifications,
                self.location,
                str(self.start_date),
                str(self.deadline),
            )
        )
        return hashlib.sha256(normalized(raw).encode()).hexdigest()

    def as_changed(self, note: str) -> JobPosting:
        return replace(self, previously_notified=True, change_note=note)

    @classmethod
    def test_payload(cls, today: date) -> JobPosting:
        return cls(
            institution="한국화학연구원 (KRICT)",
            title="[테스트] 유기반도체 박사후연구원 채용",
            position="박사후연구원",
            employment_type="계약직",
            research_fields=("유기반도체", "고분자 반도체", "전기화학"),
            qualifications="관련 분야 박사학위 소지자",
            location="대전",
            start_date=today,
            deadline=date.fromordinal(today.toordinal() + 14),
            url="https://example.invalid/korean-research-job-alert-test",
            first_seen=today,
            previously_notified=False,
            fit_score=100,
            fit_reasons=("유기반도체", "고분자 반도체", "박사후연구원"),
            change_note=None,
        )


@dataclass(frozen=True, slots=True)
class SentRecord:
    url_key: str
    auxiliary_key: str
    content_hash: str
    deadline: date | None

    @classmethod
    def from_posting(cls, posting: JobPosting) -> SentRecord:
        return cls(
            url_key=posting.url_key,
            auxiliary_key=posting.auxiliary_key,
            content_hash=posting.content_hash,
            deadline=posting.deadline,
        )


@dataclass(frozen=True, slots=True)
class RunMetrics:
    sources_attempted: int
    collected_count: int
    new_count: int
    deduplicated_count: int
    excluded_count: int
    source_errors: tuple[str, ...]
    collected_at: datetime
    email_status: str
