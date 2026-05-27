from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskInfo:
    task_id: str
    title: str


@dataclass(frozen=True)
class TaskGroupInfo:
    group_id: str
    title: str
    task_count: int | None = None


@dataclass(frozen=True)
class ModuleInfo:
    module_id: str
    title: str
    description: str | None = None
    task_count: int | None = None


@dataclass(frozen=True)
class LibraryInfo:
    library_id: str
    title: str
    description: str | None = None
    module_count: int | None = None
