from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery

from src.bot.ui import keyboards, renderers
from src.bot.ui.callback_data import decode
from src.core.models import State
from src.core.ports import BotStateStore, LibraryRegistry, UserEventStore

router = Router()


def _is_library_action(callback: CallbackQuery) -> bool:
    payload = decode(callback.data or "")
    if payload.action == keyboards.ACTION_BACK:
        return payload.data.get("t") in {"MM", "LL", "ML", "GL", "TL"}
    return payload.action in {
        keyboards.ACTION_DO_TASKS,
        keyboards.ACTION_SELECT_LIBRARY,
        keyboards.ACTION_SELECT_MODULE,
        keyboards.ACTION_SELECT_TASK_GROUP,
        keyboards.ACTION_SELECT_TASK,
    }


def _scores(
    event_store: UserEventStore,
    user_id: int,
    library_id: str,
    module_id: str,
) -> dict[str, tuple[float | None, float | None]]:
    scores: dict[str, tuple[float | None, float | None]] = {}
    events = event_store.list_events(
        user_id, library_id=library_id, module_id=module_id
    )
    grouped: dict[str, list[float]] = {}
    for event in events:
        grouped.setdefault(event.task_id, []).append(event.rating)
    for task_id, ratings in grouped.items():
        last = ratings[-1] if ratings else None
        mean = sum(ratings) / len(ratings) if ratings else None
        scores[task_id] = (last, mean)
    return scores


async def _show_library_list(
    callback: CallbackQuery, registry: LibraryRegistry, state_store: BotStateStore
) -> None:
    if callback.message is None or callback.from_user is None:
        return
    libraries = registry.list_libraries()
    user_id = callback.from_user.id
    state_store.set(user_id, State.LIBRARY_LIST, {})
    await callback.message.answer(
        renderers.library_list_text(libraries),
        reply_markup=keyboards.library_list_keyboard(libraries),
    )


async def _show_module_list(
    callback: CallbackQuery,
    registry: LibraryRegistry,
    state_store: BotStateStore,
    library_id: str,
) -> None:
    if callback.message is None or callback.from_user is None:
        return
    library = registry.get_library(library_id)
    modules = library.list_modules()
    user_id = callback.from_user.id
    state_store.set(user_id, State.MODULE_LIST, {"library_id": library_id})
    await callback.message.answer(
        renderers.module_list_text(library.info(), modules),
        reply_markup=keyboards.module_list_keyboard(library_id, modules),
    )


async def _show_task_list(
    callback: CallbackQuery,
    registry: LibraryRegistry,
    event_store: UserEventStore,
    state_store: BotStateStore,
    library_id: str,
    module_id: str,
    group_id: str | None = None,
) -> None:
    if callback.message is None or callback.from_user is None:
        return
    library = registry.get_library(library_id)
    module = library.get_module(module_id)
    tasks = module.list_tasks(group_id)
    scores = _scores(event_store, callback.from_user.id, library_id, module_id)
    user_id = callback.from_user.id
    state_store.set(
        user_id,
        State.TASK_LIST,
        {"library_id": library_id, "module_id": module_id, "group_id": group_id},
    )
    await callback.message.answer(
        renderers.task_list_text(module.info(), tasks, scores),
        reply_markup=keyboards.task_list_keyboard(
            library_id, module_id, tasks, group_id
        ),
    )


async def _show_task_group_list(
    callback: CallbackQuery,
    registry: LibraryRegistry,
    state_store: BotStateStore,
    library_id: str,
    module_id: str,
) -> None:
    if callback.message is None or callback.from_user is None:
        return
    module = registry.get_library(library_id).get_module(module_id)
    groups = module.list_task_groups()
    state_store.set(
        callback.from_user.id,
        State.TASK_LIST,
        {"library_id": library_id, "module_id": module_id},
    )
    await callback.message.answer(
        renderers.task_group_list_text(module.info(), groups),
        reply_markup=keyboards.task_group_list_keyboard(library_id, module_id, groups),
    )


async def _show_task_overview(
    callback: CallbackQuery,
    registry: LibraryRegistry,
    state_store: BotStateStore,
    library_id: str,
    module_id: str,
    task_id: str,
    group_id: str | None = None,
) -> None:
    if callback.message is None or callback.from_user is None:
        return
    task = registry.get_library(library_id).get_task(module_id, task_id)
    user_id = callback.from_user.id
    state_store.set(
        user_id,
        State.TASK_OVERVIEW,
        {
            "library_id": library_id,
            "module_id": module_id,
            "task_id": task_id,
            "group_id": group_id,
        },
    )
    await callback.message.answer(
        renderers.task_overview_text(task),
        reply_markup=keyboards.task_overview_keyboard(
            library_id, module_id, task_id, group_id
        ),
    )


@router.callback_query(_is_library_action)
async def handle_callbacks(
    callback: CallbackQuery,
    registry: LibraryRegistry,
    event_store: UserEventStore,
    state_store: BotStateStore,
) -> None:
    payload = decode(callback.data or "")
    if payload.action == keyboards.ACTION_DO_TASKS:
        await _show_library_list(callback, registry, state_store)
        await callback.answer()
        return
    if payload.action == keyboards.ACTION_SELECT_LIBRARY:
        library_id = payload.data["l"]
        await _show_module_list(callback, registry, state_store, library_id)
        await callback.answer()
        return
    if payload.action == keyboards.ACTION_SELECT_MODULE:
        if callback.from_user is None:
            return
        state = state_store.get(callback.from_user.id)
        library_id = payload.data.get("l") or state.context.get("library_id", "")
        module_id = payload.data["m"]
        module = registry.get_library(library_id).get_module(module_id)
        if module.has_task_groups():
            await _show_task_group_list(
                callback, registry, state_store, library_id, module_id
            )
        else:
            await _show_task_list(
                callback,
                registry,
                event_store,
                state_store,
                library_id,
                module_id,
            )
        await callback.answer()
        return
    if payload.action == keyboards.ACTION_SELECT_TASK_GROUP:
        if callback.from_user is None:
            return
        state = state_store.get(callback.from_user.id)
        library_id = payload.data.get("l") or state.context.get("library_id", "")
        module_id = payload.data.get("m") or state.context.get("module_id", "")
        await _show_task_list(
            callback,
            registry,
            event_store,
            state_store,
            library_id,
            module_id,
            payload.data["g"],
        )
        await callback.answer()
        return
    if payload.action == keyboards.ACTION_SELECT_TASK:
        if callback.from_user is None:
            return
        state = state_store.get(callback.from_user.id)
        library_id = payload.data.get("l") or state.context.get("library_id", "")
        module_id = payload.data.get("m") or state.context.get("module_id", "")
        group_id = payload.data.get("g") or state.context.get("group_id")
        await _show_task_overview(
            callback,
            registry,
            state_store,
            library_id,
            module_id,
            payload.data["t"],
            group_id,
        )
        await callback.answer()
        return
    if payload.action == keyboards.ACTION_BACK:
        target = payload.data.get("t")
        if callback.from_user is None:
            return
        state = state_store.get(callback.from_user.id)
        if target == "MM":
            if callback.message is None:
                return
            state_store.set(callback.from_user.id, State.MAIN_MENU, {})
            await callback.message.answer(
                renderers.main_menu_text(),
                reply_markup=keyboards.main_menu_keyboard(),
            )
        elif target == "LL":
            await _show_library_list(callback, registry, state_store)
        elif target == "ML":
            await _show_module_list(
                callback,
                registry,
                state_store,
                payload.data.get("l") or state.context.get("library_id", ""),
            )
        elif target == "GL":
            await _show_task_group_list(
                callback,
                registry,
                state_store,
                payload.data.get("l") or state.context.get("library_id", ""),
                payload.data.get("m") or state.context.get("module_id", ""),
            )
        elif target == "TL":
            await _show_task_list(
                callback,
                registry,
                event_store,
                state_store,
                payload.data.get("l") or state.context.get("library_id", ""),
                payload.data.get("m") or state.context.get("module_id", ""),
                payload.data.get("g") or state.context.get("group_id"),
            )
        await callback.answer()
