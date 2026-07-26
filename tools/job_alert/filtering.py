from __future__ import annotations

import re
from datetime import date
from typing import Final

from .models import JobPosting, PriorityLevel, RawPosting
from .relevance import assess_relevance
from .taxonomy import POSITION_KEYWORDS as _POSITION_KEYWORDS

POSITION_KEYWORDS: Final = _POSITION_KEYWORDS
EXCLUDED_KEYWORDS: Final = (
    "합격자 발표",
    "합격자발표",
    "최종합격",
    "서류전형 결과",
    "면접 결과",
    "선정 결과",
    "선정결과",
    "입찰",
    "용역 공고",
    "사업 공고",
    "사업공고",
    "연구비",
    "신규과제",
    "지원사업",
    "과제 공모",
    "수혜자 모집",
)
LOCATIONS: Final = (
    "서울",
    "대전",
    "세종",
    "경기",
    "인천",
    "광주",
    "대구",
    "부산",
    "울산",
    "창원",
    "포항",
    "전북",
    "전남",
    "충북",
    "충남",
    "경북",
    "경남",
    "제주",
)
DATE_RE: Final = re.compile(r"(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})")
SHORT_END_DATE_RE: Final = re.compile(
    r"(20\d{2})[.\-/년]\s*\d{1,2}[.\-/월]\s*\d{1,2}\D{0,8}~\s*"
    + r"(\d{1,2})[.\-/월]\s*(\d{1,2})"
)
GENERIC_PAGE_TITLES: Final = (
    "개인정보처리방침",
    "채용안내",
    "채용 안내",
    "채용정보",
    "채용 정보",
    "채용공고",
    "인력채용 faq",
)
APPLICATION_DATE_MARKERS: Final = (
    "접수기간",
    "접수 기간",
    "접수마감",
    "접수 마감",
    "지원기간",
    "지원 기간",
    "모집기간",
    "모집 기간",
    "마감일",
)


def _dates(text: str) -> tuple[date, ...]:
    found: list[date] = []
    for match in DATE_RE.finditer(text):
        year, month, day = match.groups()
        try:
            found.append(date(int(year), int(month), int(day)))
        except ValueError:
            continue
    for match in SHORT_END_DATE_RE.finditer(text):
        year, month, day = match.groups()
        try:
            found.append(date(int(year), int(month), int(day)))
        except ValueError:
            continue
    return tuple(found)


def _first_match(text: str, values: tuple[str, ...], fallback: str) -> str:
    folded = text.casefold()
    return next((value for value in values if value.casefold() in folded), fallback)


def _application_dates(text: str) -> tuple[date, ...]:
    folded = text.casefold()
    for marker in APPLICATION_DATE_MARKERS:
        start = 0
        while (index := folded.find(marker.casefold(), start)) >= 0:
            dates = _dates(text[index : index + 260])
            if dates:
                return dates[:2]
            start = index + len(marker)
    return ()


def evaluate_posting(raw: RawPosting, today: date) -> JobPosting | None:
    combined = f"{raw.title} {raw.text}"
    folded = combined.casefold()
    title_folded = raw.title.casefold()
    excluded = any(keyword.casefold() in title_folded for keyword in EXCLUDED_KEYWORDS)
    generic = any(title_folded == title.casefold() for title in GENERIC_PAGE_TITLES)
    if excluded or generic:
        return None
    position = _first_match(raw.title, POSITION_KEYWORDS, "")
    if not position:
        return None
    assessment = assess_relevance(
        combined,
        institution=raw.institution,
        researcher_level=True,
    )
    if assessment.priority is PriorityLevel.IGNORE:
        return None
    parsed_dates = _dates(raw.title) or _application_dates(combined)
    if not parsed_dates and "채용시까지" not in folded:
        return None
    past_dates = tuple(item for item in parsed_dates if item <= today)
    future_dates = tuple(item for item in parsed_dates if item >= today)
    start_date = max(past_dates) if past_dates else None
    deadline = min(future_dates) if future_dates else None
    if parsed_dates and deadline is None:
        return None
    employment_type = _first_match(
        combined,
        ("정규직", "무기계약직", "계약직", "비정규직", "연수직"),
        "원문 확인",
    )
    location = _first_match(combined, LOCATIONS, "원문 확인")
    qualification_match = re.search(
        r"((?:지원|응시)\s*자격.{0,240}|박사학위.{0,160})", combined, re.IGNORECASE
    )
    qualifications = (
        qualification_match.group(1).strip() if qualification_match else "원문 확인"
    )
    department_match = re.search(
        r"((?:department of|학과|연구센터|연구단|연구실)\s*[\w가-힣 &/-]{2,80})",
        combined,
        re.IGNORECASE,
    )
    return JobPosting(
        institution=raw.institution,
        title=raw.title.strip(),
        position=position,
        employment_type=employment_type,
        research_fields=assessment.research_fields,
        qualifications=qualifications,
        location=location,
        start_date=start_date,
        deadline=deadline,
        url=raw.url,
        first_seen=today,
        previously_notified=False,
        fit_score=assessment.final_score,
        fit_reasons=assessment.fit_reasons,
        change_note=None,
        department=(
            department_match.group(1).strip() if department_match else "원문 확인"
        ),
        research_fit_score=assessment.research_fit_score,
        career_advancement_score=assessment.career_advancement_score,
        application_compatibility_score=assessment.application_compatibility_score,
        institution_score=assessment.institution_score,
        career_reasons=assessment.career_reasons,
        career_value=assessment.career_value,
    )
