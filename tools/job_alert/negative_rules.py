from __future__ import annotations

from typing import Final

from .rule_models import NegativeKeywordRule

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
        "Facility",
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
        "Mechanical engineering only",
        -30,
        ("mechanical engineering", "mechanical engineer", "기계공학", "기계 설계"),
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
        "Biomedical-only",
        -30,
        ("clinical research", "clinical trial", "biomedical", "임상", "의생명"),
        disqualifying=False,
        unrelated_only=True,
    ),
)
