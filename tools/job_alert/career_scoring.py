from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .assessments import CareerAssessment
from .research_fit import contains_keyword

CAREER_SCORE_REFERENCE: Final = 70


@dataclass(frozen=True, slots=True)
class CareerRule:
    name: str
    score: int
    keywords: tuple[str, ...]


POSITION_RULES: Final = (
    CareerRule(
        "Tenure-track or assistant professor",
        30,
        ("tenure track", "assistant professor", "조교수", "전임교원"),
    ),
    CareerRule(
        "Research professor or research faculty",
        25,
        ("research professor", "research faculty", "연구교수"),
    ),
    CareerRule(
        "Senior, principal, or permanent researcher",
        25,
        (
            "senior researcher",
            "principal researcher",
            "permanent researcher",
            "선임연구원",
            "책임연구원",
            "정규직 연구",
        ),
    ),
    CareerRule(
        "Project or contract professor",
        20,
        ("project professor", "contract professor", "프로젝트교수", "계약교수"),
    ),
    CareerRule(
        "Research scientist",
        20,
        ("research scientist", "연구과학자"),
    ),
    CareerRule(
        "Postdoctoral researcher",
        5,
        ("postdoctoral", "post-doc", "postdoc", "박사후연구원", "박사후 연구원"),
    ),
    CareerRule(
        "Researcher",
        12,
        ("researcher", "scientist", "연구원", "연구직"),
    ),
)

INDEPENDENCE_RULES: Final = (
    CareerRule(
        "PI responsibility",
        20,
        ("pi responsibility", "연구책임자", "과제책임"),
    ),
    CareerRule(
        "Research leadership",
        15,
        ("research leadership", "research leader", "연구 리더", "연구책임"),
    ),
    CareerRule(
        "Project management",
        10,
        ("project management", "과제 관리", "프로젝트 관리"),
    ),
    CareerRule(
        "Independent research",
        15,
        ("independent research", "independent researcher", "독립 연구"),
    ),
    CareerRule(
        "Grant participation",
        10,
        ("grant participation", "연구비 참여", "과제 참여"),
    ),
)

TOP_INSTITUTIONS: Final = (
    "kist",
    "krict",
    "kims",
    "kier",
    "kriss",
    "ibs",
    "kaeri",
    "kbsi",
    "kaist",
    "postech",
    "seoul national university",
    "서울대학교",
    "korea university",
    "고려대학교",
    "yonsei",
    "연세대학교",
    "sungkyunkwan",
    "성균관대학교",
    "hanyang",
    "한양대학교",
    "unist",
    "dgist",
    "gist",
)
MAJOR_RND_COMPANIES: Final = (
    "samsung",
    "lg chem",
    "lg energy solution",
    "sk materials",
    "oci",
    "hanwha solutions",
    "kolon",
    "lotte chemical",
)
EXCESSIVE_EXPERIENCE: Final = (
    "10 years",
    "10+ years",
    "10년 이상",
    "semiconductor manufacturing industry experience",
)
PHD_MARKERS: Final = ("phd", "ph.d", "박사학위", "박사 학위")


def _best_position_rule(text: str) -> CareerRule | None:
    return next(
        (rule for rule in POSITION_RULES if contains_keyword(text, rule.keywords)),
        None,
    )


def _institution_score(institution: str) -> tuple[int, str]:
    folded = institution.casefold()
    if any(name in folded for name in TOP_INSTITUTIONS):
        return 15, "Top research institution"
    if "연구원" in institution or "national research institute" in folded:
        return 12, "National research institute"
    if "university" in folded or "대학교" in institution:
        return 12, "Major university"
    if any(name in folded for name in MAJOR_RND_COMPANIES):
        return 12, "Major industrial R&D organization"
    return 0, "Institution quality requires manual review"


def _compatibility_score(text: str, *, research_match: bool) -> tuple[int, str]:
    if contains_keyword(text, EXCESSIVE_EXPERIENCE):
        return 0, "Low compatibility: excessive industry-experience requirement"
    if research_match and contains_keyword(text, PHD_MARKERS):
        return 15, "High compatibility: PhD requirement and research match"
    if research_match:
        return 8, "Medium compatibility: relevant research background"
    return 0, "Low compatibility: research match not demonstrated"


def assess_career_advancement(
    text: str,
    institution: str,
    *,
    research_match: bool,
) -> CareerAssessment:
    position_rule = _best_position_rule(text)
    position_score = position_rule.score if position_rule else 0
    position_reason = (
        f"Position level: {position_rule.name} (+{position_score})"
        if position_rule
        else "Position level requires manual review"
    )
    independence = tuple(
        rule for rule in INDEPENDENCE_RULES if contains_keyword(text, rule.keywords)
    )
    independence_score = sum(rule.score for rule in independence)
    institution_score, institution_reason = _institution_score(institution)
    compatibility_score, compatibility_reason = _compatibility_score(
        text,
        research_match=research_match,
    )
    raw_score = (
        position_score + independence_score + institution_score + compatibility_score
    )
    score = min(100, round(raw_score * 100 / CAREER_SCORE_REFERENCE))
    independence_reasons = tuple(
        f"Independence: {rule.name} (+{rule.score})" for rule in independence
    )
    career_value = (
        "Greater independence and research ownership"
        if independence_score
        else "Independence potential requires confirmation"
    )
    return CareerAssessment(
        score=score,
        position_score=position_score,
        independence_score=independence_score,
        institution_score=institution_score,
        compatibility_score=compatibility_score,
        reasons=(
            position_reason,
            *independence_reasons,
            institution_reason,
            compatibility_reason,
        ),
        career_value=(
            career_value,
            "Publication potential follows the matched research domain",
            "Long-term value reflects position level and institution quality",
        ),
    )
