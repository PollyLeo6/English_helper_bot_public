from __future__ import annotations

from pathlib import Path


def user_dir(base: Path, user_id: int) -> Path:
    return base / "users" / str(user_id)


def events_dir(base: Path, user_id: int) -> Path:
    return user_dir(base, user_id) / "events"


def state_file(base: Path, user_id: int) -> Path:
    return user_dir(base, user_id) / "state.json"


def ensure_user_dirs(base: Path, user_id: int) -> None:
    events = events_dir(base, user_id)
    events.mkdir(parents=True, exist_ok=True)
    user_dir(base, user_id).mkdir(parents=True, exist_ok=True)
