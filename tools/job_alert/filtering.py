from __future__ import annotations

import re
from datetime import date
from typing import Final

from .models import JobPosting, RawPosting

POSITION_KEYWORDS: Final = (
    "박사후연구원",
    "박사후 연구원",
    "postdoctoral researcher",
    "post-doc",
    "postdoc",
    "연구교수",
    "research professor",
    "책임연구원",
    "principal researcher",
    "선임연구원",
    "senior researcher",
    "전임연구원",
    "정규직 연구",
    "연구직",
    "위촉연구원",
    "석사후연구원",
)
INTEREST_KEYWORDS: Final = (
    "유기반도체",
    "고분자 반도체",
    "광촉매",
    "수소 생산",
    "수소생산",
    "수소 센서",
    "전기화학",
    "유기전자",
    "omiec",
    "oect",
    "n-type sam",
    "계면 전하이동",
    "계면 전하 이동",
    "광전소자",
    "소자물리",
    "재료화학",
)
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
    if any(keyword.casefold() in title_folded for keyword in EXCLUDED_KEYWORDS):
        return None
    if any(title_folded == title.casefold() for title in GENERIC_PAGE_TITLES):
        return None
    position = _first_match(raw.title, POSITION_KEYWORDS, "")
    if not position:
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
    fields = tuple(
        keyword for keyword in INTEREST_KEYWORDS if keyword.casefold() in folded
    )
    reasons = fields + ((position,) if position else ())
    score = min(100, 35 + (15 * len(fields)) + (15 if "박사" in folded else 0))
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
    return JobPosting(
        institution=raw.institution,
        title=raw.title.strip(),
        position=position,
        employment_type=employment_type,
        research_fields=fields or ("세부 연구 분야 원문 확인",),
        qualifications=qualifications,
        location=location,
        start_date=start_date,
        deadline=deadline,
        url=raw.url,
        first_seen=today,
        previously_notified=False,
        fit_score=score,
        fit_reasons=reasons,
        change_note=None,
    )
