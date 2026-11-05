"""Reachability check for the chatbot behind the dashboard's chat button."""
import os
import urllib.request

CHATBOT_URL = (
    f"http://{os.environ.get('CHATBOT_HOST', '127.0.0.1')}:"
    f"{os.environ.get('CHATBOT_PORT', '8001')}"
)
HEALTH_TIMEOUT_S = 1


def chatbot_is_up(url: str = CHATBOT_URL) -> bool:
    """True when the chatbot's /health answers 200 within the timeout."""
    try:
        with urllib.request.urlopen(f"{url}/health", timeout=HEALTH_TIMEOUT_S) as resp:
            return resp.status == 200
    except OSError:  # URLError, timeouts and refused connections all subclass OSError
        return False
