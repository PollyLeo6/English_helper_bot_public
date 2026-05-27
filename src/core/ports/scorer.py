from __future__ import annotations

from typing import Protocol

from src.core.models import ItemScoreResult, ScoreResult, Task


class Scorer(Protocol):
    def score(self, task: Task, user_answers: list[str]) -> ScoreResult: ...

    def score_item(
        self, text: str, question: str, user_answer: str
    ) -> ItemScoreResult: ...
