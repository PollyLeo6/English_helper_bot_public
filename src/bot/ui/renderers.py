from __future__ import annotations

from src.core.models import (
    LibraryInfo,
    LibraryProgress,
    ModuleInfo,
    ModuleProgress,
    OverallProgress,
    ScoreResult,
    Task,
    TaskGroupInfo,
    TaskInfo,
    TaskProgress,
)
from src.core.utils import safe_truncate


def main_menu_text() -> str:
    return "Welcome! Choose an option:"


def library_list_text(libraries: list[LibraryInfo]) -> str:
    return "Choose a library:" if libraries else "No libraries found."


def module_list_text(library: LibraryInfo, modules: list[ModuleInfo]) -> str:
    return f"Library: {library.title}\nChoose a module:" if modules else "No modules."


def task_list_text(
    module: ModuleInfo,
    tasks: list[TaskInfo],
    scores: dict[str, tuple[float | None, float | None]],
) -> str:
    lines = [f"Module: {module.title}", "Choose a task:"]
    for task in tasks:
        last_score, mean_score = scores.get(task.task_id, (None, None))
        score_parts = []
        if last_score is not None:
            score_parts.append(f"last: {last_score:.1f}")
        if mean_score is not None:
            score_parts.append(f"mean: {mean_score:.1f}")
        score_text = f" ({', '.join(score_parts)})" if score_parts else ""
        lines.append(f"- {task.title}{score_text}")
    return "\n".join(lines)


def task_group_list_text(
    module: ModuleInfo,
    groups: list[TaskGroupInfo],
) -> str:
    if not groups:
        return f"Module: {module.title}\nNo task groups."
    lines = [f"Module: {module.title}", "Choose a section:"]
    for group in groups:
        count = f" ({group.task_count} tasks)" if group.task_count is not None else ""
        lines.append(f"- {group.title}{count}")
    return "\n".join(lines)


def task_overview_text(task: Task) -> str:
    return f"{task.title}\nItems: {len(task.pairs())}"


def task_prompt_text(task: Task, index: int) -> str:
    items = task.pairs()
    item = items[index]
    header = f"Item {index + 1}/{len(items)}"
    if item.text.strip():
        return f"{header}\n\n{safe_truncate(item.text, limit=3500)}\n\nQuestion: {item.question}"
    return f"{header}\n\nQuestion: {item.question}"


def task_result_text(result: ScoreResult) -> str:
    lines = [f"Score: {result.score:.1f}", "", result.feedback]
    missed_items = [
        (index, item)
        for index, item in enumerate(result.items, start=1)
        if item.score < 100 and item.feedback.strip()
    ]
    if missed_items:
        lines.append("")
        lines.append("Review:")
        for index, item in missed_items:
            lines.append(f"Item {index}: {item.feedback}")
    return "\n".join(lines)


def progress_overview_text(progress: OverallProgress) -> str:
    if progress.mean_rating is None:
        return "Overall progress\nNo attempts yet."
    return (
        "Overall progress\n"
        f"Tasks completed: {progress.tasks_completed}/{progress.tasks_total}\n"
        f"Mean score: {progress.mean_rating:.1f}"
    )


def progress_library_text(library: LibraryInfo, progress: LibraryProgress) -> str:
    if progress.mean_rating is None:
        return f"Library: {library.title}\nNo attempts yet."
    return (
        f"Library: {library.title}\n"
        f"Tasks completed: {progress.tasks_completed}/{progress.tasks_total}\n"
        f"Mean score: {progress.mean_rating:.1f}"
    )


def progress_module_text(module: ModuleInfo, progress: ModuleProgress) -> str:
    if progress.mean_rating is None:
        return f"Module: {module.title}\nNo attempts yet."
    return (
        f"Module: {module.title}\n"
        f"Tasks completed: {progress.tasks_completed}/{progress.tasks_total}\n"
        f"Mean score: {progress.mean_rating:.1f}"
    )


def progress_task_details_text(task: TaskInfo, progress: TaskProgress) -> str:
    if progress.attempts == 0:
        return f"Task: {task.title}\nNo attempts yet."
    return (
        f"Task: {task.title}\n"
        f"Attempts: {progress.attempts}\n"
        f"Last score: {progress.last_rating:.1f}\n"
        f"Mean score: {progress.mean_rating:.1f}"
    )
