from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ItemScoreResult:
    score: float
    feedback: str


@dataclass(frozen=True)
class ScoreResult:
    score: float
    feedback: str
    items: list[ItemScoreResult]
    mode: str
