"""Load AI configuration and enforce approval and call-budget controls."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "ai.yaml"
DEFAULT_ENV_PATH = REPO_ROOT / ".env"
_ALLOWED_ENV_KEYS = frozenset({"GEMINI_API_KEY", "GEMINI_MODEL"})
_REQUIRED_APPROVED_FIELDS = (
    "model",
    "max_calls_total",
    "max_calls_per_file",
    "max_output_tokens",
)


def _read_dotenv(path: Path) -> dict[str, str]:
    """Read only the two supported keys from a local environment file."""

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeError):
        raise RuntimeError("Unable to read the local AI environment file") from None

    values: dict[str, str] = {}
    for raw_line in lines:
        key, separator, raw_value = raw_line.partition("=")
        key = key.strip()
        if not separator or key not in _ALLOWED_ENV_KEYS:
            continue
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def _read_yaml_config(path: Path) -> dict[str, Any]:
    """Read the AI configuration as a mapping without exposing file contents."""

    try:
        parsed_config = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        raise RuntimeError("Unable to read the AI configuration file") from None
    except yaml.YAMLError:
        raise RuntimeError("The AI configuration file is not valid YAML") from None

    if not isinstance(parsed_config, dict):
        raise RuntimeError("The AI configuration must be a mapping")  # noqa: TRY004
    return parsed_config


def load_ai_config(
    config_path: str | Path | None = None,
    env_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load the AI configuration and apply a non-empty environment model override."""

    config_file = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    env_file = Path(env_path) if env_path is not None else DEFAULT_ENV_PATH
    config = _read_yaml_config(config_file)
    gemini = config.get("gemini")
    if not isinstance(gemini, dict):
        raise RuntimeError("The AI configuration must contain a gemini block")  # noqa: TRY004

    model_override = os.environ.get("GEMINI_MODEL")
    if model_override is None:
        model_override = _read_dotenv(env_file).get("GEMINI_MODEL")
    if model_override:
        gemini["model"] = model_override
    return config


def load_ai_yaml_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load the AI YAML without consulting environment-backed credential settings."""

    config_file = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    return _read_yaml_config(config_file)


def get_api_key(env_path: str | Path | None = None) -> str:
    """Return the API key from the process environment or the local environment file."""

    env_file = Path(env_path) if env_path is not None else DEFAULT_ENV_PATH
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key is None:
        api_key = _read_dotenv(env_file).get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return api_key


def require_approved(config: Mapping[str, Any]) -> None:
    """Require owner approval and the fields needed for a bounded provider call."""

    gemini = config.get("gemini")
    if not isinstance(gemini, Mapping):
        raise RuntimeError("The AI configuration must contain a gemini block")  # noqa: TRY004
    if gemini.get("approval") != "approved":
        raise RuntimeError(
            "AI calls are not approved: set gemini.approval to 'approved' after owner confirmation"
        )

    for field in _REQUIRED_APPROVED_FIELDS:
        field_value = gemini.get(field)
        if field_value is None or (
            isinstance(field_value, str) and not field_value.strip()
        ):
            raise RuntimeError(f"AI configuration is missing required field: gemini.{field}")


def require_chatbot_approved(config: Mapping[str, Any]) -> None:
    """Require independent chatbot approval and a positive total-call budget."""

    chatbot = config.get("chatbot")
    if not isinstance(chatbot, Mapping):
        raise RuntimeError("AI configuration must contain a chatbot block")  # noqa: TRY004
    if chatbot.get("approval") != "approved":
        raise RuntimeError(
            "Chatbot model calls are not approved: set chatbot.approval to 'approved' "
            "after owner confirmation"
        )
    max_calls_total = chatbot.get("max_calls_total")
    if (
        isinstance(max_calls_total, bool)
        or not isinstance(max_calls_total, int)
        or max_calls_total <= 0
    ):
        raise RuntimeError(
            "Chatbot configuration requires a positive integer: chatbot.max_calls_total"
        )


class CallBudget:
    """Enforce total and per-file limits for provider calls."""

    def __init__(self, max_calls_total: int, max_calls_per_file: int) -> None:
        self.max_calls_total = max_calls_total
        self.max_calls_per_file = max_calls_per_file
        self._total_calls = 0
        self._calls_by_file: dict[str, int] = {}

    def spend(self, file_id: str) -> None:
        """Record one call or raise before the applicable limit is exceeded."""

        if self._total_calls >= self.max_calls_total:
            raise RuntimeError("AI call budget total limit reached")
        file_calls = self._calls_by_file.get(file_id, 0)
        if file_calls >= self.max_calls_per_file:
            raise RuntimeError("AI call budget per-file limit reached")
        self._total_calls += 1
        self._calls_by_file[file_id] = file_calls + 1
