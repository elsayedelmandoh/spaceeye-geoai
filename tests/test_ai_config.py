"""Tests for AI configuration, approval controls, budgets, and prompt assets."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.inference.ai_config import (
    CallBudget,
    _read_dotenv,
    get_api_key,
    load_ai_config,
    require_approved,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "ai.yaml"
PROMPT_FILES = (
    REPO_ROOT / "prompts" / "system" / "inspection_agent.md",
    REPO_ROOT / "prompts" / "templates" / "inspection_paragraph.md",
    REPO_ROOT / "prompts" / "templates" / "visit_questions.md",
)
TEMPLATE_PLACEHOLDERS = {
    "inspection_paragraph.md": frozenset(
        {"facts_json", "code", "quarter", "level_word", "reason_ar"}
    ),
    "visit_questions.md": frozenset({"facts_json", "code", "quarter"}),
}


@pytest.fixture(autouse=True)
def isolate_process_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent a developer's real environment from affecting fabricated tests."""

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)


def _approved_config() -> dict:
    return {
        "gemini": {
            "model": "fabricated-model",
            "max_calls_total": 30,
            "max_calls_per_file": 3,
            "max_output_tokens": 1024,
            "temperature": 0,
            "approval": "approved",
        }
    }


def test_default_config_is_pending_and_calls_are_blocked(tmp_path: Path) -> None:
    config = load_ai_config(
        config_path=DEFAULT_CONFIG_PATH,
        env_path=tmp_path / "missing.env",
    )

    assert config["gemini"]["approval"] == "pending"
    with pytest.raises(RuntimeError, match="approved"):
        require_approved(config)


@pytest.mark.parametrize(
    "missing_field",
    ["model", "max_calls_total", "max_calls_per_file", "max_output_tokens"],
)
def test_approved_config_with_missing_field_is_rejected(missing_field: str) -> None:
    config = _approved_config()
    del config["gemini"][missing_field]

    with pytest.raises(RuntimeError, match=missing_field):
        require_approved(config)


def test_fully_set_approved_config_is_accepted() -> None:
    require_approved(_approved_config())


def test_call_budget_raises_after_total_limit() -> None:
    budget = CallBudget(max_calls_total=2, max_calls_per_file=3)

    budget.spend("C01")
    budget.spend("C02")
    with pytest.raises(RuntimeError, match="total"):
        budget.spend("C03")


def test_call_budget_raises_after_per_file_limit() -> None:
    budget = CallBudget(max_calls_total=3, max_calls_per_file=1)

    budget.spend("C01")
    with pytest.raises(RuntimeError, match="file"):
        budget.spend("C01")


def test_environment_model_overrides_yaml_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "ai.yaml"
    config_path.write_text("gemini:\n  model: fabricated-yaml-model\n", encoding="utf-8")
    monkeypatch.setenv("GEMINI_MODEL", "fabricated-environment-model")

    config = load_ai_config(
        config_path=config_path,
        env_path=tmp_path / "missing.env",
    )

    assert config["gemini"]["model"] == "fabricated-environment-model"


def test_dotenv_parser_reads_only_allowed_keys_and_strips_quotes(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        'GEMINI_API_KEY="fabricated-key"\n'
        "GEMINI_MODEL='fabricated-model'\n"
        'UNRELATED_SECRET="must-not-be-read"\n',
        encoding="utf-8",
    )

    parsed = _read_dotenv(env_path)

    assert parsed == {
        "GEMINI_API_KEY": "fabricated-key",
        "GEMINI_MODEL": "fabricated-model",
    }


def test_get_api_key_error_does_not_echo_fabricated_secret(
    tmp_path: Path,
) -> None:
    fabricated_secret = "fabricated-unrelated-secret"
    env_path = tmp_path / ".env"
    env_path.write_text(
        f"GEMINI_API_KEY {fabricated_secret}\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError) as error:
        get_api_key(env_path=env_path)

    assert str(error.value) == "GEMINI_API_KEY is not set"
    assert fabricated_secret not in str(error.value)


@pytest.mark.parametrize("prompt_path", PROMPT_FILES)
def test_prompt_files_exist_and_state_core_language_requirements(
    prompt_path: Path,
) -> None:
    assert prompt_path.is_file()
    text = prompt_path.read_text(encoding="utf-8")
    assert text.strip()
    assert "facts" in text.lower()
    assert "Arabic" in text


@pytest.mark.parametrize(
    ("template_name", "expected_placeholders"),
    TEMPLATE_PLACEHOLDERS.items(),
)
def test_template_placeholders_match_documented_set(
    template_name: str,
    expected_placeholders: frozenset[str],
) -> None:
    template_path = REPO_ROOT / "prompts" / "templates" / template_name
    text = template_path.read_text(encoding="utf-8")
    placeholders = set(re.findall(r"\{\{([a-z_]+)\}\}", text))

    assert placeholders == expected_placeholders


def test_generation_scaffold_blocks_pending_approval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.inference import generate

    monkeypatch.setenv("GEMINI_MODEL", "fabricated-environment-model")

    with pytest.raises(RuntimeError, match="approved"):
        generate.run_batch_generation(
            model=object(),
            tokenized_prompts=[],
            sampling_params={},
        )
