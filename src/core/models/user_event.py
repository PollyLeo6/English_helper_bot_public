from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserEvent:
    user_id: int
    library_id: str
    module_id: str
    task_id: str
    user_answers: list[str]
    feedback: str
    rating: float
    mean_rating: float | None
    created_at: str

    def to_json(self) -> dict:
        return {
            "user_id": self.user_id,
            "library_id": self.library_id,
            "module_id": self.module_id,
            "task_id": self.task_id,
            "user_answers": self.user_answers,
            "feedback": self.feedback,
            "rating": self.rating,
            "mean_rating": self.mean_rating,
            "created_at": self.created_at,
        }

    @classmethod
    def from_json(cls, data: dict) -> UserEvent:
        return cls(
            user_id=int(data["user_id"]),
            library_id=str(data["library_id"]),
            module_id=str(data["module_id"]),
            task_id=str(data["task_id"]),
            user_answers=list(data.get("user_answers", [])),
            feedback=str(data.get("feedback", "")),
            rating=float(data.get("rating", 0.0)),
            mean_rating=(
                float(data["mean_rating"])
                if data.get("mean_rating") is not None
                else None
            ),
            created_at=str(data.get("created_at", "")),
        )
