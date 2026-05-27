from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.ui.callback_data import encode
from src.core.models import LibraryInfo, ModuleInfo, TaskGroupInfo, TaskInfo

ACTION_DO_TASKS = "DT"
ACTION_PROGRESS = "PR"
ACTION_SELECT_LIBRARY = "SL"
ACTION_SELECT_MODULE = "SM"
ACTION_SELECT_TASK_GROUP = "SG"
ACTION_SELECT_TASK = "ST"
ACTION_START_TASK = "GO"
ACTION_CANCEL_TASK = "CN"
ACTION_RETRY_TASK = "RT"
ACTION_NEXT_TASK = "NT"
ACTION_BACK_TASKS = "BT"
ACTION_HOME = "HM"
ACTION_BACK = "BK"
ACTION_PROGRESS_LIBRARY = "PL"
ACTION_PROGRESS_MODULE = "PM"
ACTION_PROGRESS_TASK = "PT"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Do tasks", callback_data=encode(ACTION_DO_TASKS))
    builder.button(text="📈 Progress", callback_data=encode(ACTION_PROGRESS))
    builder.adjust(1)
    return builder.as_markup()


def library_list_keyboard(libraries: list[LibraryInfo]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for library in libraries:
        builder.button(
            text=library.title,
            callback_data=encode(ACTION_SELECT_LIBRARY, l=library.library_id),
        )
    builder.button(text="Back", callback_data=encode(ACTION_BACK, t="MM"))
    builder.adjust(1)
    return builder.as_markup()


def module_list_keyboard(
    library_id: str, modules: list[ModuleInfo]
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for module in modules:
        builder.button(
            text=module.title,
            callback_data=encode(
                ACTION_SELECT_MODULE, l=library_id, m=module.module_id
            ),
        )
    builder.button(text="Back", callback_data=encode(ACTION_BACK, t="LL"))
    builder.button(text="Home", callback_data=encode(ACTION_HOME))
    builder.adjust(1)
    return builder.as_markup()


def task_list_keyboard(
    library_id: str, module_id: str, tasks: list[TaskInfo], group_id: str | None = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task in tasks:
        data = (
            {"t": task.task_id}
            if group_id is not None
            else {"l": library_id, "m": module_id, "t": task.task_id}
        )
        builder.button(
            text=task.title,
            callback_data=encode(ACTION_SELECT_TASK, **data),
        )
    back_target = "GL" if group_id is not None else "ML"
    builder.button(text="Back", callback_data=encode(ACTION_BACK, t=back_target))
    builder.button(text="Home", callback_data=encode(ACTION_HOME))
    builder.adjust(1)
    return builder.as_markup()


def task_group_list_keyboard(
    library_id: str, module_id: str, groups: list[TaskGroupInfo]
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(
            text=group.title,
            callback_data=encode(
                ACTION_SELECT_TASK_GROUP,
                l=library_id,
                m=module_id,
                g=group.group_id,
            ),
        )
    builder.button(text="Back", callback_data=encode(ACTION_BACK, t="ML"))
    builder.button(text="Home", callback_data=encode(ACTION_HOME))
    builder.adjust(1)
    return builder.as_markup()


def task_overview_keyboard(
    library_id: str, module_id: str, task_id: str, group_id: str | None = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    data = {} if group_id is not None else {"l": library_id, "m": module_id, "t": task_id}
    builder.button(
        text="Start",
        callback_data=encode(ACTION_START_TASK, **data),
    )
    back_data = (
        {"t": "TL"} if group_id is not None else {"t": "TL", "l": library_id, "m": module_id}
    )
    builder.button(
        text="Back",
        callback_data=encode(ACTION_BACK, **back_data),
    )
    builder.button(text="Home", callback_data=encode(ACTION_HOME))
    builder.adjust(1)
    return builder.as_markup()


def task_in_progress_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Cancel", callback_data=encode(ACTION_CANCEL_TASK))
    builder.adjust(1)
    return builder.as_markup()


def task_result_keyboard(
    library_id: str,
    module_id: str,
    task_id: str,
    next_task_id: str | None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Retry",
        callback_data=encode(
            ACTION_RETRY_TASK,
            l=library_id,
            m=module_id,
            t=task_id,
        ),
    )
    if next_task_id:
        builder.button(
            text="Next task",
            callback_data=encode(
                ACTION_NEXT_TASK,
                l=library_id,
                m=module_id,
                t=next_task_id,
            ),
        )
    builder.button(
        text="Back to tasks",
        callback_data=encode(ACTION_BACK_TASKS, l=library_id, m=module_id),
    )
    builder.button(text="Home", callback_data=encode(ACTION_HOME))
    builder.adjust(1)
    return builder.as_markup()


def progress_overview_keyboard(libraries: list[LibraryInfo]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for library in libraries:
        builder.button(
            text=library.title,
            callback_data=encode(ACTION_PROGRESS_LIBRARY, l=library.library_id),
        )
    builder.button(text="Home", callback_data=encode(ACTION_HOME))
    builder.adjust(1)
    return builder.as_markup()


def progress_library_keyboard(
    library_id: str, modules: list[ModuleInfo]
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for module in modules:
        builder.button(
            text=module.title,
            callback_data=encode(
                ACTION_PROGRESS_MODULE,
                l=library_id,
                m=module.module_id,
            ),
        )
    builder.button(text="Back", callback_data=encode(ACTION_BACK, t="PO"))
    builder.button(text="Home", callback_data=encode(ACTION_HOME))
    builder.adjust(1)
    return builder.as_markup()


def progress_module_keyboard(
    library_id: str, module_id: str, tasks: list[TaskInfo]
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task in tasks:
        builder.button(
            text=task.title,
            callback_data=encode(
                ACTION_PROGRESS_TASK,
                l=library_id,
                m=module_id,
                t=task.task_id,
            ),
        )
    builder.button(text="Back", callback_data=encode(ACTION_BACK, t="PL"))
    builder.button(text="Home", callback_data=encode(ACTION_HOME))
    builder.adjust(1)
    return builder.as_markup()


def progress_task_details_keyboard(
    library_id: str, module_id: str, task_id: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Start task",
        callback_data=encode(
            ACTION_START_TASK,
            l=library_id,
            m=module_id,
            t=task_id,
        ),
    )
    builder.button(text="Back", callback_data=encode(ACTION_BACK, t="PM"))
    builder.button(text="Home", callback_data=encode(ACTION_HOME))
    builder.adjust(1)
    return builder.as_markup()
