from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class State(StrEnum):
    MAIN_MENU = "MAIN_MENU"
    LIBRARY_LIST = "LIBRARY_LIST"
    MODULE_LIST = "MODULE_LIST"
    TASK_LIST = "TASK_LIST"
    TASK_OVERVIEW = "TASK_OVERVIEW"
    TASK_IN_PROGRESS = "TASK_IN_PROGRESS"
    TASK_RESULT = "TASK_RESULT"
    PROGRESS_OVERVIEW = "PROGRESS_OVERVIEW"
    PROGRESS_LIBRARY = "PROGRESS_LIBRARY"
    PROGRESS_MODULE = "PROGRESS_MODULE"
    PROGRESS_TASK_DETAILS = "PROGRESS_TASK_DETAILS"


@dataclass(frozen=True)
class BotState:
    user_id: int
    state: State
    context: dict[str, Any]

    def to_json(self) -> dict:
        return {
            "user_id": self.user_id,
            "state": self.state.value,
            "context": self.context,
        }

    @classmethod
    def from_json(cls, data: dict) -> BotState:
        return cls(
            user_id=int(data["user_id"]),
            state=State(data["state"]),
            context=dict(data.get("context", {})),
        )
