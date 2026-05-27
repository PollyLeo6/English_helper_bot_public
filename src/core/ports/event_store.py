from __future__ import annotations

from typing import Protocol

from src.core.models import UserEvent


class UserEventStore(Protocol):
    def append(self, event: UserEvent) -> None: ...

    def list_events(
        self,
        user_id: int,
        library_id: str | None = None,
        module_id: str | None = None,
        task_id: str | None = None,
    ) -> list[UserEvent]: ...

    def get_last_event(
        self, user_id: int, library_id: str, module_id: str, task_id: str
    ) -> UserEvent | None: ...

    def get_events_for_task(
        self, user_id: int, library_id: str, module_id: str, task_id: str
    ) -> list[UserEvent]: ...

    def compute_mean_rating(
        self, user_id: int, library_id: str, module_id: str, task_id: str
    ) -> float | None: ...
