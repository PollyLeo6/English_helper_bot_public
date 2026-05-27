from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from src.bot.ui import keyboards, renderers
from src.bot.ui.callback_data import decode
from src.core.models import BotState, ScoreResult, State
from src.core.ports import BotStateStore, LibraryRegistry, UserEventStore
from src.core.services import ProgressService, ScoringService, TaskSession

router = Router()


def _is_task_action(callback: CallbackQuery) -> bool:
    return decode(callback.data or "").action in {
        keyboards.ACTION_START_TASK,
        keyboards.ACTION_CANCEL_TASK,
        keyboards.ACTION_RETRY_TASK,
        keyboards.ACTION_NEXT_TASK,
        keyboards.ACTION_BACK_TASKS,
    }


def _next_task_id(
    registry: LibraryRegistry, library_id: str, module_id: str, task_id: str
) -> str | None:
    module = registry.get_library(library_id).get_module(module_id)
    tasks = module.list_tasks()
    for idx, info in enumerate(tasks):
        if info.task_id == task_id and idx + 1 < len(tasks):
            return tasks[idx + 1].task_id
    return None


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


async def _send_current_state(
    message: Message,
    bot_state: BotState,
    registry: LibraryRegistry,
    event_store: UserEventStore,
    progress_service: ProgressService,
    state_store: BotStateStore,
) -> None:
    if message.from_user is None:
        return
    user_id = message.from_user.id
    state = bot_state.state
    context = bot_state.context

    if state == State.MAIN_MENU:
        await message.answer(
            renderers.main_menu_text(), reply_markup=keyboards.main_menu_keyboard()
        )
        return

    if state == State.LIBRARY_LIST:
        libraries = registry.list_libraries()
        await message.answer(
            renderers.library_list_text(libraries),
            reply_markup=keyboards.library_list_keyboard(libraries),
        )
        return

    if state == State.MODULE_LIST:
        library_id = context.get("library_id", "")
        if not library_id or not registry.library_exists(library_id):
            state_store.set(user_id, State.LIBRARY_LIST, {})
            libraries = registry.list_libraries()
            await message.answer(
                renderers.library_list_text(libraries),
                reply_markup=keyboards.library_list_keyboard(libraries),
            )
            return
        library = registry.get_library(library_id)
        modules = library.list_modules()
        await message.answer(
            renderers.module_list_text(library.info(), modules),
            reply_markup=keyboards.module_list_keyboard(library_id, modules),
        )
        return

    if state == State.TASK_LIST:
        library_id = context.get("library_id", "")
        module_id = context.get("module_id", "")
        group_id = context.get("group_id")
        if not library_id or not module_id or not registry.library_exists(library_id):
            state_store.set(user_id, State.LIBRARY_LIST, {})
            libraries = registry.list_libraries()
            await message.answer(
                renderers.library_list_text(libraries),
                reply_markup=keyboards.library_list_keyboard(libraries),
            )
            return
        module = registry.get_library(library_id).get_module(module_id)
        tasks = module.list_tasks(group_id)
        scores = _scores(event_store, user_id, library_id, module_id)
        await message.answer(
            renderers.task_list_text(module.info(), tasks, scores),
            reply_markup=keyboards.task_list_keyboard(
                library_id, module_id, tasks, group_id
            ),
        )
        return

    if state == State.TASK_OVERVIEW:
        library_id = context.get("library_id", "")
        module_id = context.get("module_id", "")
        task_id = context.get("task_id", "")
        group_id = context.get("group_id")
        if not library_id or not module_id or not task_id:
            state_store.set(user_id, State.LIBRARY_LIST, {})
            libraries = registry.list_libraries()
            await message.answer(
                renderers.library_list_text(libraries),
                reply_markup=keyboards.library_list_keyboard(libraries),
            )
            return
        task = registry.get_library(library_id).get_task(module_id, task_id)
        await message.answer(
            renderers.task_overview_text(task),
            reply_markup=keyboards.task_overview_keyboard(
                library_id, module_id, task_id, group_id
            ),
        )
        return

    if state == State.TASK_IN_PROGRESS:
        library_id = context.get("library_id", "")
        module_id = context.get("module_id", "")
        task_id = context.get("task_id", "")
        group_id = context.get("group_id")
        if not library_id or not module_id or not task_id:
            state_store.set(user_id, State.LIBRARY_LIST, {})
            libraries = registry.list_libraries()
            await message.answer(
                renderers.library_list_text(libraries),
                reply_markup=keyboards.library_list_keyboard(libraries),
            )
            return
        task = registry.get_library(library_id).get_task(module_id, task_id)
        try:
            items = task.pairs()
        except ValueError:
            state_store.set(
                user_id,
                State.TASK_OVERVIEW,
                {"library_id": library_id, "module_id": module_id, "task_id": task_id},
            )
            await message.answer(
                "Task data is invalid. Please choose another task.",
                reply_markup=keyboards.task_overview_keyboard(
                    library_id, module_id, task_id, group_id
                ),
            )
            return
        if not items:
            state_store.set(
                user_id,
                State.TASK_OVERVIEW,
                {"library_id": library_id, "module_id": module_id, "task_id": task_id},
            )
            await message.answer(
                "This task has no items yet. Please choose another task.",
                reply_markup=keyboards.task_overview_keyboard(
                    library_id, module_id, task_id, group_id
                ),
            )
            return
        index = int(context.get("index", 0))
        if index < 0:
            index = 0
        if index >= len(items):
            index = max(len(items) - 1, 0)
        await message.answer(
            renderers.task_prompt_text(task, index),
            reply_markup=keyboards.task_in_progress_keyboard(),
        )
        return

    if state == State.TASK_RESULT:
        library_id = context.get("library_id", "")
        module_id = context.get("module_id", "")
        task_id = context.get("task_id", "")
        next_task_id = context.get("next_task_id")
        score = context.get("score")
        feedback = context.get("feedback")
        mode = context.get("mode", "rule")
        if score is None or feedback is None:
            if library_id and module_id and task_id:
                last = event_store.get_last_event(
                    user_id, library_id, module_id, task_id
                )
            else:
                last = None
            if last:
                score = last.rating
                feedback = last.feedback
        result = ScoreResult(
            score=float(score) if score is not None else 0.0,
            feedback=str(feedback) if feedback is not None else "No results yet.",
            items=[],
            mode=str(mode),
        )
        if next_task_id is None and library_id and module_id and task_id:
            next_task_id = _next_task_id(registry, library_id, module_id, task_id)
        await message.answer(
            renderers.task_result_text(result),
            reply_markup=keyboards.task_result_keyboard(
                library_id, module_id, task_id, next_task_id
            ),
        )
        return

    if state == State.PROGRESS_OVERVIEW:
        overall_progress = progress_service.get_overall_progress(user_id)
        libraries = registry.list_libraries()
        await message.answer(
            renderers.progress_overview_text(overall_progress),
            reply_markup=keyboards.progress_overview_keyboard(libraries),
        )
        return

    if state == State.PROGRESS_LIBRARY:
        library_id = context.get("library_id", "")
        if not library_id:
            state_store.set(user_id, State.PROGRESS_OVERVIEW, {})
            overall_progress = progress_service.get_overall_progress(user_id)
            libraries = registry.list_libraries()
            await message.answer(
                renderers.progress_overview_text(overall_progress),
                reply_markup=keyboards.progress_overview_keyboard(libraries),
            )
            return
        library = registry.get_library(library_id)
        library_progress = progress_service.get_library_progress(user_id, library_id)
        modules = library.list_modules()
        await message.answer(
            renderers.progress_library_text(library.info(), library_progress),
            reply_markup=keyboards.progress_library_keyboard(library_id, modules),
        )
        return

    if state == State.PROGRESS_MODULE:
        library_id = context.get("library_id", "")
        module_id = context.get("module_id", "")
        if not library_id or not module_id:
            state_store.set(user_id, State.PROGRESS_OVERVIEW, {})
            overall_progress = progress_service.get_overall_progress(user_id)
            libraries = registry.list_libraries()
            await message.answer(
                renderers.progress_overview_text(overall_progress),
                reply_markup=keyboards.progress_overview_keyboard(libraries),
            )
            return
        module = registry.get_library(library_id).get_module(module_id)
        module_progress = progress_service.get_module_progress(
            user_id, library_id, module_id
        )
        tasks = module.list_tasks()
        await message.answer(
            renderers.progress_module_text(module.info(), module_progress),
            reply_markup=keyboards.progress_module_keyboard(
                library_id, module_id, tasks
            ),
        )
        return

    if state == State.PROGRESS_TASK_DETAILS:
        library_id = context.get("library_id", "")
        module_id = context.get("module_id", "")
        task_id = context.get("task_id", "")
        if not library_id or not module_id or not task_id:
            state_store.set(user_id, State.PROGRESS_OVERVIEW, {})
            overall_progress = progress_service.get_overall_progress(user_id)
            libraries = registry.list_libraries()
            await message.answer(
                renderers.progress_overview_text(overall_progress),
                reply_markup=keyboards.progress_overview_keyboard(libraries),
            )
            return
        library = registry.get_library(library_id)
        task_info = library.get_task_info(module_id, task_id)
        task_progress = progress_service.get_task_progress(
            user_id, library_id, module_id, task_id
        )
        await message.answer(
            renderers.progress_task_details_text(task_info, task_progress),
            reply_markup=keyboards.progress_task_details_keyboard(
                library_id, module_id, task_id
            ),
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
    module = registry.get_library(library_id).get_module(module_id)
    tasks = module.list_tasks(group_id)
    scores: dict[str, tuple[float | None, float | None]] = {}
    events = event_store.list_events(callback.from_user.id, library_id, module_id)
    grouped: dict[str, list[float]] = {}
    for event in events:
        grouped.setdefault(event.task_id, []).append(event.rating)
    for task_id, ratings in grouped.items():
        scores[task_id] = (ratings[-1], sum(ratings) / len(ratings))
    state_store.set(
        callback.from_user.id,
        State.TASK_LIST,
        {"library_id": library_id, "module_id": module_id, "group_id": group_id},
    )
    await callback.message.answer(
        renderers.task_list_text(module.info(), tasks, scores),
        reply_markup=keyboards.task_list_keyboard(
            library_id, module_id, tasks, group_id
        ),
    )


async def _start_task(
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
    try:
        items = task.pairs()
    except ValueError:
        await callback.message.answer(
            "Task data is invalid. Please choose another task.",
            reply_markup=keyboards.task_overview_keyboard(
                library_id, module_id, task_id
            ),
        )
        return
    if not items:
        await callback.message.answer(
            "This task has no items yet. Please choose another task.",
            reply_markup=keyboards.task_overview_keyboard(
                library_id, module_id, task_id
            ),
        )
        return
    user_id = callback.from_user.id
    state_store.set(
        user_id,
        State.TASK_IN_PROGRESS,
        {
            "library_id": library_id,
            "module_id": module_id,
            "task_id": task_id,
            "group_id": group_id,
            "answers": [],
            "index": 0,
        },
    )
    await callback.message.answer(
        renderers.task_prompt_text(task, 0),
        reply_markup=keyboards.task_in_progress_keyboard(),
    )


@router.callback_query(_is_task_action)
async def handle_callbacks(
    callback: CallbackQuery,
    registry: LibraryRegistry,
    event_store: UserEventStore,
    state_store: BotStateStore,
) -> None:
    payload = decode(callback.data or "")
    if payload.action == keyboards.ACTION_START_TASK:
        if callback.from_user is None:
            return
        state = state_store.get(callback.from_user.id)
        library_id = payload.data.get("l") or state.context.get("library_id", "")
        module_id = payload.data.get("m") or state.context.get("module_id", "")
        task_id = payload.data.get("t") or state.context.get("task_id", "")
        group_id = payload.data.get("g") or state.context.get("group_id")
        await _start_task(
            callback,
            registry,
            state_store,
            library_id,
            module_id,
            task_id,
            group_id,
        )
        await callback.answer()
        return

    if payload.action == keyboards.ACTION_CANCEL_TASK:
        if callback.from_user is None:
            return
        state = state_store.get(callback.from_user.id)
        await _show_task_overview(
            callback,
            registry,
            state_store,
            state.context.get("library_id", ""),
            state.context.get("module_id", ""),
            state.context.get("task_id", ""),
            state.context.get("group_id"),
        )
        await callback.answer()
        return

    if payload.action == keyboards.ACTION_RETRY_TASK:
        if callback.from_user is None:
            return
        state = state_store.get(callback.from_user.id)
        library_id = payload.data.get("l") or state.context.get("library_id", "")
        module_id = payload.data.get("m") or state.context.get("module_id", "")
        task_id = payload.data.get("t") or state.context.get("task_id", "")
        group_id = payload.data.get("g") or state.context.get("group_id")
        await _start_task(
            callback,
            registry,
            state_store,
            library_id,
            module_id,
            task_id,
            group_id,
        )
        await callback.answer()
        return

    if payload.action == keyboards.ACTION_NEXT_TASK:
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

    if payload.action == keyboards.ACTION_BACK_TASKS:
        if callback.from_user is None:
            return
        state = state_store.get(callback.from_user.id)
        library_id = payload.data.get("l") or state.context.get("library_id", "")
        module_id = payload.data.get("m") or state.context.get("module_id", "")
        group_id = payload.data.get("g") or state.context.get("group_id")
        await _show_task_list(
            callback,
            registry,
            event_store,
            state_store,
            library_id,
            module_id,
            group_id,
        )
        await callback.answer()
        return


@router.message()
async def handle_task_answers(
    message: Message,
    bot_state: BotState,
    registry: LibraryRegistry,
    scoring_service: ScoringService,
    event_store: UserEventStore,
    progress_service: ProgressService,
    state_store: BotStateStore,
) -> None:
    if message.text and message.text.startswith("/"):
        return
    if bot_state.state != State.TASK_IN_PROGRESS:
        await _send_current_state(
            message,
            bot_state,
            registry,
            event_store,
            progress_service,
            state_store,
        )
        return
    if message.from_user is None or not message.text:
        return
    context = bot_state.context
    library_id = context.get("library_id", "")
    module_id = context.get("module_id", "")
    task_id = context.get("task_id", "")
    group_id = context.get("group_id")
    answers: list[str] = list(context.get("answers", []))

    task = registry.get_library(library_id).get_task(module_id, task_id)
    session = TaskSession(
        user_id=message.from_user.id,
        library_id=library_id,
        module_id=module_id,
        scoring_service=scoring_service,
        event_store=event_store,
    )
    session.start(task)
    for answer in answers:
        session.submit_answer(answer)
    session.submit_answer(message.text)
    answers.append(message.text.strip())

    if session.is_complete():
        event, score = session.finish()
        event_store.append(event)
        next_task_id = _next_task_id(registry, library_id, module_id, task_id)
        state_store.set(
            message.from_user.id,
            State.TASK_RESULT,
            {
                "library_id": library_id,
                "module_id": module_id,
                "task_id": task_id,
                "group_id": group_id,
                "next_task_id": next_task_id,
                "score": score.score,
                "feedback": score.feedback,
                "mode": score.mode,
            },
        )
        await message.answer(
            renderers.task_result_text(score),
            reply_markup=keyboards.task_result_keyboard(
                library_id, module_id, task_id, next_task_id
            ),
        )
        return

    index = len(answers)
    state_store.set(
        message.from_user.id,
        State.TASK_IN_PROGRESS,
        {
            "library_id": library_id,
            "module_id": module_id,
            "task_id": task_id,
            "group_id": group_id,
            "answers": answers,
            "index": index,
        },
    )
    await message.answer(
        renderers.task_prompt_text(task, index),
        reply_markup=keyboards.task_in_progress_keyboard(),
    )
