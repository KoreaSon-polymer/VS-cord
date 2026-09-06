from __future__ import annotations

import re
from datetime import date

from tools.notice_utils import application_period, matches, research_matches
from .models import JobPosting, RawPosting

POSITION_KEYWORDS = ("전임교원", "전임 교원", "전임교수", "교수 초빙", "교수초빙", "교원", "정년트랙", "정년 트랙", "정규직", "정규 연구직", "연구직", "선임연구원", "tenure-track", "faculty", "permanent")
INTEREST_KEYWORDS = ("유기반도체", "고분자", "광촉매", "전기화학", "신소재", "화학")
EXCLUDED_KEYWORDS = ("합격자 발표", "합격자발표", "최종합격", "합격자", "매뉴얼", "서류전형 결과", "면접 결과", "입찰", "연구비", "신규과제", "지원사업", "선정결과")
EXCLUDED_ROLES = re.compile(r"박사\s*후|포닥|post[\s-]?doc|연수직|연수연구원|위촉|기간제|계약직|비정규|비\s*전임|비\s*정년|연구교수|연구교원|산학교수|겸임|객원|강사|초빙교수|특임|석좌|(?:원장|총장|이사장|기관장|소장|CEO|대표이사)\s*(?:초빙|공모|채용|모집)", re.I)
FACULTY = re.compile(r"(?<!비)전임\s*(?:교원|교수)|(?<!비)정년\s*트랙|tenure[ -]?track|assistant professor", re.I)
PERMANENT = re.compile(r"(?<!비)정규\s*직|정규\s*연구직|permanent", re.I)
LOCATIONS = ("서울", "대전", "세종", "경기", "인천", "광주", "대구", "부산", "울산", "창원", "포항", "전북", "전남", "충북", "충남", "경북", "경남", "제주")


def evaluate_posting(raw: RawPosting, today: date) -> JobPosting | None:
    title = re.sub(r"\s+", " ", raw.title).strip()
    combined = title + "\n" + raw.text
    if EXCLUDED_ROLES.search(title) or matches(title, EXCLUDED_KEYWORDS):
        return None
    if not re.search(r"채용|초빙|모집|임용|recruit|position|opening", title, re.I):
        return None
    if "상세 페이지 접근 실패" in raw.text:
        return None
    # Positive employment evidence is mandatory; 비정규직 must never match 정규직.
    faculty = bool(FACULTY.search(title) or FACULTY.search(raw.text))
    permanent = bool(PERMANENT.search(title) or PERMANENT.search(raw.text))
    if re.search(r"비\s*정년", combined) and not re.search(r"(?<!비)정년\s*트랙|tenure[ -]?track", combined, re.I):
        return None
    if not (faculty or permanent):
        return None
    # Generic titles require an unambiguous permanent role in the body.
    if not (FACULTY.search(title) or PERMANENT.search(title)) and EXCLUDED_ROLES.search(raw.text[:1200]):
        return None
    if not faculty and not re.search(r"연구직|연구원|연구분야|연구 분야|research", combined, re.I):
        return None
    fields = research_matches(combined)
    if not fields:
        return None
    start_date, deadline, _ = application_period(raw.text, title)
    if deadline and deadline < today:
        return None
    # Ongoing recruitment is useful; unlabeled dates are never substituted.
    if not deadline and not re.search(r"채용\s*시까지|상시\s*(?:채용|초빙|모집)|연중\s*(?:채용|초빙)|until filled|rolling", combined, re.I):
        return None
    if faculty:
        position, employment = "전임교원 신규 임용", "전임교원 (정년트랙 여부 원문 확인)"
        if re.search(r"(?<!비)정년\s*트랙|tenure[ -]?track", combined, re.I):
            employment = "정년트랙 전임교원"
    else:
        position, employment = "정규 연구직", "정규직"
    qualification = re.search(r"(?:관련\s*(?:분야)?\s*)?박사\s*학위[^\n]{0,220}|(?:학력|학위)\s*(?:요건|조건)[^\n]{0,220}", raw.text) or re.search(r"(?:지원|응시|공통)\s*자격[\s\S]{0,350}|박사\s*학위[\s\S]{0,200}", raw.text)
    return JobPosting(
        institution=raw.institution, title=title, position=position, employment_type=employment,
        research_fields=fields, qualifications=re.sub(r"\s+", " ", qualification.group(0)) if qualification else "세부 학위·경력·논문 요건 원문 확인",
        location=next((v for v in LOCATIONS if v in combined), "원문 확인"),
        start_date=start_date, deadline=deadline, url=raw.url, first_seen=today,
        previously_notified=False, fit_score=min(100, 55 + 10 * len(fields)),
        fit_reasons=fields + (position,), change_note=None,
    )
