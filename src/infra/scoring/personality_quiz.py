from __future__ import annotations

import re
from collections import Counter

from src.core.models import ItemScoreResult, ScoreResult, Task

PERSONALITY_QUIZ_TAG = "personality_quiz"

RESULTS = {
    "a": (
        "Mostly A",
        "You are a planner. You like structure, preparation, and clear "
        "information. You usually prefer to know what you are doing in advance.",
    ),
    "b": (
        "Mostly B",
        "You are balanced and practical. You like to be prepared, but you can "
        "also adapt when necessary.",
    ),
    "c": (
        "Mostly C",
        "You are flexible and intuitive. You often trust your instincts and "
        "prefer not to plan everything too strictly.",
    ),
    "d": (
        "Mostly D",
        "You are spontaneous and people-oriented. You enjoy freedom, "
        "communication, and reacting to situations as they happen.",
    ),
}


def score_personality_quiz(task: Task, user_answers: list[str]) -> ScoreResult | None:
    if PERSONALITY_QUIZ_TAG not in (task.tags or []):
        return None

    answers = _parse_answers("\n".join(user_answers))
    if len(answers) != 12:
        return ScoreResult(
            score=0.0,
            feedback=(
                "Please answer all 12 questions in one line.\n\n"
                "Format: 1a 2b 3c 4d 5a 6b 7c 8d 9a 10b 11c 12d"
            ),
            items=[ItemScoreResult(score=0.0, feedback="Expected 12 quiz answers.")],
            mode="personality_quiz",
        )

    counts = Counter(answers.values())
    top_count = max(counts.values())
    winners = [letter for letter in "abcd" if counts[letter] == top_count]
    lines = [
        "You chose:",
        f"A - {counts['a']}",
        f"B - {counts['b']}",
        f"C - {counts['c']}",
        f"D - {counts['d']}",
        "",
    ]
    if len(winners) > 1:
        lines.append("Your result is mixed.")
        lines.append(
            "You have a combination of personality traits from these types:"
        )
        lines.extend(_result_line(letter) for letter in winners)
    else:
        lines.append(f"Your result: {_result_line(winners[0])}")

    return ScoreResult(
        score=100.0,
        feedback="\n".join(lines),
        items=[ItemScoreResult(score=100.0, feedback="Quiz completed.")],
        mode="personality_quiz",
    )


def _parse_answers(raw_answer: str) -> dict[int, str]:
    answers: dict[int, str] = {}
    for number, letter in re.findall(
        r"\b(1[0-2]|[1-9])\s*[\).:-]?\s*([abcd])\b",
        raw_answer.lower(),
    ):
        answers[int(number)] = letter
    if answers:
        return {
            question_number: answers[question_number]
            for question_number in range(1, 13)
            if question_number in answers
        }

    bare_letters = re.findall(r"\b([abcd])\b", raw_answer.lower())
    if len(bare_letters) == 12:
        return dict(enumerate(bare_letters, start=1))
    return {}


def _result_line(letter: str) -> str:
    title, description = RESULTS[letter]
    return f"{title} - {description}"
