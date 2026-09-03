from __future__ import annotations

from dataclasses import dataclass

from .models import PriorityLevel


@dataclass(frozen=True, slots=True)
class ResearchFitAssessment:
    score: int
    research_fields: tuple[str, ...]
    reasons: tuple[str, ...]
    disqualified: bool


@dataclass(frozen=True, slots=True)
class CareerAssessment:
    score: int
    position_score: int
    independence_score: int
    institution_score: int
    compatibility_score: int
    reasons: tuple[str, ...]
    career_value: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CareerIntelligenceAssessment:
    research_fit_score: int
    career_advancement_score: int
    final_score: int
    priority: PriorityLevel
    research_fields: tuple[str, ...]
    fit_reasons: tuple[str, ...]
    career_reasons: tuple[str, ...]
    career_value: tuple[str, ...]
    institution_score: int
    application_compatibility_score: int
