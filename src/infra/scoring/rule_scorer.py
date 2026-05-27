from __future__ import annotations

from src.core.models import ItemScoreResult, ScoreResult, Task
from src.core.ports import Scorer
from src.infra.scoring.answer_key import score_from_answer_key
from src.infra.scoring.personality_quiz import score_personality_quiz


class RuleScorer(Scorer):
    def score(self, task: Task, user_answers: list[str]) -> ScoreResult:
        personality_quiz_result = score_personality_quiz(task, user_answers)
        if personality_quiz_result is not None:
            return personality_quiz_result

        answer_key_result = score_from_answer_key(task, user_answers)
        if answer_key_result is not None:
            return answer_key_result

        items = task.pairs()
        item_scores = []
        for item, user_answer in zip(items, user_answers, strict=False):
            item_scores.append(self.score_item(item.text, item.question, user_answer))
        if not item_scores:
            return ScoreResult(
                score=0.0, feedback="No answers provided.", items=[], mode="rule"
            )
        total = sum(item.score for item in item_scores) / len(item_scores)
        feedback = (
            "Nice effort. Focus on accuracy and clarity."
            if total >= 60
            else "Good start. Try to be more precise and complete in your answers."
        )
        return ScoreResult(
            score=round(total, 2), feedback=feedback, items=item_scores, mode="rule"
        )

    def score_item(self, text: str, question: str, user_answer: str) -> ItemScoreResult:
        answer = user_answer.strip()
        if not answer:
            return ItemScoreResult(score=0.0, feedback="Answer is empty. Try again.")
        score = 40.0
        if len(answer) >= 10:
            score += 20
        if any(ch in answer for ch in ".,;:?!"):
            score += 10
        if len(answer.split()) >= 4:
            score += 15
        if answer[0:1].isupper():
            score += 5
        score = min(score, 100.0)
        feedback = (
            "Clear answer. Consider small grammar improvements."
            if score >= 70
            else "Decent attempt. Try adding more detail or fixing grammar."
        )
        return ItemScoreResult(score=score, feedback=feedback)
