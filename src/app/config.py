from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    bot_token: str
    scoring_mode: str
    llm_api_key: str | None
    llm_model: str | None
    llm_base_url: str | None
    libraries_path: Path
    data_path: Path
    log_path: Path

    @classmethod
    def from_env(cls) -> AppConfig:
        bot_token = os.environ.get("BOT_TOKEN", "").strip()
        if not bot_token:
            raise ValueError("BOT_TOKEN is required")
        scoring_mode = os.environ.get("SCORING_MODE", "rule").strip().lower()
        if scoring_mode not in {"rule", "llm"}:
            raise ValueError("SCORING_MODE must be 'rule' or 'llm'")
        llm_api_key = os.environ.get("LLM_API_KEY", "").strip() or None
        llm_model = os.environ.get("LLM_MODEL", "").strip() or None
        llm_base_url = os.environ.get("LLM_BASE_URL", "").strip() or None
        if scoring_mode == "llm":
            if not llm_api_key:
                raise ValueError("LLM_API_KEY is required when SCORING_MODE=llm")
            if not llm_model:
                raise ValueError("LLM_MODEL is required when SCORING_MODE=llm")
        libraries_path = Path(os.environ.get("LIBRARIES_PATH", "src/libraries"))
        data_path = Path(os.environ.get("DATA_PATH", "data"))
        log_path = Path(os.environ.get("LOG_PATH", "data/logs/app.log"))
        return cls(
            bot_token=bot_token,
            scoring_mode=scoring_mode,
            llm_api_key=llm_api_key,
            llm_model=llm_model,
            llm_base_url=llm_base_url,
            libraries_path=libraries_path,
            data_path=data_path,
            log_path=log_path,
        )
