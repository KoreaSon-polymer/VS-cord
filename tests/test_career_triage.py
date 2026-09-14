from datetime import date
import pytest
from tools.job_alert.models import RawPosting
from tools.job_alert.filtering import evaluate_posting
from tools.job_alert.triage import classify_notice, role_title_excluded, qualifications
from tools.job_alert.scraper import _candidate_links
from tools.job_alert.sources import Source, SOURCES
from tools.job_alert.discovery import board_links, nst_registry, notice_institution
from tools.research_monitor import to_opportunity, notification_events

TODAY = date(2026, 9, 14)
PERIOD = "\n접수기간 2026.09.01 ~ 2026.09.30"
def classify(title, body, **kw):
    return classify_notice(RawPosting("예시대학교", title, "https://example.test/notice?id=42",
                                     body, **kw), TODAY, evaluate_posting)

@pytest.mark.parametrize("title", ["화학 박사후연구원 모집", "고분자 석사후연구원 채용",
    "나노기술원 원장 초빙", "정규직 전환 가능한 Post-Doc 채용", "유기반도체 시간제 연구원 채용"])
def test_hard_exclusions(title):
    assert classify(title, "유기반도체 연구 정규직"+PERIOD) == ([], [])

@pytest.mark.parametrize("body", ["고용형태 비정규직", "고용형태 비 정규직", "직종 박사후연구원"])
def test_negative_employment_not_substring_positive(body):
    assert classify("유기반도체 연구원 모집", body+PERIOD) == ([], [])

def test_postdoc_experience_and_director_signature_do_not_exclude():
    accepted, review = classify("정규직 고분자 연구원 모집",
        "담당업무 공액고분자 합성\n박사후연구 경력 우대\n원장 명의 제출"+PERIOD)
    assert len(accepted) == 1 and not review

def test_missing_deadline_is_reviewed():
    accepted, review = classify("정규직 유기반도체 연구원 모집", "담당업무 고분자 합성")
    assert not accepted and len(review) == 1 and "접수 마감 미확인" in review[0]["action"]

def test_unknown_tenure_is_reviewed():
    accepted, review = classify("화학 전임교원 신규채용", "모집분야 유기반도체"+PERIOD)
    assert not accepted and len(review) == 1

def test_fixed_initial_contract_does_not_exclude_tenure():
    accepted, review = classify("화학 정년트랙 전임교원 초빙",
        "모집분야 유기반도체\n최초 계약기간 2년"+PERIOD)
    assert len(accepted) == 1 and not review

def test_unreadable_attachment_is_reviewed():
    accepted, review = classify("전임교원 신규채용", "첨부 참조"+PERIOD,
                               review_notes=("첨부 미확인",))
    assert not accepted and review

def test_mixed_notice_is_collected_and_reviewed():
    title = "정규직 연구원 및 박사후연구원 채용"
    assert not role_title_excluded(title)
    links = _candidate_links(Source("TEST", "기관", "https://example.test/board"),
                             '<a href="/notice?id=42">'+title+'</a>')
    assert len(links) == 1
    accepted, review = classify(title, "담당업무 유기반도체 연구"+PERIOD)
    assert not accepted and review

def test_role_codes_separate_permanent_postdoc_and_admin():
    body = "[R01] 정규직 연구원 유기반도체\n담당업무 고분자 합성\n박사학위\n[R02] 박사후연구원 광촉매\n담당업무 광촉매\n[A01] 정규직 행정원\n화학과 사무보조"+PERIOD
    accepted, review = classify("정규직 및 박사후연구원 채용", body)
    assert len(accepted) == 1 and accepted[0].role_id == "R01" and not review
    assert to_opportunity(accepted[0])["role_id"] == "R01"

def test_two_roles_at_same_url_have_distinct_identity():
    body = "[R01] 정규직 연구원 유기반도체\n담당업무 고분자 합성\n[R02] 정규직 연구원 전기화학\n담당업무 전기화학"+PERIOD
    accepted, review = classify("정규직 연구원 채용", body)
    ops = [to_opportunity(p) for p in accepted]
    assert len(ops) == 2 and len({o["key"] for o in ops}) == 2
    assert len(notification_events(ops, {"records":{}}, TODAY)) == 2

def test_qualification_keywords_do_not_make_unrelated_work_relevant():
    assert classify("정규직 연구원 모집",
        "담당업무 혈액 품질관리\n지원자격 화학 생화학 전문학사 이상"+PERIOD) == ([], [])

def test_no_fake_qualification_from_boilerplate():
    result = qualifications("지원자격 미달, 부정행위 시 응시 불가\n박사학위 취득 후 경력 년 이상")
    assert "불완전" in result and "부정행위" not in result

def test_board_discovery_does_not_use_login_or_anchor():
    links = board_links('<a href="#jobs">채용</a><a href="/login">교원채용</a><a href="/faculty">교수초빙</a>',
                        "https://example.test/")
    assert links == ["https://example.test/faculty"]

def test_nst_directory_adds_missing_institutes_only():
    sources = nst_registry('<a href="https://www.example.re.kr/">한국예시연구원</a>',
                           [Source("X","기존","https://www.kist.re.kr/")])
    assert len(sources) == 1 and sources[0].discover

def test_alio_source_is_not_institution_name():
    assert notice_institution(Source("JOB-ALIO","JOB-ALIO","https://job.alio.go.kr"),
        "채용", "<tr><th>기관명</th><td>예시연구원</td></tr>") == "예시연구원"

def test_registry_has_regions_and_unique_codes():
    assert len({s.institution for s in SOURCES if s.kind == "university"}) >= 60
    assert len({s.name for s in SOURCES}) == len(SOURCES)


@pytest.mark.parametrize("title", ["Non-tenure Track Faculty Position Opening", "Research Professor Position Opening"])
def test_english_temporary_faculty_is_excluded(title):
    assert classify(title, "organic semiconductor tenure-track"+PERIOD) == ([], [])

def test_korean_full_time_faculty_spelling():
    accepted, review = classify("전임직교원 공개초빙", "모집분야 유기반도체 정년트랙"+PERIOD)
    assert len(accepted) == 1 and not review


def test_scan_only_and_dry_run_never_send_or_mark_delivered(tmp_path, monkeypatch):
    import anyio
    import json
    from types import SimpleNamespace
    import tools.research_monitor as monitor
    from tools.job_alert.scraper import SourceResult
    monkeypatch.chdir(tmp_path)
    (tmp_path/"tools").mkdir()
    async def collect():
        raw = RawPosting("예시연구원", "정규직 유기반도체 연구원 채용",
                         "https://example.test/42", "담당업무 고분자 합성\n상시채용")
        return (SourceResult("EX", (raw,), None, 1, 0, "예시연구원",
                             "https://example.test", "institute"),)
    monkeypatch.setattr(monitor, "collect_sources", collect)
    monkeypatch.setattr(monitor, "collect_funding", lambda: ([], []))
    def forbidden(*args):
        raise AssertionError("A preview or collection-only run attempted SMTP")
    monkeypatch.setattr(monitor, "send_email", forbidden)
    assert anyio.run(monitor.run, {"DRY_RUN":"true"}) == 0
    assert not monitor.STATE_PATH.exists()
    assert anyio.run(monitor.run, {"SEND_DIGEST":"false"}) == 0
    state = json.loads(monitor.STATE_PATH.read_text())
    assert len(state["pending"]) == 1 and state["records"] == {}
    original = monitor.STATE_PATH.read_text()
    assert anyio.run(monitor.run, {"DRY_RUN":"true"}) == 0
    assert monitor.STATE_PATH.read_text() == original


def test_mobile_and_paginated_notice_identity():
    from tools.notice_utils import canonical_url
    assert canonical_url("https://job.alio.go.kr/mobile2021/recruit/recruitView.do?idx=42") == canonical_url("https://job.alio.go.kr/recruitview.do?idx=42")
    assert canonical_url("https://www.kims.re.kr/board.php?wr_id=42&page=1") == canonical_url("https://www.kims.re.kr/board.php?page=2&wr_id=42")
    assert canonical_url("https://example.test/board?page=1") != canonical_url("https://example.test/board?page=2")

@pytest.mark.parametrize('title', [
    "[부산앵커센터] 찾아가는 굿잡 버스 참가 모집 안내",
    "2027학년도 수시모집 경쟁률 발표",
    "연구팀, 줄기세포 recruitment를 이용한 신소재 개발",
    "학습지원 프로그램 튜터 모집 안내",
    "2026년 하반기 부연구단장 공개 모집",
    "정규직 채용 발표전형 결과 및 3단계 전형 안내",
    "신소재 연구직(이노코어 펠로우) 채용 공고",
])
def test_live_discovery_false_positives_are_not_jobs(title):
    assert classify(title, '정규직 유기반도체 연구원'+PERIOD) == ([], [])


def test_old_unknown_deadline_notice_not_new_review():
    assert classify('2024년 정규직 연구원 공개채용', '고분자 연구 첨부 확인 필요') == ([], [])


def test_attachment_number_is_not_a_role_code():
    from tools.job_alert.triage import split_roles
    raw = RawPosting('대학', '전임교원 신규채용', 'https://example.test/1',
        '[1] 교수초빙지원서.hwp\n[2] 연구계획서.pdf\n모집분야 화학')
    assert split_roles(raw) == [raw]


@pytest.mark.parametrize('title', [
    'KAIST 경영공학부 회계 분야 전임직 교원 채용 공고',
    'KAIST Full-time EFL Faculty Opening',
])
def test_explicit_unrelated_field_not_rescued_by_attachment(title):
    assert classify(title, '모집분야 첨부파일 참조'+PERIOD) == ([], [])
