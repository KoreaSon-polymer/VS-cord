from datetime import date, datetime, timedelta, timezone

from tools.job_alert.models import JobPosting, RunMetrics
from tools.job_alert.reporting import build_email


def test_test_email_contains_required_sections_and_marker() -> None:
    # Given
    posting = JobPosting.test_payload(date(2026, 7, 26))
    metrics = RunMetrics(
        sources_attempted=20,
        collected_count=12,
        new_count=1,
        deduplicated_count=3,
        excluded_count=8,
        source_errors=("ETRI: 접근 실패",),
        collected_at=datetime(
            2026,
            7,
            26,
            9,
            30,
            tzinfo=timezone(timedelta(hours=9), name="KST"),
        ),
        email_status="sent",
    )

    # When
    email = build_email((posting,), metrics, is_test=True)

    # Then
    assert (
        email.subject == "[TEST] [Korean Research Job Alert] 신규 공고 1건 · 2026-07-26"
    )
    assert "마감 임박 공고" in email.text_body
    assert "높은 적합도 공고" in email.text_body
    assert "전체 신규 공고 목록" in email.text_body
    assert "중복 제외: 3건" in email.text_body
    assert "ETRI: 접근 실패" in email.text_body
    assert "Priority: ★★★★★ Apply seriously" in email.text_body
    assert "Research Fit Score: 100/100" in email.text_body
    assert "Career Advancement Score: 86/100" in email.text_body
    assert "Final Recommendation Score: 94/100" in email.text_body
    assert "Why this fits:" in email.text_body
    assert "Recommended application strategy:" in email.text_body
    assert "Career value:" in email.text_body
