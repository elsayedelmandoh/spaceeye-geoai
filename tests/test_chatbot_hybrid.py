"""Hybrid RAG chatbot: knowledge ingestion, shared Gemini config, approval budget (no network)."""

import json
from types import SimpleNamespace

import yaml

from chatbot.app.core import budget, config
from chatbot.app.generation import gemini_client, query_understanding
from chatbot.app.retrieval import knowledge

DOC = """---
title: "Sample Law"
source_url: "https://example.org/law"
retrieval_date: "2026-11-02"
kind: "law"
language: "en"
---

Intro text before any heading.

# Article 1

First article text.

## Article 2

Second article text.

```
# not a heading
```

# Empty section
"""


def test_knowledge_markdown_is_chunked_by_heading_with_source_metadata(tmp_path):
    (tmp_path / "sample.md").write_text(DOC, encoding="utf-8")

    chunks = knowledge.build_knowledge_chunks(tmp_path)

    sections = [c["metadata"]["section"] for c in chunks]
    assert sections == ["", "Article 1", "Article 2"]
    article = chunks[1]
    assert "First article text." in article["document"]
    assert article["metadata"] == {
        "document_type": "external_knowledge",
        "origin": "external_source",
        "title": "Sample Law",
        "section": "Article 1",
        "source_url": "https://example.org/law",
        "retrieval_date": "2026-11-02",
        "kind": "law",
        "language": "en",
        "file_path": article["metadata"]["file_path"],
    }
    assert article["metadata"]["file_path"].endswith("sample.md")
    assert "# not a heading" in chunks[2]["document"]
    assert len({c["id"] for c in chunks}) == len(chunks)


def test_repository_knowledge_files_all_produce_cited_chunks():
    chunks = knowledge.build_knowledge_chunks()

    files = {c["metadata"]["file_path"] for c in chunks}
    assert len(files) >= 9
    assert all(f.startswith("chatbot/knowledge/external/") for f in files)
    assert all(
        isinstance(v, str) for c in chunks for v in c["metadata"].values()
    )  # Chroma metadata must be scalar
    assert any(c["metadata"]["source_url"].startswith("http") for c in chunks)


def test_settings_use_project_model_and_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setattr(config, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        config, "load_ai_config", lambda: {"gemini": {"model": "model-from-yaml"}}
    )

    settings = config.get_settings()

    assert settings.gemini_model == "model-from-yaml"
    assert settings.gemini_api_key == "test-key"


def test_settings_model_matches_configs_ai_yaml_and_env_override(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setattr(config, "get_api_key", lambda: "k")
    from src.inference.ai_config import DEFAULT_CONFIG_PATH

    yaml_model = yaml.safe_load(DEFAULT_CONFIG_PATH.read_text("utf-8"))["gemini"]["model"]
    assert config.get_settings().gemini_model == yaml_model

    monkeypatch.setenv("GEMINI_MODEL", "override-model")
    assert config.get_settings().gemini_model == "override-model"


def test_missing_api_key_gives_empty_key_not_an_error(monkeypatch):
    def raise_missing():
        raise RuntimeError("GEMINI_API_KEY is not set")

    monkeypatch.setattr(config, "get_api_key", raise_missing)

    assert config.get_settings().gemini_api_key == ""


def _set_chatbot_config(monkeypatch, approval, max_calls):
    monkeypatch.setattr(
        budget,
        "load_ai_yaml_config",
        lambda: {"chatbot": {"approval": approval, "max_calls_total": max_calls}},
    )


def test_repository_config_is_approved_with_200_calls():
    chatbot = yaml.safe_load(
        (budget.COUNTER_PATH.parents[2] / "configs" / "ai.yaml").read_text("utf-8")
    )["chatbot"]

    assert chatbot == {"approval": "approved", "max_calls_total": 200}


def test_budget_stops_after_max_calls(monkeypatch, tmp_path):
    _set_chatbot_config(monkeypatch, "approved", 2)
    counter = tmp_path / "calls.json"

    results = [budget.try_spend_gemini_call(counter) for _ in range(3)]

    assert results == [True, True, False]
    assert json.loads(counter.read_text("utf-8")) == {"calls": 2}


def test_budget_refuses_when_approval_is_pending(monkeypatch, tmp_path):
    _set_chatbot_config(monkeypatch, "pending", 200)
    counter = tmp_path / "calls.json"

    assert budget.try_spend_gemini_call(counter) is False
    assert not counter.exists()


class _FailingClient:
    def __init__(self, *args, **kwargs):
        raise AssertionError("Gemini must not be called")


def _fake_settings():
    return SimpleNamespace(gemini_api_key="test-key", gemini_model="m")


def test_answer_generation_makes_no_gemini_call_when_pending(monkeypatch, tmp_path):
    _set_chatbot_config(monkeypatch, "pending", 200)
    monkeypatch.setattr(budget, "COUNTER_PATH", tmp_path / "calls.json")
    monkeypatch.setattr(gemini_client, "get_settings", _fake_settings)
    monkeypatch.setattr(gemini_client.genai, "Client", _FailingClient)
    monkeypatch.setattr(gemini_client, "try_spend_gemini_call", budget.try_spend_gemini_call)

    answer = gemini_client.generate_answer("q", "some evidence", fallback_answer="local answer")

    assert answer == "local answer"


def test_query_understanding_makes_no_gemini_call_when_pending(monkeypatch, tmp_path):
    _set_chatbot_config(monkeypatch, "pending", 200)
    monkeypatch.setattr(query_understanding, "get_settings", _fake_settings)
    monkeypatch.setattr(query_understanding.genai, "Client", _FailingClient)
    monkeypatch.setattr(
        query_understanding,
        "try_spend_gemini_call",
        lambda: budget.try_spend_gemini_call(tmp_path / "calls.json"),
    )

    result = query_understanding.understand_query("ما هي حالة المشروع C04؟")

    assert result["understanding_mode"] == "keyword_fallback"


def test_answer_generation_calls_mocked_gemini_when_approved(monkeypatch, tmp_path):
    _set_chatbot_config(monkeypatch, "approved", 5)
    counter = tmp_path / "calls.json"
    monkeypatch.setattr(
        gemini_client, "try_spend_gemini_call", lambda: budget.try_spend_gemini_call(counter)
    )
    monkeypatch.setattr(gemini_client, "get_settings", _fake_settings)

    class FakeClient:
        def __init__(self, api_key):
            self.models = SimpleNamespace(
                generate_content=lambda **kw: SimpleNamespace(text="model answer")
            )

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(gemini_client.genai, "Client", FakeClient)

    assert gemini_client.generate_answer("q", "evidence", "local") == "model answer"
    assert json.loads(counter.read_text("utf-8")) == {"calls": 1}


def test_api_key_falls_back_to_chatbot_env(monkeypatch):
    """start.ps1 puts the key in chatbot/.env; the project key is tried first."""
    from chatbot.app.core import config

    calls = []

    def fake_get_api_key(env_path=None):
        calls.append(env_path)
        if env_path is None:
            raise RuntimeError("GEMINI_API_KEY is not set")
        return "key-from-chatbot-env"

    monkeypatch.setattr(config, "get_api_key", fake_get_api_key)
    assert config._api_key_or_empty() == "key-from-chatbot-env"
    assert calls == [None, config.CHATBOT_DIR / ".env"]
