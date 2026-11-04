import os
from dataclasses import dataclass
from pathlib import Path

from src.inference.ai_config import get_api_key, load_ai_config

CHATBOT_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = CHATBOT_DIR.parent


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    database_path: Path
    api_host: str
    api_port: int


def _api_key_or_empty() -> str:
    """The project Gemini key; else the key in chatbot/.env (start.ps1 flow); else "" for the non-model path."""
    for env_path in (None, CHATBOT_DIR / ".env"):
        try:
            return get_api_key() if env_path is None else get_api_key(env_path)
        except RuntimeError:
            continue
    return ""


def get_settings() -> Settings:
    # Default: the release unpacked by setup_review next to app_data (follows SPACEEYE_DATA_ROOT).
    from src.pipeline.common import APP

    database_path = Path(
        os.getenv("SPACEYE_DB_PATH", str(APP.parent / "ready-data" / "spaceeye_ready.duckdb"))
    )

    if not database_path.is_absolute():
        database_path = REPO_ROOT / database_path

    return Settings(
        gemini_api_key=_api_key_or_empty(),
        # Same model as the rest of the project; GEMINI_MODEL still overrides it.
        gemini_model=load_ai_config()["gemini"]["model"],
        database_path=database_path,
        api_host=os.getenv("CHATBOT_HOST", "127.0.0.1"),
        api_port=int(os.getenv("CHATBOT_PORT", "8001")),
    )
