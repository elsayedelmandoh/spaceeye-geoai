import urllib.error

from src.dashboard import chatbot_status


class _Resp:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_chatbot_is_up_when_health_returns_200(monkeypatch):
    monkeypatch.setattr(chatbot_status.urllib.request, "urlopen", lambda *a, **k: _Resp(200))
    assert chatbot_status.chatbot_is_up("http://x") is True


def test_chatbot_is_down_when_connection_fails(monkeypatch):
    def refuse(*a, **k):
        raise urllib.error.URLError("refused")

    monkeypatch.setattr(chatbot_status.urllib.request, "urlopen", refuse)
    assert chatbot_status.chatbot_is_up("http://x") is False
