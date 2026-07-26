from datetime import date

import pytest
from tools.job_alert.career_scoring import assess_career_advancement
from tools.job_alert.filtering import evaluate_posting
from tools.job_alert.models import JobPosting, RawPosting

TODAY = date(2026, 7, 26)


def _evaluate(institution: str, title: str, details: str = "") -> JobPosting | None:
    raw = RawPosting(
        institution=institution,
        title=title,
        url=f"https://example.test/{title.casefold().replace(' ', '-')}",
        text=(
            f"{title} {details} 접수기간 2026.07.20 ~ 2026.08.10 "
            "관련 분야 박사학위 소지자"
        ),
    )
    return evaluate_posting(raw, TODAY)


@pytest.mark.parametrize(
    ("institution", "title", "details"),
    [
        (
            "한국과학기술연구원 (KIST)",
            "Research professor in functional polymer materials",
            "independent research and PI responsibility",
        ),
        (
            "Seoul National University",
            "Assistant professor in organic materials chemistry",
            "tenure track faculty position and independent research",
        ),
        (
            "한국화학연구원 (KRICT)",
            "Senior researcher in semiconductor materials",
            "research leadership and project management",
        ),
        (
            "LG Energy Solution",
            "Research scientist in energy materials",
            "independent research and grant participation",
        ),
    ],
)
def test_high_value_positions_rank_at_least_strongly_consider(
    institution: str,
    title: str,
    details: str,
) -> None:
    # Given
    candidate_details = details

    # When
    posting = _evaluate(institution, title, candidate_details)

    # Then
    assert posting is not None
    assert posting.research_fit_score >= 50
    assert posting.career_advancement_score >= 50
    assert posting.final_recommendation_score >= 70
    assert posting.priority in ("★★★★★ Apply seriously", "★★★★ Strongly consider")


@pytest.mark.parametrize(
    "title",
    [
        "Battery materials researcher",
        "Electrochemical materials researcher",
    ],
)
def test_adjacent_materials_positions_are_monitor_priority(title: str) -> None:
    # Given
    institution = "Regional Research Center"

    # When
    posting = _evaluate(institution, title)

    # Then
    assert posting is not None
    assert 50 <= posting.final_recommendation_score <= 69
    assert posting.priority == "★★★ Monitor"


@pytest.mark.parametrize(
    "title",
    [
        "Mechanical engineer",
        "Administrative researcher",
        "Software engineer",
        "Biomedical researcher",
    ],
)
def test_unrelated_or_support_positions_are_rejected(title: str) -> None:
    # Given
    institution = "Example Institute"

    # When
    posting = _evaluate(institution, title)

    # Then
    assert posting is None


def test_excessive_industry_experience_requirement_reduces_compatibility() -> None:
    # Given
    details = "10 years semiconductor manufacturing industry experience required"

    # When
    posting = _evaluate(
        "Samsung Electronics",
        "Senior researcher in semiconductor materials",
        details,
    )

    # Then
    assert posting is not None
    assert posting.application_compatibility_score == 0


def test_domestic_postdoctoral_role_uses_low_career_level_weight() -> None:
    # Given
    text = "국내 박사후연구원 유기반도체 연구 관련 분야 박사학위 소지자"

    # When
    assessment = assess_career_advancement(
        text,
        "한국화학연구원 (KRICT)",
        research_match=True,
    )

    # Then
    assert assessment.position_score == 5


def test_final_recommendation_uses_sixty_forty_weighting() -> None:
    # Given
    posting = _evaluate(
        "한국화학연구원 (KRICT)",
        "Senior researcher in semiconductor materials",
        "research leadership",
    )

    # When
    assert posting is not None
    expected = round(
        (posting.research_fit_score * 0.6) + (posting.career_advancement_score * 0.4)
    )

    # Then
    assert posting.final_recommendation_score == expected
