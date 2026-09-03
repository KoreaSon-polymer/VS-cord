from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KeywordCategory:
    name: str
    keywords: tuple[str, ...]
    explanation: str
    profile_emphasis: tuple[str, ...]
    tier: int
