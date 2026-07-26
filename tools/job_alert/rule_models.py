from __future__ import annotations

from dataclasses import dataclass


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
