from dataclasses import dataclass
from pathlib import Path
import os


CHATBOT_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = CHATBOT_DIR.parent
ENV_FILE = CHATBOT_DIR / ".env"


def load_local_env() -> None:
    """Load chatbot-specific environment variables."""
    if not ENV_FILE.exists():
        return

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")

        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    database_path: Path
    api_host: str
    api_port: int


def get_settings() -> Settings:
    load_local_env()

    database_path = Path(
        os.getenv(
            "SPACEYE_DB_PATH",
            str(
                REPO_ROOT
                / "artifacts"
                / "ready_data_v7"
                / "SpaceEye_R7_READY_DATA_2026-10-31_v7"
                / "spaceeye_ready.duckdb"
            ),
        )
    )

    if not database_path.is_absolute():
        database_path = REPO_ROOT / database_path

    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        # gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        gemini_model=os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite",
        database_path=database_path,
        api_host=os.getenv("CHATBOT_HOST", "127.0.0.1"),
        api_port=int(os.getenv("CHATBOT_PORT", "8001")),
    )
