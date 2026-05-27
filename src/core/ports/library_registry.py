from __future__ import annotations

from typing import Protocol

from src.core.models import LibraryInfo
from src.infra.libraries.task_library import TaskLibrary


class LibraryRegistry(Protocol):
    def list_libraries(self) -> list[LibraryInfo]: ...

    def get_library(self, library_id: str) -> TaskLibrary: ...

    def library_exists(self, library_id: str) -> bool: ...

    def reload(self) -> None: ...
