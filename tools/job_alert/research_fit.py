from __future__ import annotations

from typing import Final

from .assessments import ResearchFitAssessment
from .negative_rules import NEGATIVE_RULES
from .research_rules import POSITIVE_RULES
from .taxonomy import CATEGORY_RULES

GENERAL_RULE_NAME: Final = "General chemistry / materials"
RESEARCH_SCORE_REFERENCE: Final = 18


def contains_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    folded = text.casefold()
    return any(keyword.casefold() in folded for keyword in keywords)


def assess_research_fit(text: str, *, researcher_level: bool) -> ResearchFitAssessment:
    categories = tuple(
        category
        for category in CATEGORY_RULES
        if contains_keyword(text, category.keywords)
    )
    positive = tuple(
        rule for rule in POSITIVE_RULES if contains_keyword(text, rule.keywords)
    )
    domain_positive = tuple(rule for rule in positive if rule.name != GENERAL_RULE_NAME)
    raw_score = sum(rule.weight for rule in positive)
    disqualified = not researcher_level or not domain_positive
    negative_reasons: list[str] = []
    for rule in NEGATIVE_RULES:
        if not contains_keyword(text, rule.keywords):
            continue
        if rule.unrelated_only and domain_positive:
            continue
        raw_score += rule.penalty
        disqualified = disqualified or rule.disqualifying
        negative_reasons.append(f"{rule.name} penalty ({rule.penalty})")
    score = max(0, min(100, round(raw_score * 100 / RESEARCH_SCORE_REFERENCE)))
    reasons = tuple(category.explanation for category in categories) + tuple(
        negative_reasons
    )
    return ResearchFitAssessment(
        score=score,
        research_fields=tuple(
            f"Tier {category.tier}: {category.name}" for category in categories
        ),
        reasons=reasons,
        disqualified=disqualified or score == 0,
    )
