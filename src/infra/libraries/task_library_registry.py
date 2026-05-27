from __future__ import annotations

from pathlib import Path

from src.core.models import LibraryInfo
from src.infra.libraries.task_library import TaskLibrary


class TaskLibraryRegistry:
    def __init__(self, root_path: str | Path) -> None:
        self._root_path = Path(root_path)
        self._libraries: dict[str, TaskLibrary] = {}
        self.reload()

    def list_libraries(self) -> list[LibraryInfo]:
        return [library.info() for library in self._libraries.values()]

    def get_library(self, library_id: str) -> TaskLibrary:
        if library_id not in self._libraries:
            raise KeyError(f"Library not found: {library_id}")
        return self._libraries[library_id]

    def library_exists(self, library_id: str) -> bool:
        return library_id in self._libraries

    def reload(self) -> None:
        libraries: dict[str, TaskLibrary] = {}
        if not self._root_path.exists():
            self._libraries = {}
            return
        for entry in sorted(self._root_path.iterdir()):
            if not entry.is_dir():
                continue
            if not (entry / "library.json").exists():
                continue
            library = TaskLibrary(entry)
            libraries[library.library_id] = library
        self._libraries = libraries
