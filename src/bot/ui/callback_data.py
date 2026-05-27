from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CallbackPayload:
    action: str
    data: dict[str, str]


def encode(action: str, **data: str) -> str:
    parts = [action]
    for key, value in data.items():
        parts.append(f"{key}={value}")
    return "|".join(parts)


def decode(payload: str) -> CallbackPayload:
    parts = payload.split("|")
    action = parts[0]
    data: dict[str, str] = {}
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            data[key] = value
    return CallbackPayload(action=action, data=data)
