from __future__ import annotations

import json
from pathlib import Path

from src.core.models import BotState, State
from src.infra.storage.paths import ensure_user_dirs, state_file


class FileBotStateStore:
    def __init__(self, base_path: str | Path) -> None:
        self._base_path = Path(base_path)

    def get(self, user_id: int) -> BotState:
        path = state_file(self._base_path, user_id)
        if not path.exists():
            return BotState(user_id=user_id, state=State.MAIN_MENU, context={})
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return BotState.from_json(data)

    def set(self, user_id: int, state: State, context: dict) -> None:
        ensure_user_dirs(self._base_path, user_id)
        path = state_file(self._base_path, user_id)
        bot_state = BotState(user_id=user_id, state=state, context=context)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(bot_state.to_json(), handle, ensure_ascii=False, indent=2)

    def reset(self, user_id: int) -> None:
        path = state_file(self._base_path, user_id)
        if path.exists():
            path.unlink()
