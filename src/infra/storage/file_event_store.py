from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from src.core.models import UserEvent
from src.core.utils import make_event_id
from src.infra.storage.paths import ensure_user_dirs, events_dir


class FileUserEventStore:
    def __init__(self, base_path: str | Path) -> None:
        self._base_path = Path(base_path)

    def append(self, event: UserEvent) -> None:
        ensure_user_dirs(self._base_path, event.user_id)
        event_id = make_event_id()
        path = events_dir(self._base_path, event.user_id) / f"{event_id}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(event.to_json(), handle, ensure_ascii=False, indent=2)

    def list_events(
        self,
        user_id: int,
        library_id: str | None = None,
        module_id: str | None = None,
        task_id: str | None = None,
    ) -> list[UserEvent]:
        folder = events_dir(self._base_path, user_id)
        if not folder.exists():
            return []
        events: list[UserEvent] = []
        for path in sorted(folder.glob("*.json")):
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            event = UserEvent.from_json(data)
            if library_id and event.library_id != library_id:
                continue
            if module_id and event.module_id != module_id:
                continue
            if task_id and event.task_id != task_id:
                continue
            events.append(event)
        events.sort(key=lambda e: e.created_at)
        return events

    def get_last_event(
        self, user_id: int, library_id: str, module_id: str, task_id: str
    ) -> UserEvent | None:
        events = self.get_events_for_task(user_id, library_id, module_id, task_id)
        return events[-1] if events else None

    def get_events_for_task(
        self, user_id: int, library_id: str, module_id: str, task_id: str
    ) -> list[UserEvent]:
        return self.list_events(
            user_id=user_id, library_id=library_id, module_id=module_id, task_id=task_id
        )

    def compute_mean_rating(
        self, user_id: int, library_id: str, module_id: str, task_id: str
    ) -> float | None:
        events = self.get_events_for_task(user_id, library_id, module_id, task_id)
        return _mean_rating(events)


def _mean_rating(events: Iterable[UserEvent]) -> float | None:
    ratings = [event.rating for event in events]
    if not ratings:
        return None
    return sum(ratings) / len(ratings)
