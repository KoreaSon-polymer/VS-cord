from datetime import date

from tools.job_alert.deduplication import classify_postings
from tools.job_alert.models import JobPosting, SentRecord


def _posting(
    *, url: str, deadline: date, title: str = "박사후연구원 채용"
) -> JobPosting:
    return JobPosting(
        institution="KRICT",
        title=title,
        position="박사후연구원",
        employment_type="계약직",
        research_fields=("유기반도체",),
        qualifications="박사학위 소지자",
        location="대전",
        start_date=date(2026, 7, 20),
        deadline=deadline,
        url=url,
        first_seen=date(2026, 7, 26),
        previously_notified=False,
        fit_score=95,
        fit_reasons=("유기반도체", "박사후연구원"),
        change_note=None,
    )


def test_deduplicates_by_url_and_auxiliary_key() -> None:
    # Given
    existing = (
        SentRecord.from_posting(
            _posting(url="https://example.test/original", deadline=date(2026, 8, 10))
        ),
    )
    candidates = (
        _posting(url="https://example.test/original", deadline=date(2026, 8, 10)),
        _posting(url="https://mirror.test/copy", deadline=date(2026, 8, 10)),
    )

    # When
    result = classify_postings(candidates, existing)

    # Then
    assert result.new_postings == ()
    assert result.deduplicated_count == 2


def test_realerts_when_deadline_changes() -> None:
    # Given
    previous = _posting(url="https://example.test/job", deadline=date(2026, 8, 10))
    changed = _posting(url=previous.url, deadline=date(2026, 8, 17))

    # When
    result = classify_postings((changed,), (SentRecord.from_posting(previous),))

    # Then
    assert len(result.new_postings) == 1
    assert result.new_postings[0].previously_notified is True
    assert (
        result.new_postings[0].change_note
        == "접수 마감일 변경: 2026-08-10 → 2026-08-17"
    )
