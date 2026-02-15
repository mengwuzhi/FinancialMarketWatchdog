"""FastAPI dependency injection."""

from functools import lru_cache

from app.config import get_settings
from notifiers.dingtalk import DingTalkNotifier
from storage.state_manager import StateManager


@lru_cache
def get_notifier() -> DingTalkNotifier:
    """Return cached DingTalkNotifier instance."""
    s = get_settings()
    return DingTalkNotifier(webhook_url=s.ding_webhook, secret=s.ding_secret)


@lru_cache
def get_state_manager() -> StateManager:
    """Return cached StateManager instance."""
    return StateManager()
