from dataclasses import replace
from datetime import date

from tools.job_alert.filtering import evaluate_posting
from tools.job_alert.models import JobPosting, RawPosting
from tools.job_alert.relevance import rank_postings

TODAY = date(2026, 7, 26)


def _evaluate(title: str) -> JobPosting | None:
    raw = RawPosting(
        institution="Example Institute",
        title=title,
        url=f"https://example.test/{title.casefold().replace(' ', '-')}",
        text=f"{title} 접수기간 2026.07.20 ~ 2026.08.10",
    )
    return evaluate_posting(raw, TODAY)


def test_functional_polymer_materials_postdoc_passes() -> None:
    # Given
    title = "Functional polymer materials postdoctoral researcher"

    # When
    posting = _evaluate(title)

    # Then
    assert posting is not None
    assert posting.fit_score >= 45


def test_organic_synthesis_researcher_passes() -> None:
    # Given
    title = "Organic synthesis researcher"

    # When
    posting = _evaluate(title)

    # Then
    assert posting is not None
    assert posting.fit_score >= 45


def test_advanced_energy_materials_researcher_passes() -> None:
    # Given
    title = "Advanced energy materials researcher"

    # When
    posting = _evaluate(title)

    # Then
    assert posting is not None
    assert posting.fit_score >= 45


def test_mechanical_engineer_fails() -> None:
    # Given
    title = "Mechanical engineer"

    # When
    posting = _evaluate(title)

    # Then
    assert posting is None


def test_administrative_researcher_support_fails() -> None:
    # Given
    title = "Administrative researcher support"

    # When
    posting = _evaluate(title)

    # Then
    assert posting is None


def test_battery_materials_scientist_is_monitor_priority() -> None:
    # Given
    title = "Battery materials scientist"

    # When
    posting = _evaluate(title)

    # Then
    assert posting is not None
    assert posting.priority == "★★★ Monitor"
    assert 50 <= posting.final_recommendation_score <= 69


def test_polymer_semiconductor_researcher_is_strongly_considered() -> None:
    # Given
    title = "Polymer semiconductor researcher"

    # When
    posting = _evaluate(title)

    # Then
    assert posting is not None
    assert posting.priority in (
        "★★★★★ Apply seriously",
        "★★★★ Strongly consider",
    )
    assert posting.final_recommendation_score >= 70


def test_ranking_places_stronger_final_score_first() -> None:
    # Given
    baseline = JobPosting.test_payload(TODAY)
    worth_checking = replace(
        baseline,
        title="Battery materials scientist",
        fit_score=48,
    )
    apply_seriously = replace(
        baseline,
        title="Polymer semiconductor researcher",
        fit_score=70,
    )

    # When
    ranked = rank_postings((worth_checking, apply_seriously))

    # Then
    assert tuple(posting.title for posting in ranked) == (
        "Polymer semiconductor researcher",
        "Battery materials scientist",
    )
