from __future__ import annotations

import re
from typing import Any

from src.core.models import ItemScoreResult, ScoreResult, Task


def score_from_answer_key(task: Task, user_answers: list[str]) -> ScoreResult | None:
    items = task.pairs()
    if not items:
        return None

    item_scores: list[ItemScoreResult] = []
    for idx, item in enumerate(items):
        if item.answer_schema is None:
            return None
        user_answer = user_answers[idx] if idx < len(user_answers) else ""
        score, feedback = score_expected_answer(item.answer_schema, user_answer)
        item_scores.append(ItemScoreResult(score=round(score, 2), feedback=feedback))

    total = sum(item.score for item in item_scores) / len(item_scores)
    total = round(total, 2)
    feedback = (
        "Checked against the answer key. Nice work."
        if total >= 80
        else "Checked against the answer key. Review the missed answers and try again."
    )
    return ScoreResult(
        score=total, feedback=feedback, items=item_scores, mode="answer_key"
    )


def score_expected_answer(expected: Any, user_answer: str) -> tuple[float, str]:
    expected_pairs = _parse_match_pairs(expected)
    user_pairs = _parse_match_pairs(user_answer)
    if expected_pairs and user_pairs:
        correct_keys = [
            key for key, value in expected_pairs.items() if user_pairs.get(key) == value
        ]
        wrong_keys = [
            key
            for key in expected_pairs
            if key in user_pairs and user_pairs[key] != expected_pairs[key]
        ]
        missing_keys = [key for key in expected_pairs if key not in user_pairs]
        total = len(expected_pairs)
        score = len(correct_keys) / total * 100 if total else 0.0
        feedback = f"Correct matches: {len(correct_keys)}/{total}."
        review_keys = wrong_keys + missing_keys
        if review_keys:
            feedback += f" Review: {', '.join(review_keys)}."
        return score, feedback

    expected_values = _expected_values(expected)
    if len(expected_values) > 1:
        user_values = _split_answer_values(user_answer)
        correct = 0
        for idx, expected_value in enumerate(expected_values):
            if idx >= len(user_values):
                continue
            if normalize_answer(user_values[idx]) == normalize_answer(expected_value):
                correct += 1
        total = len(expected_values)
        score = correct / total * 100 if total else 0.0
        return score, f"Correct answers in order: {correct}/{total}."

    expected_text = expected_values[0] if expected_values else ""
    if normalize_answer(user_answer) == normalize_answer(expected_text):
        return 100.0, "Correct."
    return 0.0, f"Expected answer: {expected_text}."


def normalize_answer(answer: str) -> str:
    text = answer.lower().strip().replace("вЂ™", "'").replace("’", "'")
    contractions = {
        "i'm": "i am",
        "you're": "you are",
        "he's": "he is",
        "she's": "she is",
        "it's": "it is",
        "we're": "we are",
        "they're": "they are",
    }
    for contraction, expanded in contractions.items():
        text = text.replace(contraction, expanded)
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _expected_values(expected: Any) -> list[str]:
    if isinstance(expected, list):
        return [str(value) for value in expected]
    return [str(expected)]


def _split_answer_values(answer: str) -> list[str]:
    values = [part.strip() for part in re.split(r"[,;\n]+", answer) if part.strip()]
    return values if values else [answer.strip()]


def _parse_match_pairs(value: Any) -> dict[str, str]:
    text = ", ".join(_expected_values(value))
    pairs: dict[str, str] = {}
    for key, match_value in re.findall(
        r"\b([A-Za-z])\s*[-:]\s*([0-9]+|[A-Za-z])\b", text
    ):
        pairs[key.upper()] = match_value.lower()
    return pairs
