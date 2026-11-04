"""Owner approval and call budget for chatbot Gemini calls (configs/ai.yaml `chatbot:`)."""

import json
import logging
from pathlib import Path

from src.inference.ai_config import load_ai_yaml_config, require_chatbot_approved

logger = logging.getLogger(__name__)

# Git-ignored (chatbot/vector_db/).
COUNTER_PATH = Path(__file__).resolve().parents[2] / "vector_db" / "gemini_calls.json"


def _read_count(path: Path) -> int:
    try:
        return int(json.loads(path.read_text(encoding="utf-8"))["calls"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def try_spend_gemini_call(counter_path: Path = COUNTER_PATH) -> bool:
    """Reserve one Gemini call; False when unapproved or the budget is used up.

    shortcut: not safe across several server processes, fine for one local app.
    """
    config = load_ai_yaml_config()
    try:
        require_chatbot_approved(config)
    except RuntimeError as exc:
        logger.info("Gemini call skipped: %s", exc)
        return False

    used = _read_count(counter_path)
    if used >= config["chatbot"]["max_calls_total"]:
        logger.warning("Gemini call budget used up (%s calls).", used)
        return False

    counter_path.parent.mkdir(parents=True, exist_ok=True)
    counter_path.write_text(json.dumps({"calls": used + 1}), encoding="utf-8")
    return True
