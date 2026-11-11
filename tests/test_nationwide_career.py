import json
from datetime import date, timedelta

import anyio
import httpx2
import pytest
from tools.job_alert.discovery import normalize_aggregate_text, notice_institution
from tools.job_alert.filtering import evaluate_posting
from tools.job_alert.http_client import create_async_client
from tools.job_alert.models import RawPosting
from tools.job_alert.national_registry import university_batch, university_sources
from tools.job_alert.scraper import _candidate_links, forwarded_notice
from tools.job_alert.sources import SOURCES, Source
from tools.job_alert.triage import classify_notice
from tools.notice_utils import application_period
from tools.research_monitor import notification_events

TODAY = date(2026, 11, 11)
TITLE = "정규직 유기반도체 연구원 채용"
BODY = "담당업무: 공액 고분자 합성\n접수기간 2026.11.01 ~ 2026.11.30\n"


@pytest.mark.parametrize(
    ("requirement", "eligible"),
    [
        ("지원자격: 관련 분야 박사학위 소지자", True),
        ("지원자격: 관련 분야 박사학위 소지자\n우대사항: 경력 3년 이상", True),
        ("지원자격: 관련 분야 박사학위 소지자\n박사학위 취득 후 경력 3년 이상", False),
        ("지원자격: 관련 분야 박사학위 소지자 및 SCIE 논문 3편 이상", False),
        ("지원자격: 관련 분야 박사학위 취득 예정자에 한함", False),
        ("지원자격: 박사학위 소지자\n대한민국 국적을 가진 자", False),
        ("지원자격: 박사학위 소지자\n최근 3년간 SCI 논문 주저자 3편", False),
        (
            "지원자격: 박사학위 소지자\n박사학위 취득 후 경력 3년 이상, 고분자 분야 우대",
            False,
        ),
        (
            "지원자격: 박사학위 소지자\n우대사항: 분석 경험\n별도 제출 필수: 경력 5년 이상",
            False,
        ),
        ("지원자격: 박사학위 소지자\n화학 전공자 지원 불가", False),
        ("지원자격: 재료공학 박사학위 소지자", False),
        ("지원자격: 박사학위 소지자\n접수일 현재 국내 대학에 소속된 자", False),
        ("지원자격: 박사학위 소지자\n산업체에서 근무한 경험이 있는 자", False),
        ("담당업무: 공액 고분자 합성 및 박사학위 소지 연구원 지도", False),
        ("지원자격: 박사학위 소지자\n전임교원 경력자", False),
        ("제출서류: 박사학위 소지 증명서", False),
        ("학위 및 경력은 첨부 참조", False),
    ],
)
def test_email_triage_requires_evidence_of_known_requirements(
    requirement: str,
    *,
    eligible: bool,
) -> None:
    raw = RawPosting(
        "한국예시연구원", TITLE, "https://example.test/1", BODY + requirement
    )
    accepted, reviews = classify_notice(
        raw,
        TODAY,
        evaluate_posting,
        require_eligibility=True,
    )
    assert bool(accepted) is eligible
    assert bool(reviews) is not eligible


def test_unresolved_legacy_job_never_creates_a_mail_event() -> None:
    review = {"kind": "job", "review": True}
    assert notification_events([review], {"records": {}}, TODAY) == []


def test_nrc_recruitment_is_monitored() -> None:
    assert any(source.name.startswith("NRC-") for source in SOURCES)


def test_results_announcement_is_skipped_at_discovery() -> None:
    page = Source("TEST", "예시대학교", "https://example.test/board")
    markup = (
        '<a href="/42">Faculty Recruitment: Announcement of Final Selection Results</a>'
    )
    assert _candidate_links(page, markup) == ()


def test_cancelled_job_with_future_nominal_deadline_is_excluded() -> None:
    body = BODY + "지원자격: 박사학위 소지자\n채용 취소: 이 공고는 취소되었습니다."
    raw = RawPosting("한국예시연구원", TITLE, "https://example.test/1", body)
    assert classify_notice(raw, TODAY, evaluate_posting, require_eligibility=True) == (
        [],
        [],
    )


@pytest.mark.parametrize(
    "status", ["접수 상태: 접수 종료", "공고상태: 취소", "접수상태: 마감"]
)
def test_closed_status_overrides_the_listed_deadline(status: str) -> None:
    raw = RawPosting(
        "한국예시연구원",
        TITLE,
        "https://example.test/1",
        BODY + "지원자격: 박사학위 소지자\n" + status,
    )
    assert classify_notice(raw, TODAY, evaluate_posting, require_eligibility=True) == (
        [],
        [],
    )


def test_temporary_role_with_conversion_does_not_qualify() -> None:
    body = BODY + "지원자격: 박사학위 소지자\n근무형태: 계약직 (정규직 전환 가능)"
    raw = RawPosting(
        "한국예시연구원", "유기반도체 연구원 채용", "https://example.test/1", body
    )
    assert classify_notice(raw, TODAY, evaluate_posting, require_eligibility=True) == (
        [],
        [],
    )


def test_unannounced_opening_is_held_for_review() -> None:
    body = BODY + "지원자격: 박사학위 소지자\n접수 시작일은 추후 공지합니다."
    raw = RawPosting("한국예시연구원", TITLE, "https://example.test/1", body)
    accepted, review = classify_notice(
        raw, TODAY, evaluate_posting, require_eligibility=True
    )
    assert not accepted and review


def test_other_roles_degree_does_not_qualify_a_job() -> None:
    body = (
        "직무별 지원자격은 아래와 같습니다.\nB2: 박사학위 소지자\n"
        "[A1] 정규직 연구원 광촉매\n담당업무: 광촉매 합성\n"
        "[B2] 정규직 연구원 유기반도체\n지원자격: 박사학위 소지자\n" + BODY
    )
    raw = RawPosting("한국예시연구원", TITLE, "https://example.test/1", body)
    accepted, review = classify_notice(
        raw, TODAY, evaluate_posting, require_eligibility=True
    )
    assert [posting.role_id for posting in accepted] == ["B2"]
    assert [op["role_id"] for op in review] == ["A1"]


def test_registry_rotates_all_latest_additional_sites_over_both_slots() -> None:
    rows = [
        {
            "SCHL_NM": f"예시대학교{i}",
            "HMPG_ADDR": f"campus{i}.ac.kr",
            "UNIV_SE_NM": "대학",
            "CRTR_YR": "2025",
        }
        for i in range(102)
    ]
    rows.append({**rows[0], "CRTR_YR": "2024"})
    rows.append({**rows[0], "SCHL_NM": "대학원", "UNIV_SE_NM": "대학원"})
    rows.append({**rows[0], "SCHL_NM": "잘못된주소", "HMPG_ADDR": "http://127.0.0.1"})
    known = Source("TEST", "국립예시대학교0", "https://campus0.ac.kr/")
    registry = university_sources(json.dumps(rows).encode(), (known,))
    slots = (
        (TODAY, False),
        (TODAY, True),
        (TODAY + timedelta(days=1), False),
    )
    batches = [
        university_batch(registry, day, evening=evening) for day, evening in slots
    ]
    assert len(registry) == 101
    assert max(map(len, batches)) <= 40
    assert {source for batch in batches for source in batch} == set(registry)


def test_job_alio_self_closing_anchor_and_two_digit_period() -> None:
    source = next(source for source in SOURCES if source.name == "JOB-ALIO-regular-1")
    link = (
        '<td class="left"><a href="recruitView.do?x=2&amp;idx=42"/>'
        + TITLE
        + "</a></td>"
    )
    assert _candidate_links(source, link)[0][1].endswith("idx=42&x=2")
    dates = normalize_aggregate_text(
        source, "채용기간 26.11.01 ~ 26.11.30 등록일 2026.11.01"
    )
    assert application_period(dates)[:2] == (date(2026, 11, 1), date(2026, 11, 30))


def test_nrc_follows_institution_notice_from_official_metadata() -> None:
    source = next(source for source in SOURCES if source.name == "NRC-1")
    original = "https://example.ac.kr/board?list_no=42"
    markup = (
        '<div class="tstyle_view"><ul class="head">'
        "<li><strong>채용기관</strong><span>예시연구원</span></li>"
        f'<li><strong>URL</strong><span><a href="{original}">{original}</a></span></li>'
        "</ul></div>"
    )
    assert notice_institution(source, TITLE, markup) == "예시연구원"
    assert forwarded_notice(source, markup) == ("예시연구원", original)


def test_public_crawler_cannot_connect_to_a_loopback_address() -> None:
    async def request_local() -> None:
        async with create_async_client(public_only=True) as client:
            await client.get("http://127.0.0.1/")

    with pytest.raises(httpx2.ConnectError, match="public address"):
        anyio.run(request_local)
