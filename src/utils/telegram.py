from __future__ import annotations

import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)


async def safe_answer_callback(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest as exc:
        message = str(exc).lower()
        if (
            "query is too old" in message
            or "query id is invalid" in message
            or "query is already answered" in message
        ):
            logger.info("Callback answer skipped: %s", exc)
            return
        raise
