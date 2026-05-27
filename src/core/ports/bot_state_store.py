from __future__ import annotations

from typing import Protocol

from src.core.models import BotState, State


class BotStateStore(Protocol):
    def get(self, user_id: int) -> BotState: ...

    def set(self, user_id: int, state: State, context: dict) -> None: ...

    def reset(self, user_id: int) -> None: ...
