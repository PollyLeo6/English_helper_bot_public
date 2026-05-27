from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskItem:
    text: str
    question: str
    answer_schema: Any | None = None


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]
    normalized_answers: list[str]
    expected_count: int


@dataclass(frozen=True)
class Task:
    task_id: str
    title: str
    texts: list[str]
    questions: list[str]
    answers: list[Any] | None = None
    rubric: str | None = None
    difficulty: str | None = None
    tags: list[str] | None = None
    source: dict[str, Any] | None = None

    def _expected_count(self) -> int:
        if len(self.texts) == len(self.questions):
            return len(self.questions)
        if not self.texts and self.questions:
            return len(self.questions)
        if len(self.texts) == 1 and len(self.questions) >= 1:
            return len(self.questions)
        raise ValueError("Task has incompatible texts/questions lengths")

    def pairs(self) -> list[TaskItem]:
        expected = self._expected_count()
        if not self.texts and expected > 0:
            texts = [""] * expected
        elif len(self.texts) == 1 and expected > 1:
            texts = [self.texts[0]] * expected
        else:
            texts = self.texts
        items: list[TaskItem] = []
        for idx, (text, question) in enumerate(zip(texts, self.questions, strict=True)):
            answer_schema = None
            if self.answers:
                if len(self.answers) == expected:
                    answer_schema = self.answers[idx]
                elif expected == 1:
                    answer_schema = self.answers
            items.append(
                TaskItem(text=text, question=question, answer_schema=answer_schema)
            )
        return items

    def validate_user_answers(self, user_answers: list[str] | str) -> ValidationResult:
        expected = self._expected_count()
        errors: list[str] = []
        if isinstance(user_answers, str):
            raw_answers = [user_answers] if expected == 1 else user_answers.splitlines()
        else:
            raw_answers = list(user_answers)
        normalized = [ans.strip() for ans in raw_answers if ans.strip() != ""]
        if len(normalized) != expected:
            errors.append(f"Expected {expected} answers, got {len(normalized)}")
        if len(normalized) != len(raw_answers):
            errors.append("Answers must be non-empty")
        return ValidationResult(
            ok=not errors,
            errors=errors,
            normalized_answers=normalized,
            expected_count=expected,
        )

    def to_prompt_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "task_id": self.task_id,
            "title": self.title,
            "items": [
                {
                    "text": item.text,
                    "question": item.question,
                    "answer_schema": item.answer_schema,
                }
                for item in self.pairs()
            ],
        }
        if self.rubric:
            payload["rubric"] = self.rubric
        if self.difficulty:
            payload["difficulty"] = self.difficulty
        if self.tags:
            payload["tags"] = self.tags
        if self.source:
            payload["source"] = self.source
        return payload
