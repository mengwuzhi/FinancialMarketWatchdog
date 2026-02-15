"""APScheduler background scheduler integration."""

import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.dependencies import get_notifier, get_state_manager
from config.scheduler_config import MONITOR_JOBS, CRAWLER_JOBS
from core.trading_calendar import TradingCalendar

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> Optional[BackgroundScheduler]:
    """Return the global scheduler instance."""
    return _scheduler


def _wrap_job(func, job_id: str, trading_day_only: bool = False):
    """Wrap job function with trading day check and error handling."""
    def wrapper():
        if trading_day_only:
            calendar = TradingCalendar()
            today = datetime.now().date()
            if not calendar.is_a_share_trading_day(today):
                logger.info("[%s] Skipped: not a trading day", job_id)
                return

        try:
            logger.info("[%s] Started", job_id)
            func()
            logger.info("[%s] Completed", job_id)
        except Exception as e:
            logger.error("[%s] Failed: %s", job_id, e, exc_info=True)

    wrapper.__name__ = f"wrapped_{job_id}"
    return wrapper


# ─── Monitor Job Handlers ─────────────────────────────────────

def _job_a_share_daily_report():
    """A-share daily report."""
    from monitors.a_share_monitor import AShareDailyReporter
    reporter = AShareDailyReporter(notifier=get_notifier())
    reporter.generate_report()


def _job_us_stock_daily_report():
    """US stock daily report."""
    from monitors.us_stock_monitor import USStockDailyReporter
    reporter = USStockDailyReporter(notifier=get_notifier())
    reporter.generate_report()


def _job_rss_article_monitor():
    """RSS article monitor."""
    from analyzers.ai_analyzer import AIAnalyzer
    from analyzers.rss_fetcher import RSSFetcher

    s = get_settings()
    if not s.rss_feed_url:
        logger.warning("RSS_FEED_URL not configured, skipping")
        return

    ai = AIAnalyzer(
        provider=s.ai_provider,
        api_key=s.ai_api_key,
        api_base_url=s.ai_api_base_url,
        model=s.ai_model,
        enable_search=s.ai_enable_search,
    )
    fetcher = RSSFetcher(
        feed_url=s.rss_feed_url,
        state_manager=get_state_manager(),
        ai_analyzer=ai,
        notifier=get_notifier(),
    )
    fetcher.check_and_analyze()


# ─── Crawler Job Handlers ─────────────────────────────────────

def _job_crawler_news():
    """News crawler."""
    from data_crawler.crawlers.news_crawler import fetch_all_news
    fetch_all_news()


def _job_crawler_realtime():
    """Realtime price crawler."""
    from data_crawler.crawlers.realtime_crawler import fetch_realtime_all
    fetch_realtime_all()


def _job_crawler_catchup():
    """Index historical catchup."""
    from data_crawler.crawlers.index_crawler import fetch_all_indices
    fetch_all_indices()


def _job_crawler_daily_us():
    """US index daily K-line."""
    from data_crawler.crawlers.index_crawler import fetch_today_indices
    fetch_today_indices()


def _job_crawler_futures():
    """Futures rollover signal."""
    from data_crawler.crawlers.futures_crawler import check_rollover_all
    check_rollover_all()


def _job_crawler_daily_cn_hk():
    """CN/HK index daily K-line."""
    from data_crawler.crawlers.index_crawler import fetch_today_indices
    fetch_today_indices()


def _job_crawler_daily_crypto_fx():
    """Crypto/FX daily K-line."""
    from data_crawler.crawlers.crypto_fx_crawler import fetch_today_crypto_fx
    fetch_today_crypto_fx()


def _job_crawler_daily_commodities():
    """Commodity daily K-line."""
    from data_crawler.crawlers.commodity_crawler import fetch_today_commodities
    fetch_today_commodities()


# ─── Job ID to Handler Mapping ────────────────────────────────

JOB_HANDLERS = {
    "a_share_daily_report": _job_a_share_daily_report,
    "us_stock_daily_report": _job_us_stock_daily_report,
    "rss_article_monitor": _job_rss_article_monitor,
    "crawler_news": _job_crawler_news,
    "crawler_realtime": _job_crawler_realtime,
    "crawler_catchup": _job_crawler_catchup,
    "crawler_daily_us": _job_crawler_daily_us,
    "crawler_futures": _job_crawler_futures,
    "crawler_daily_cn_hk": _job_crawler_daily_cn_hk,
    "crawler_daily_crypto_fx": _job_crawler_daily_crypto_fx,
    "crawler_daily_commodities": _job_crawler_daily_commodities,
}


def start_scheduler():
    """Start the background scheduler with all jobs."""
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already started")
        return

    _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    # Add monitor jobs
    for job_cfg in MONITOR_JOBS:
        job_id = job_cfg["job_id"]
        handler = JOB_HANDLERS.get(job_id)
        if not handler:
            logger.error("No handler for job: %s", job_id)
            continue

        trading_day_only = job_cfg.get("trading_day_only", False)
        wrapped = _wrap_job(handler, job_id, trading_day_only)

        trigger_kwargs = {k: v for k, v in job_cfg.items() 
                          if k not in ["job_id", "trading_day_only"]}
        trigger = CronTrigger(**trigger_kwargs)

        _scheduler.add_job(
            func=wrapped,
            trigger=trigger,
            id=job_id,
            name=job_id,
            replace_existing=True,
        )
        logger.info("Registered monitor job: %s", job_id)

    # Add crawler jobs
    for job_cfg in CRAWLER_JOBS:
        job_id = job_cfg["job_id"]
        handler = JOB_HANDLERS.get(job_id)
        if not handler:
            logger.error("No handler for job: %s", job_id)
            continue

        wrapped = _wrap_job(handler, job_id, trading_day_only=False)

        trigger_kwargs = {k: v for k, v in job_cfg.items() if k != "job_id"}
        trigger = CronTrigger(**trigger_kwargs)

        _scheduler.add_job(
            func=wrapped,
            trigger=trigger,
            id=job_id,
            name=job_id,
            replace_existing=True,
        )
        logger.info("Registered crawler job: %s", job_id)

    _scheduler.start()
    logger.info("Scheduler started with %d jobs", len(_scheduler.get_jobs()))


def shutdown_scheduler():
    """Shutdown the scheduler."""
    global _scheduler

    if _scheduler is None:
        return

    _scheduler.shutdown(wait=True)
    _scheduler = None
    logger.info("Scheduler stopped")
