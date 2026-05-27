from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from src.bot.ui import keyboards, renderers
from src.bot.ui.callback_data import decode
from src.core.models import State
from src.core.ports import BotStateStore

router = Router()


def _is_home(callback: CallbackQuery) -> bool:
    return decode(callback.data or "").action == keyboards.ACTION_HOME


@router.message(CommandStart())
async def start(message: Message, state_store: BotStateStore) -> None:
    if message.from_user is None:
        return
    user_id = message.from_user.id
    state_store.set(user_id, State.MAIN_MENU, {})
    await message.answer(
        renderers.main_menu_text(), reply_markup=keyboards.main_menu_keyboard()
    )


@router.callback_query(_is_home)
async def handle_home(callback: CallbackQuery, state_store: BotStateStore) -> None:
    if callback.from_user is None or callback.message is None:
        return
    user_id = callback.from_user.id
    state_store.set(user_id, State.MAIN_MENU, {})
    await callback.message.answer(
        renderers.main_menu_text(), reply_markup=keyboards.main_menu_keyboard()
    )
    await callback.answer()
