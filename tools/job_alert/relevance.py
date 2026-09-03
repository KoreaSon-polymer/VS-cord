from __future__ import annotations

from datetime import date
from typing import Final

from .assessments import CareerIntelligenceAssessment
from .career_scoring import assess_career_advancement
from .models import JobPosting, PriorityLevel
from .research_fit import assess_research_fit
from .taxonomy import CATEGORY_RULES

RESEARCH_WEIGHT: Final = 0.6
CAREER_WEIGHT: Final = 0.4
APPLY_SERIOUSLY_SCORE: Final = 85
STRONGLY_CONSIDER_SCORE: Final = 70
MONITOR_SCORE: Final = 50


def priority_for_score(score: int, *, disqualified: bool) -> PriorityLevel:
    if disqualified or score < MONITOR_SCORE:
        return PriorityLevel.IGNORE
    if score >= APPLY_SERIOUSLY_SCORE:
        return PriorityLevel.APPLY_SERIOUSLY
    if score >= STRONGLY_CONSIDER_SCORE:
        return PriorityLevel.STRONGLY_CONSIDER
    return PriorityLevel.MONITOR


def assess_relevance(
    text: str,
    *,
    institution: str,
    researcher_level: bool,
) -> CareerIntelligenceAssessment:
    research = assess_research_fit(text, researcher_level=researcher_level)
    career = assess_career_advancement(
        text,
        institution,
        research_match=not research.disqualified,
    )
    final_score = round(
        (research.score * RESEARCH_WEIGHT) + (career.score * CAREER_WEIGHT)
    )
    priority = priority_for_score(final_score, disqualified=research.disqualified)
    return CareerIntelligenceAssessment(
        research_fit_score=research.score,
        career_advancement_score=career.score,
        final_score=final_score,
        priority=priority,
        research_fields=research.research_fields,
        fit_reasons=research.reasons,
        career_reasons=career.reasons,
        career_value=career.career_value,
        institution_score=career.institution_score,
        application_compatibility_score=career.compatibility_score,
    )


def recommended_profile_emphasis(
    research_fields: tuple[str, ...],
) -> tuple[str, ...]:
    emphases: list[str] = []
    for category in CATEGORY_RULES:
        if not any(category.name in field for field in research_fields):
            continue
        for emphasis in category.profile_emphasis:
            if emphasis not in emphases:
                emphases.append(emphasis)
    return tuple(emphases[:4])


def rank_postings(postings: tuple[JobPosting, ...]) -> tuple[JobPosting, ...]:
    return tuple(
        sorted(
            postings,
            key=lambda posting: (
                -posting.final_recommendation_score,
                -posting.career_advancement_score,
                -posting.research_fit_score,
                posting.deadline or date.max,
                posting.title.casefold(),
            ),
        )
    )
