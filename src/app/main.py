from __future__ import annotations

import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import cast

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from src.app.config import AppConfig
from src.app.di import build_services
from src.bot.middleware.error_handler import ErrorHandlerMiddleware
from src.bot.middleware.state_loader import StateLoaderMiddleware
from src.bot.router import build_router
from src.core.ports import BotStateStore


def _setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            RotatingFileHandler(
                log_path,
                maxBytes=5_000_000,
                backupCount=5,
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
    )


def _ensure_data_dirs(data_path: Path) -> None:
    (data_path / "users").mkdir(parents=True, exist_ok=True)
    (data_path / "logs").mkdir(parents=True, exist_ok=True)


async def main() -> None:
    load_dotenv()
    config = AppConfig.from_env()
    _setup_logging(config.log_path)
    _ensure_data_dirs(config.data_path)

    services = build_services(config)
    state_store = cast(BotStateStore, services["state_store"])

    bot = Bot(token=config.bot_token)
    dispatcher = Dispatcher()
    dispatcher.update.middleware(ErrorHandlerMiddleware())
    dispatcher.message.middleware(StateLoaderMiddleware(state_store))
    dispatcher.callback_query.middleware(StateLoaderMiddleware(state_store))
    dispatcher.include_router(build_router())
    dispatcher.workflow_data.update(services)

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())  # pragma: no cover
