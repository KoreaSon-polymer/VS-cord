from datetime import date

from tools.job_alert.filtering import evaluate_posting
from tools.job_alert.models import PriorityLevel, RawPosting


def test_rejects_non_job_result_and_funding_notices() -> None:
    # Given
    notices = (
        RawPosting(
            institution="KRICT",
            title="2026년도 신규과제 선정결과 공고",
            url="https://example.test/result",
            text="연구비 지원사업 선정 결과 및 합격자 발표",
        ),
        RawPosting(
            institution="KIST",
            title="2026년 연구사업 공고",
            url="https://example.test/funding",
            text="신규과제 연구비 지원 입찰 공고",
        ),
    )

    # When
    evaluated = tuple(evaluate_posting(item, date(2026, 7, 26)) for item in notices)

    # Then
    assert all(item is None for item in evaluated)


def test_accepts_relevant_open_postdoctoral_job() -> None:
    # Given
    raw = RawPosting(
        institution="한국화학연구원 (KRICT)",
        title="박사후연구원 채용 공고",
        url="https://example.test/postdoc",
        text=(
            "정규 채용 박사후연구원 Postdoctoral Researcher 유기반도체 "
            "고분자 반도체 전기화학 연구 대전 근무 "
            "접수기간 2026.07.20 ~ 2026.08.10 박사학위 소지자"
        ),
    )

    # When
    posting = evaluate_posting(raw, date(2026, 7, 26))

    # Then
    assert posting is not None
    assert posting.institution == "한국화학연구원 (KRICT)"
    assert posting.position == "박사후연구원"
    assert posting.deadline == date(2026, 8, 10)
    assert posting.location == "대전"
    assert posting.fit_score >= 80
    assert posting.priority is PriorityLevel.APPLY_SERIOUSLY
    assert any(
        "organic semiconductor" in reason.casefold() for reason in posting.fit_reasons
    )


def test_ignores_navigation_funding_terms_for_a_real_job_title() -> None:
    # Given
    raw = RawPosting(
        institution="KIMS",
        title="2026년 4차 박사후연구원 모집 공고",
        url="https://example.test/kims-postdoc",
        text=(
            "홈 연구사업 사업공고 입찰공고 채용공고 "
            "접수기간 2026.07.16 ~ 2026.08.02 재료화학 박사학위 소지자 창원"
        ),
    )

    # When
    posting = evaluate_posting(raw, date(2026, 7, 26))

    # Then
    assert posting is not None
    assert posting.deadline == date(2026, 8, 2)


def test_rejects_navigation_and_expired_titles_despite_detail_page_keywords() -> None:
    # Given
    notices = (
        RawPosting(
            institution="KERI",
            title="개인정보처리방침",
            url="https://example.test/privacy",
            text="채용공고 박사후연구원 연구직 2026.08.10",
        ),
        RawPosting(
            institution="KIER",
            title="2026년도 신규직원 채용(연구직)(2026. 6. 22. ~ 7. 7.)",
            url="https://example.test/expired",
            text="박사후연구원 관련 공지 다음 채용일 2026.08.10",
        ),
    )

    # When
    evaluated = tuple(evaluate_posting(item, date(2026, 7, 26)) for item in notices)

    # Then
    assert evaluated == (None, None)


def test_rejects_expired_application_period_before_later_navigation_date() -> None:
    # Given
    raw = RawPosting(
        institution="KIST",
        title="2026년 5월 연수직(Post-Doc.) 공개채용",
        url="https://example.test/kist-expired",
        text=(
            "2026년 5월 연수직(Post-Doc.) 공개채용 "
            "접수기간 2026.05.01 ~ 2026.05.15 "
            "다음 공고 접수기간 2026.08.01 ~ 2026.08.10"
        ),
    )

    # When
    posting = evaluate_posting(raw, date(2026, 7, 26))

    # Then
    assert posting is None
