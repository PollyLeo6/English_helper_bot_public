from __future__ import annotations

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.core.ports import BotStateStore


class StateLoaderMiddleware(BaseMiddleware):
    def __init__(self, store: BotStateStore) -> None:
        self._store = store

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        if user_id is not None:
            data["bot_state"] = self._store.get(user_id)
        data["state_store"] = self._store
        return await handler(event, data)
