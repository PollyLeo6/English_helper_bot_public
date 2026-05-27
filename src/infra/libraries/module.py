from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.models import ModuleInfo, Task, TaskGroupInfo, TaskInfo
from src.infra.libraries.json_loader import load_json


class Module:
    def __init__(self, module_dir: Path) -> None:
        self._module_dir = module_dir
        module_data = load_json(module_dir / "module.json")
        self.module_id = str(module_data["module_id"])
        self.title = str(module_data.get("title", self.module_id))
        self.description = str(module_data.get("description", ""))
        self._tasks_index: dict[str, TaskInfo] = {}
        self._task_groups: dict[str, tuple[TaskGroupInfo, list[str]]] = {}
        for task in module_data.get("tasks", []):
            task_id = str(task["task_id"])
            self._tasks_index[task_id] = TaskInfo(
                task_id=task_id, title=str(task.get("title", task_id))
            )
        for group in module_data.get("task_groups", []):
            group_id = str(group["group_id"])
            task_ids = [str(task_id) for task_id in group.get("tasks", [])]
            self._task_groups[group_id] = (
                TaskGroupInfo(
                    group_id=group_id,
                    title=str(group.get("title", group_id)),
                    task_count=len(task_ids),
                ),
                task_ids,
            )

    def list_task_groups(self) -> list[TaskGroupInfo]:
        return [group_info for group_info, _ in self._task_groups.values()]

    def has_task_groups(self) -> bool:
        return bool(self._task_groups)

    def list_tasks(self, group_id: str | None = None) -> list[TaskInfo]:
        if group_id is None:
            return list(self._tasks_index.values())
        if group_id not in self._task_groups:
            raise KeyError(f"Task group not found: {group_id}")
        _, task_ids = self._task_groups[group_id]
        return [self._tasks_index[task_id] for task_id in task_ids]

    def get_task(self, task_id: str) -> Task:
        task_file = self._module_dir / "tasks" / f"{task_id}.json"
        if not task_file.exists():
            raise FileNotFoundError(f"Task not found: {task_id}")
        data = load_json(task_file)
        return self._load_task(data)

    def get_task_count(self) -> int:
        return len(self._tasks_index)

    def _load_task(self, data: dict[str, Any]) -> Task:
        return Task(
            task_id=str(data["task_id"]),
            title=str(data.get("title", "")),
            texts=list(data.get("texts", [])),
            questions=list(data.get("questions", [])),
            answers=data.get("answers"),
            rubric=data.get("rubric"),
            difficulty=data.get("difficulty"),
            tags=data.get("tags"),
            source=data.get("source"),
        )

    def info(self) -> ModuleInfo:
        return ModuleInfo(
            module_id=self.module_id,
            title=self.title,
            description=self.description,
            task_count=self.get_task_count(),
        )
