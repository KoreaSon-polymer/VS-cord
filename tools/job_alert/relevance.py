from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final

from .models import APPLY_SERIOUSLY_SCORE, JobPosting, PriorityLevel
from .taxonomy import CATEGORY_RULES, GENERAL_CHEMISTRY_MATERIALS, KeywordCategory

RESEARCHER_LEVEL_SCORE: Final = 20
DIRECT_MATCH_SCORE: Final = 15
MINIMUM_RELEVANT_SCORE: Final = 45


@dataclass(frozen=True, slots=True)
class WeightedKeywordRule:
    name: str
    weight: int
    keywords: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NegativeKeywordRule:
    name: str
    penalty: int
    keywords: tuple[str, ...]
    disqualifying: bool
    unrelated_only: bool = False


@dataclass(frozen=True, slots=True)
class RelevanceAssessment:
    score: int
    priority: PriorityLevel
    research_fields: tuple[str, ...]
    reasons: tuple[str, ...]


POSITIVE_RULES: Final = (
    WeightedKeywordRule(
        "Organic semiconductor / organic electronics",
        15,
        (
            "organic semiconductor",
            "organic electronics",
            "organic optoelectronics",
            "organic photovoltaic",
            "conjugated polymer",
            "polymer semiconductor",
            "semiconducting polymer",
            "유기반도체",
            "유기전자",
            "유기광전자",
            "공액고분자",
            "고분자 반도체",
        ),
    ),
    WeightedKeywordRule(
        "Polymer synthesis / polymer chemistry",
        12,
        (
            "polymer synthesis",
            "polymer chemistry",
            "polymer semiconductor",
            "functional polymer",
            "macromolecular chemistry",
            "monomer synthesis",
            "고분자 합성",
            "고분자 화학",
            "고분자 반도체",
            "기능성 고분자",
            "단량체 합성",
        ),
    ),
    WeightedKeywordRule(
        "Organic synthesis / functional molecules",
        10,
        (
            "organic synthesis",
            "molecular design",
            "functional molecules",
            "organic materials",
            "유기합성",
            "분자설계",
            "기능성 분자",
            "유기소재",
        ),
    ),
    WeightedKeywordRule(
        "Advanced materials chemistry",
        10,
        (
            "advanced materials",
            "functional materials",
            "smart materials",
            "nanomaterials",
            "materials chemistry",
            "materials science",
            "첨단소재",
            "기능성 소재",
            "나노소재",
            "소재화학",
            "재료화학",
            "신소재",
        ),
    ),
    WeightedKeywordRule(
        "Energy materials",
        8,
        (
            "energy materials",
            "energy conversion",
            "energy storage",
            "battery materials",
            "fuel cell",
            "electrode materials",
            "에너지 소재",
            "에너지 변환",
            "에너지 저장",
            "배터리 소재",
            "연료전지",
            "전극 소재",
        ),
    ),
    WeightedKeywordRule(
        "Electrochemistry",
        8,
        (
            "electrochemistry",
            "electrochemical materials",
            "electrochemical device",
            "electrocatalysis",
            "전기화학",
            "전기화학 소재",
            "전기촉매",
        ),
    ),
    WeightedKeywordRule(
        "Photocatalysis",
        10,
        ("photocatalysis", "photocatalytic", "광촉매"),
    ),
    WeightedKeywordRule(
        "Hydrogen energy",
        8,
        (
            "hydrogen energy",
            "hydrogen production",
            "hydrogen evolution",
            "water splitting",
            "hydrogen sensor",
            "수소 생산",
            "수소생산",
            "수소 센서",
            "수전해",
        ),
    ),
    WeightedKeywordRule(
        "Photoelectrochemistry",
        10,
        ("photoelectrochemistry", "photoelectrochemical", "광전기화학"),
    ),
    WeightedKeywordRule(
        "Semiconductor materials",
        8,
        (
            "semiconductor materials",
            "polymer semiconductor",
            "molecular semiconductor",
            "반도체 소재",
            "고분자 반도체",
        ),
    ),
    WeightedKeywordRule(
        "Device physics / thin-film devices",
        8,
        (
            "device physics",
            "thin film device",
            "thin-film device",
            "thin film transistor",
            "device fabrication",
            "optoelectronic device",
            "소자물리",
            "박막트랜지스터",
            "소자 제작",
            "광전자 소자",
            "광전소자",
        ),
    ),
    WeightedKeywordRule(
        "Sensor materials",
        6,
        (
            "sensor materials",
            "chemical sensor",
            "gas sensor",
            "hydrogen sensor",
            "센서 소재",
            "가스센서",
            "수소 센서",
        ),
    ),
    WeightedKeywordRule(
        "Interface engineering / charge transport",
        8,
        (
            "interface engineering",
            "interface physics",
            "charge transfer",
            "charge transport",
            "carrier mobility",
            "n-type sam",
            "계면제어",
            "계면 물리",
            "계면 전하이동",
            "계면 전하 이동",
            "전하 이동",
        ),
    ),
    WeightedKeywordRule(
        "General chemistry / materials",
        5,
        GENERAL_CHEMISTRY_MATERIALS.keywords,
    ),
)

NEGATIVE_RULES: Final = (
    NegativeKeywordRule(
        "Administrative",
        -50,
        ("administrative", "administration", "research support", "행정", "연구지원"),
        disqualifying=True,
    ),
    NegativeKeywordRule(
        "Accounting",
        -50,
        ("accounting", "finance officer", "회계", "재무"),
        disqualifying=True,
    ),
    NegativeKeywordRule(
        "HR",
        -50,
        ("human resources", "hr specialist", "인사담당", "인사 관리"),
        disqualifying=True,
    ),
    NegativeKeywordRule(
        "Facility management",
        -40,
        ("facility management", "facilities manager", "시설관리", "시설 관리"),
        disqualifying=False,
    ),
    NegativeKeywordRule(
        "Technician-only",
        -30,
        ("technician", "technical assistant", "기술원", "기술직", "기능원"),
        disqualifying=True,
    ),
    NegativeKeywordRule(
        "Undergraduate internship",
        -40,
        ("undergraduate intern", "undergraduate internship", "학부 인턴"),
        disqualifying=True,
    ),
    NegativeKeywordRule(
        "Mechanical engineering only",
        -30,
        ("mechanical engineering", "mechanical engineer", "기계공학", "기계 설계"),
        disqualifying=False,
        unrelated_only=True,
    ),
    NegativeKeywordRule(
        "Automotive only",
        -30,
        ("automotive", "vehicle engineering", "자동차", "차량"),
        disqualifying=False,
        unrelated_only=True,
    ),
    NegativeKeywordRule(
        "Software-only",
        -40,
        ("software engineer", "software developer", "소프트웨어 개발"),
        disqualifying=False,
        unrelated_only=True,
    ),
    NegativeKeywordRule(
        "AI-only",
        -30,
        ("artificial intelligence", "machine learning", "인공지능", "머신러닝"),
        disqualifying=False,
        unrelated_only=True,
    ),
    NegativeKeywordRule(
        "Biomedical / clinical only",
        -30,
        ("clinical research", "clinical trial", "biomedical", "임상", "의생명"),
        disqualifying=False,
        unrelated_only=True,
    ),
)


def _contains(text: str, keywords: tuple[str, ...]) -> bool:
    folded = text.casefold()
    return any(keyword.casefold() in folded for keyword in keywords)


def _matched_categories(text: str) -> tuple[KeywordCategory, ...]:
    return tuple(rule for rule in CATEGORY_RULES if _contains(text, rule.keywords))


def assess_relevance(text: str, *, researcher_level: bool) -> RelevanceAssessment:
    categories = _matched_categories(text)
    positive = tuple(rule for rule in POSITIVE_RULES if _contains(text, rule.keywords))
    domain_positive = tuple(
        rule for rule in positive if rule.name != "General chemistry / materials"
    )
    score = RESEARCHER_LEVEL_SCORE if researcher_level else 0
    if domain_positive:
        score += DIRECT_MATCH_SCORE
    score += sum(rule.weight for rule in positive)
    disqualified = not researcher_level or not domain_positive
    for rule in NEGATIVE_RULES:
        if not _contains(text, rule.keywords):
            continue
        if rule.unrelated_only and domain_positive:
            continue
        score += rule.penalty
        disqualified = disqualified or rule.disqualifying
    bounded_score = max(0, min(100, score))
    if disqualified or bounded_score < MINIMUM_RELEVANT_SCORE:
        priority = PriorityLevel.IGNORE
    elif bounded_score >= APPLY_SERIOUSLY_SCORE:
        priority = PriorityLevel.APPLY_SERIOUSLY
    else:
        priority = PriorityLevel.WORTH_CHECKING
    reasons = (
        ("Researcher-level role aligns with the target career stage",)
        if researcher_level
        else ()
    ) + tuple(category.explanation for category in categories)
    return RelevanceAssessment(
        score=bounded_score,
        priority=priority,
        research_fields=tuple(category.name for category in categories),
        reasons=reasons,
    )


def recommended_profile_emphasis(
    research_fields: tuple[str, ...],
) -> tuple[str, ...]:
    emphases: list[str] = []
    for category in CATEGORY_RULES:
        if category.name not in research_fields:
            continue
        for emphasis in category.profile_emphasis:
            if emphasis not in emphases:
                emphases.append(emphasis)
    return tuple(emphases[:4])


def rank_postings(postings: tuple[JobPosting, ...]) -> tuple[JobPosting, ...]:
    priority_order = {
        PriorityLevel.APPLY_SERIOUSLY: 0,
        PriorityLevel.WORTH_CHECKING: 1,
        PriorityLevel.IGNORE: 2,
    }
    return tuple(
        sorted(
            postings,
            key=lambda posting: (
                priority_order[posting.priority],
                -posting.fit_score,
                posting.deadline or date.max,
                posting.title.casefold(),
            ),
        )
    )
