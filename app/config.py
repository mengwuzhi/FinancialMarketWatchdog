"""Unified configuration using Pydantic BaseSettings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # ─── Database ─────────────────────────────────────────────
    db_host: str = "47.95.221.184"
    db_port: int = 18453
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "watchdog_db"

    # ─── DingTalk ─────────────────────────────────────────────
    ding_webhook: str = ""
    ding_secret: str = ""

    # ─── AI (Qwen) ────────────────────────────────────────────
    ai_provider: str = "qwen"
    ai_api_key: str = ""
    ai_api_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ai_model: str = "qwen-plus"
    ai_enable_search: bool = True

    # ─── RSS ──────────────────────────────────────────────────
    rss_feed_url: str = ""

    # ─── General ──────────────────────────────────────────────
    timezone: str = "Asia/Shanghai"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance (lives for the process lifetime)."""
    return Settings()
