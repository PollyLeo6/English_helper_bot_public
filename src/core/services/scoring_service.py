from __future__ import annotations

from src.core.models import ItemScoreResult, ScoreResult, Task
from src.core.ports import Scorer


class ScoringService:
    def __init__(self, scorer: Scorer) -> None:
        self._scorer = scorer

    def score(self, task: Task, user_answers: list[str]) -> ScoreResult:
        return self._scorer.score(task, user_answers)

    def score_item(self, text: str, question: str, user_answer: str) -> ItemScoreResult:
        return self._scorer.score_item(text, question, user_answer)
