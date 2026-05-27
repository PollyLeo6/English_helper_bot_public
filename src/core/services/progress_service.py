from __future__ import annotations

from statistics import mean

from src.core.models import (
    LibraryProgress,
    ModuleProgress,
    OverallProgress,
    TaskProgress,
)
from src.core.ports import LibraryRegistry, UserEventStore


class ProgressService:
    def __init__(self, registry: LibraryRegistry, event_store: UserEventStore) -> None:
        self._registry = registry
        self._event_store = event_store

    def get_task_progress(
        self, user_id: int, library_id: str, module_id: str, task_id: str
    ) -> TaskProgress:
        events = self._event_store.get_events_for_task(
            user_id=user_id, library_id=library_id, module_id=module_id, task_id=task_id
        )
        attempts = len(events)
        last_rating = events[-1].rating if events else None
        mean_rating = mean([event.rating for event in events]) if events else None
        return TaskProgress(
            library_id=library_id,
            module_id=module_id,
            task_id=task_id,
            attempts=attempts,
            last_rating=last_rating,
            mean_rating=mean_rating,
        )

    def get_module_progress(
        self, user_id: int, library_id: str, module_id: str
    ) -> ModuleProgress:
        library = self._registry.get_library(library_id)
        module = library.get_module(module_id)
        tasks = [
            self.get_task_progress(user_id, library_id, module_id, task.task_id)
            for task in module.list_tasks()
        ]
        tasks_total = len(tasks)
        tasks_completed = sum(1 for task in tasks if task.attempts > 0)
        ratings = [task.mean_rating for task in tasks if task.mean_rating is not None]
        module_mean = mean(ratings) if ratings else None
        return ModuleProgress(
            library_id=library_id,
            module_id=module_id,
            tasks_total=tasks_total,
            tasks_completed=tasks_completed,
            mean_rating=module_mean,
            tasks=tasks,
        )

    def get_library_progress(self, user_id: int, library_id: str) -> LibraryProgress:
        library = self._registry.get_library(library_id)
        modules = [
            self.get_module_progress(user_id, library_id, module.module_id)
            for module in library.list_modules()
        ]
        tasks_total = sum(module.tasks_total for module in modules)
        tasks_completed = sum(module.tasks_completed for module in modules)
        ratings = [
            module.mean_rating for module in modules if module.mean_rating is not None
        ]
        library_mean = mean(ratings) if ratings else None
        return LibraryProgress(
            library_id=library_id,
            modules_total=len(modules),
            tasks_total=tasks_total,
            tasks_completed=tasks_completed,
            mean_rating=library_mean,
            modules=modules,
        )

    def get_overall_progress(self, user_id: int) -> OverallProgress:
        libraries = [
            self.get_library_progress(user_id, library.library_id)
            for library in self._registry.list_libraries()
        ]
        tasks_total = sum(library.tasks_total for library in libraries)
        tasks_completed = sum(library.tasks_completed for library in libraries)
        ratings = [
            library.mean_rating
            for library in libraries
            if library.mean_rating is not None
        ]
        overall_mean = mean(ratings) if ratings else None
        return OverallProgress(
            libraries_total=len(libraries),
            tasks_total=tasks_total,
            tasks_completed=tasks_completed,
            mean_rating=overall_mean,
            libraries=libraries,
        )
