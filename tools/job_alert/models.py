from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import StrEnum
from typing import Final

_SPACE_RE: Final = re.compile(r"\s+")
APPLY_SERIOUSLY_SCORE: Final = 85
STRONGLY_CONSIDER_SCORE: Final = 70
MONITOR_SCORE: Final = 50


def normalized(value: str) -> str:
    return _SPACE_RE.sub(" ", value).strip().casefold()


class PriorityLevel(StrEnum):
    APPLY_SERIOUSLY = "★★★★★ Apply seriously"
    STRONGLY_CONSIDER = "★★★★ Strongly consider"
    MONITOR = "★★★ Monitor"
    IGNORE = "Ignore"


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
    department: str = "원문 확인"
    research_fit_score: int = 0
    career_advancement_score: int = 0
    application_compatibility_score: int = 0
    institution_score: int = 0
    career_reasons: tuple[str, ...] = ()
    career_value: tuple[str, ...] = ()

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

    @property
    def priority(self) -> PriorityLevel:
        if self.fit_score >= APPLY_SERIOUSLY_SCORE:
            return PriorityLevel.APPLY_SERIOUSLY
        if self.fit_score >= STRONGLY_CONSIDER_SCORE:
            return PriorityLevel.STRONGLY_CONSIDER
        if self.fit_score >= MONITOR_SCORE:
            return PriorityLevel.MONITOR
        return PriorityLevel.IGNORE

    @property
    def final_recommendation_score(self) -> int:
        return self.fit_score

    def as_changed(self, note: str) -> JobPosting:
        return replace(self, previously_notified=True, change_note=note)

    @classmethod
    def test_payload(cls, today: date) -> JobPosting:
        return cls(
            institution="한국화학연구원 (KRICT)",
            title="[테스트] 유기반도체 박사후연구원 채용",
            position="박사후연구원",
            employment_type="계약직",
            research_fields=(
                "Organic semiconductor and organic electronics",
                "Polymer chemistry and organic materials synthesis",
                "Energy materials and electrochemistry",
            ),
            qualifications="관련 분야 박사학위 소지자",
            location="대전",
            start_date=today,
            deadline=date.fromordinal(today.toordinal() + 14),
            url="https://example.invalid/korean-research-job-alert-test",
            first_seen=today,
            previously_notified=False,
            fit_score=94,
            fit_reasons=(
                "Researcher-level role aligns with the target career stage",
                "Strong overlap with organic semiconductor and polymer synthesis",
                "Electrochemical-device experience can be emphasized",
            ),
            change_note=None,
            department="Advanced Materials Division",
            research_fit_score=100,
            career_advancement_score=86,
            application_compatibility_score=15,
            institution_score=15,
            career_reasons=(
                "Position level: Postdoctoral researcher (+5)",
                "Top research institution",
                "High compatibility: PhD requirement and research match",
            ),
            career_value=(
                "Publication potential follows the matched research domain",
                "Long-term value reflects position level and institution quality",
            ),
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
