from __future__ import annotations

from statistics import mean

from src.core.models import ScoreResult, Task, UserEvent
from src.core.ports import UserEventStore
from src.core.services.scoring_service import ScoringService
from src.core.utils import now_utc_iso


class TaskSession:
    def __init__(
        self,
        user_id: int,
        library_id: str,
        module_id: str,
        scoring_service: ScoringService,
        event_store: UserEventStore,
    ) -> None:
        self._user_id = user_id
        self._library_id = library_id
        self._module_id = module_id
        self._scoring_service = scoring_service
        self._event_store = event_store
        self._task: Task | None = None
        self._answers: list[str] = []
        self._index = 0

    def start(self, task: Task) -> None:
        self._task = task
        self._answers = []
        self._index = 0

    def get_current_prompt(self) -> str:
        if not self._task:
            raise RuntimeError("TaskSession not started")
        items = self._task.pairs()
        item = items[self._index]
        return f"{item.text}\n\nQuestion: {item.question}"

    def submit_answer(self, text: str) -> None:
        if not self._task:
            raise RuntimeError("TaskSession not started")
        self._answers.append(text.strip())
        self._index += 1

    def is_complete(self) -> bool:
        if not self._task:
            return False
        return self._index >= len(self._task.pairs())

    def finish(self) -> tuple[UserEvent, ScoreResult]:
        if not self._task:
            raise RuntimeError("TaskSession not started")
        score_result = self._scoring_service.score(self._task, self._answers)
        existing = self._event_store.get_events_for_task(
            user_id=self._user_id,
            library_id=self._library_id,
            module_id=self._module_id,
            task_id=self._task.task_id,
        )
        ratings = [event.rating for event in existing] + [score_result.score]
        mean_rating = mean(ratings) if ratings else None
        event = UserEvent(
            user_id=self._user_id,
            library_id=self._library_id,
            module_id=self._module_id,
            task_id=self._task.task_id,
            user_answers=list(self._answers),
            feedback=score_result.feedback,
            rating=score_result.score,
            mean_rating=mean_rating,
            created_at=now_utc_iso(),
        )
        return event, score_result
