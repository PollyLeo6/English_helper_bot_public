from __future__ import annotations

from src.app.config import AppConfig
from src.core.ports import Scorer
from src.core.services import ProgressService, ScoringService
from src.infra.libraries import TaskLibraryRegistry
from src.infra.scoring import LLMScorer, RuleScorer
from src.infra.storage import FileBotStateStore, FileUserEventStore


def build_services(config: AppConfig) -> dict[str, object]:
    registry = TaskLibraryRegistry(config.libraries_path)
    event_store = FileUserEventStore(config.data_path)
    state_store = FileBotStateStore(config.data_path)
    scorer: Scorer
    if config.scoring_mode == "llm":
        scorer = LLMScorer(
            api_key=config.llm_api_key or "",
            model=config.llm_model or "",
            base_url=config.llm_base_url or "https://api.openai.com/v1",
        )
    else:
        scorer = RuleScorer()
    scoring_service = ScoringService(scorer)
    progress_service = ProgressService(registry, event_store)
    return {
        "registry": registry,
        "event_store": event_store,
        "state_store": state_store,
        "scoring_service": scoring_service,
        "progress_service": progress_service,
    }
