from __future__ import annotations

import uuid
from datetime import UTC, datetime


def make_event_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"event_{timestamp}_{uuid.uuid4().hex[:8]}"
