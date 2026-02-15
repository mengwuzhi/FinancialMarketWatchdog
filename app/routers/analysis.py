"""Analysis endpoints: RSS monitoring and AI article analysis."""

import logging
from threading import Thread

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import get_settings
from app.dependencies import get_notifier, get_state_manager
from analyzers.ai_analyzer import AIAnalyzer
from analyzers.rss_fetcher import RSSFetcher
from notifiers.dingtalk import DingTalkNotifier
from storage.state_manager import StateManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class ArticleRequest(BaseModel):
    content: str


def _build_ai_analyzer() -> AIAnalyzer:
    """Build AIAnalyzer from settings."""
    s = get_settings()
    return AIAnalyzer(
        provider=s.ai_provider,
        api_key=s.ai_api_key,
        api_base_url=s.ai_api_base_url,
        model=s.ai_model,
        enable_search=s.ai_enable_search,
    )


@router.post("/rss/check")
def trigger_rss_check(
    notifier: DingTalkNotifier = Depends(get_notifier),
    state_manager: StateManager = Depends(get_state_manager),
):
    """Trigger RSS feed check and AI analysis."""
    s = get_settings()
    if not s.rss_feed_url:
        return {"status": "error", "message": "RSS_FEED_URL not configured"}

    def _run():
        try:
            ai = _build_ai_analyzer()
            fetcher = RSSFetcher(
                feed_url=s.rss_feed_url,
                state_manager=state_manager,
                ai_analyzer=ai,
                notifier=notifier,
            )
            fetcher.check_and_analyze()
        except Exception as e:
            logger.error("RSS check failed: %s", e)

    Thread(target=_run, daemon=True).start()
    return {"status": "accepted", "message": "RSS check started"}


@router.post("/article")
def analyze_article(req: ArticleRequest):
    """Analyze article content with AI."""
    if not req.content.strip():
        return {"status": "error", "message": "Content is empty"}

    ai = _build_ai_analyzer()
    result = ai.analyze(req.content)
    return {"status": "ok", "analysis": result}
