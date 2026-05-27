from __future__ import annotations

from aiogram import Router

from src.bot.handlers import libraries, main_menu, progress, task_flow


def build_router() -> Router:
    router = Router()
    router.include_router(main_menu.router)
    router.include_router(libraries.router)
    router.include_router(task_flow.router)
    router.include_router(progress.router)
    return router
