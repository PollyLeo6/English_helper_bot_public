from __future__ import annotations

from pathlib import Path

from src.core.models import LibraryInfo, ModuleInfo, Task, TaskInfo
from src.infra.libraries.json_loader import load_json
from src.infra.libraries.module import Module


class TaskLibrary:
    def __init__(self, library_dir: Path) -> None:
        self._library_dir = library_dir
        library_data = load_json(library_dir / "library.json")
        self.library_id = str(library_data["library_id"])
        self.title = str(library_data.get("title", self.library_id))
        self.description = str(library_data.get("description", ""))
        self._modules: dict[str, Module] = {}
        for module_info in library_data.get("modules", []):
            module_id = str(module_info["module_id"])
            module_dir = library_dir / "modules" / module_id
            self._modules[module_id] = Module(module_dir)

    def list_modules(self) -> list[ModuleInfo]:
        return [module.info() for module in self._modules.values()]

    def get_module(self, module_id: str | int) -> Module:
        module_key = str(module_id)
        if module_key not in self._modules:
            raise KeyError(f"Module not found: {module_id}")
        return self._modules[module_key]

    def get_module_info(self, module_id: str | int) -> ModuleInfo:
        return self.get_module(module_id).info()

    def get_task(self, module_id: str | int, task_id: str) -> Task:
        return self.get_module(module_id).get_task(task_id)

    def get_task_info(self, module_id: str | int, task_id: str) -> TaskInfo:
        module = self.get_module(module_id)
        for task_info in module.list_tasks():
            if task_info.task_id == task_id:
                return task_info
        raise KeyError(f"Task not found: {task_id}")

    def info(self) -> LibraryInfo:
        return LibraryInfo(
            library_id=self.library_id,
            title=self.title,
            description=self.description,
            module_count=len(self._modules),
        )
