from __future__ import annotations

import logging

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        try:
            return await handler(event, data)
        except Exception:  # pragma: no cover - safeguard in runtime
            logger.exception("Unhandled error")
            return None
