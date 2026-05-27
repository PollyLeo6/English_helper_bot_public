from __future__ import annotations

import json
from typing import Any


def build_scoring_prompt(payload: dict[str, Any], user_answers: list[str]) -> str:
    items = payload.get("items", [])
    lines = [
        "You are an English teacher. Score each answer from 0 to 100.",
        "Return ONLY JSON with keys: score (0-100), feedback (string), items (list).",
        'Each item: {"score": number, "feedback": string}.',
        "When an expected answer is provided, use it as the answer key and award partial credit for partially correct lists or matching pairs.",
    ]
    if payload.get("rubric"):
        lines.append(f"Rubric: {payload['rubric']}")
    for idx, item in enumerate(items, start=1):
        answer = user_answers[idx - 1] if idx - 1 < len(user_answers) else ""
        lines.append(f"Item {idx}:")
        lines.append(f"Text: {item.get('text', '')}")
        lines.append(f"Question: {item.get('question', '')}")
        if item.get("answer_schema") is not None:
            expected = json.dumps(item["answer_schema"], ensure_ascii=False)
            lines.append(f"Expected answer: {expected}")
        lines.append(f"User answer: {answer}")
    return "\n".join(lines)
