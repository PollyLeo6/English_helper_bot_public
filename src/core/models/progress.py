from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskProgress:
    library_id: str
    module_id: str
    task_id: str
    attempts: int
    last_rating: float | None
    mean_rating: float | None


@dataclass(frozen=True)
class ModuleProgress:
    library_id: str
    module_id: str
    tasks_total: int
    tasks_completed: int
    mean_rating: float | None
    tasks: list[TaskProgress]


@dataclass(frozen=True)
class LibraryProgress:
    library_id: str
    modules_total: int
    tasks_total: int
    tasks_completed: int
    mean_rating: float | None
    modules: list[ModuleProgress]


@dataclass(frozen=True)
class OverallProgress:
    libraries_total: int
    tasks_total: int
    tasks_completed: int
    mean_rating: float | None
    libraries: list[LibraryProgress]
