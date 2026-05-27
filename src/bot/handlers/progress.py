from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery

from src.bot.ui import keyboards, renderers
from src.bot.ui.callback_data import decode
from src.core.models import State
from src.core.ports import BotStateStore, LibraryRegistry
from src.core.services import ProgressService

router = Router()


def _is_progress_action(callback: CallbackQuery) -> bool:
    payload = decode(callback.data or "")
    if payload.action == keyboards.ACTION_BACK:
        return payload.data.get("t") in {"PO", "PL", "PM"}
    return payload.action in {
        keyboards.ACTION_PROGRESS,
        keyboards.ACTION_PROGRESS_LIBRARY,
        keyboards.ACTION_PROGRESS_MODULE,
        keyboards.ACTION_PROGRESS_TASK,
    }


async def _show_overview(
    callback: CallbackQuery,
    registry: LibraryRegistry,
    progress_service: ProgressService,
    state_store: BotStateStore,
) -> None:
    if callback.message is None or callback.from_user is None:
        return
    user_id = callback.from_user.id
    progress = progress_service.get_overall_progress(user_id)
    libraries = registry.list_libraries()
    state_store.set(user_id, State.PROGRESS_OVERVIEW, {})
    await callback.message.answer(
        renderers.progress_overview_text(progress),
        reply_markup=keyboards.progress_overview_keyboard(libraries),
    )


async def _show_library(
    callback: CallbackQuery,
    registry: LibraryRegistry,
    progress_service: ProgressService,
    state_store: BotStateStore,
    library_id: str,
) -> None:
    if callback.message is None or callback.from_user is None:
        return
    user_id = callback.from_user.id
    library = registry.get_library(library_id)
    progress = progress_service.get_library_progress(user_id, library_id)
    modules = library.list_modules()
    state_store.set(user_id, State.PROGRESS_LIBRARY, {"library_id": library_id})
    await callback.message.answer(
        renderers.progress_library_text(library.info(), progress),
        reply_markup=keyboards.progress_library_keyboard(library_id, modules),
    )


async def _show_module(
    callback: CallbackQuery,
    registry: LibraryRegistry,
    progress_service: ProgressService,
    state_store: BotStateStore,
    library_id: str,
    module_id: str,
) -> None:
    if callback.message is None or callback.from_user is None:
        return
    user_id = callback.from_user.id
    library = registry.get_library(library_id)
    module = library.get_module(module_id)
    progress = progress_service.get_module_progress(user_id, library_id, module_id)
    tasks = module.list_tasks()
    state_store.set(
        user_id,
        State.PROGRESS_MODULE,
        {"library_id": library_id, "module_id": module_id},
    )
    await callback.message.answer(
        renderers.progress_module_text(module.info(), progress),
        reply_markup=keyboards.progress_module_keyboard(library_id, module_id, tasks),
    )


async def _show_task_details(
    callback: CallbackQuery,
    registry: LibraryRegistry,
    progress_service: ProgressService,
    state_store: BotStateStore,
    library_id: str,
    module_id: str,
    task_id: str,
) -> None:
    if callback.message is None or callback.from_user is None:
        return
    user_id = callback.from_user.id
    library = registry.get_library(library_id)
    task_info = library.get_task_info(module_id, task_id)
    progress = progress_service.get_task_progress(
        user_id, library_id, module_id, task_id
    )
    state_store.set(
        user_id,
        State.PROGRESS_TASK_DETAILS,
        {"library_id": library_id, "module_id": module_id, "task_id": task_id},
    )
    await callback.message.answer(
        renderers.progress_task_details_text(task_info, progress),
        reply_markup=keyboards.progress_task_details_keyboard(
            library_id, module_id, task_id
        ),
    )


@router.callback_query(_is_progress_action)
async def handle_callbacks(
    callback: CallbackQuery,
    registry: LibraryRegistry,
    progress_service: ProgressService,
    state_store: BotStateStore,
) -> None:
    payload = decode(callback.data or "")
    if payload.action == keyboards.ACTION_PROGRESS:
        await _show_overview(callback, registry, progress_service, state_store)
        await callback.answer()
        return

    if payload.action == keyboards.ACTION_PROGRESS_LIBRARY:
        await _show_library(
            callback,
            registry,
            progress_service,
            state_store,
            payload.data["l"],
        )
        await callback.answer()
        return

    if payload.action == keyboards.ACTION_PROGRESS_MODULE:
        if callback.from_user is None:
            return
        state = state_store.get(callback.from_user.id)
        library_id = payload.data.get("l") or state.context.get("library_id", "")
        await _show_module(
            callback,
            registry,
            progress_service,
            state_store,
            library_id,
            payload.data["m"],
        )
        await callback.answer()
        return

    if payload.action == keyboards.ACTION_PROGRESS_TASK:
        if callback.from_user is None:
            return
        state = state_store.get(callback.from_user.id)
        library_id = payload.data.get("l") or state.context.get("library_id", "")
        module_id = payload.data.get("m") or state.context.get("module_id", "")
        await _show_task_details(
            callback,
            registry,
            progress_service,
            state_store,
            library_id,
            module_id,
            payload.data["t"],
        )
        await callback.answer()
        return

    if payload.action == keyboards.ACTION_BACK:
        if callback.from_user is None:
            return
        target = payload.data.get("t")
        state = state_store.get(callback.from_user.id)
        if target == "PO":
            await _show_overview(callback, registry, progress_service, state_store)
        elif target == "PL":
            await _show_library(
                callback,
                registry,
                progress_service,
                state_store,
                payload.data.get("l") or state.context.get("library_id", ""),
            )
        elif target == "PM":
            await _show_module(
                callback,
                registry,
                progress_service,
                state_store,
                payload.data.get("l") or state.context.get("library_id", ""),
                payload.data.get("m") or state.context.get("module_id", ""),
            )
        await callback.answer()
