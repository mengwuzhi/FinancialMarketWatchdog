"""
FinancialMarketWatchdog — Main Scheduler

APScheduler + Asia/Shanghai timezone

Schedule (all times CST / Asia/Shanghai):
  Every hour  :00  ->  财经新闻爬取
  Every hour  :05  ->  实时价格采集 (USD/CNH, BTC, ETH, GOLD, SILVER)
  Daily 03:00      ->  历史数据补齐 (指数 / 加密 / 贵金属)
  Daily 06:00      ->  美股前一交易日 K线
  Daily 14:30      ->  IC/IM 期货移仓信号检测
  Daily 15:30      ->  A股/港股 今日K线
  Daily 16:40      ->  加密/汇率 今日K线
  Daily 16:50      ->  贵金属 今日K线
  Startup          ->  立即执行一次历史补齐
"""
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool      import ThreadPoolExecutor
from apscheduler.triggers.cron       import CronTrigger
from apscheduler.triggers.date       import DateTrigger

from db.init_tables                  import init_all_tables
from crawlers.news_crawler           import fetch_all_news
from crawlers.index_crawler          import fetch_all_indices, fetch_today_indices
from crawlers.crypto_fx_crawler      import fetch_all_crypto_fx, fetch_today_crypto_fx
from crawlers.commodity_crawler      import fetch_all_commodities, fetch_today_commodities
from crawlers.futures_crawler        import check_and_save_rollover
from crawlers.realtime_crawler       import fetch_all_realtime

# ─── Logging ──────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR   = os.environ.get("LOG_DIR", "/app/logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, "watchdog.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger("scheduler")

SH = pytz.timezone("Asia/Shanghai")


# ─── Job wrappers ─────────────────────────────────────────────
def _run(label, fn):
    logger.info("═══ START  %s ═══", label)
    try:
        fn()
    except Exception as exc:
        logger.error("═══ FAILED %s — %s ═══", label, exc)
    else:
        logger.info("═══ DONE   %s ═══", label)


def job_news():             _run("新闻爬取",              fetch_all_news)
def job_realtime():         _run("实时价格",              fetch_all_realtime)
def job_daily_cn_hk():      _run("今日K线(CN/HK)",       fetch_today_indices)
def job_daily_crypto_fx():  _run("今日K线(Crypto/FX)",   fetch_today_crypto_fx)
def job_daily_commodities():_run("今日K线(贵金属)",      fetch_today_commodities)
def job_daily_us():         _run("今日K线(US)",          fetch_today_indices)
def job_futures():          _run("期货移仓检测",         check_and_save_rollover)


def job_catchup():
    """Historical data fill-up."""
    _run("补齐(指数)",     fetch_all_indices)
    _run("补齐(加密/FX)", fetch_all_crypto_fx)
    _run("补齐(贵金属)",  fetch_all_commodities)


# ─── Main ─────────────────────────────────────────────────────
def main():
    logger.info("Initializing DB tables ...")
    init_all_tables()

    executors = {"default": ThreadPoolExecutor(3)}
    scheduler = BlockingScheduler(timezone=SH, executors=executors)

    # Every hour :00 — news
    scheduler.add_job(job_news,
                      CronTrigger(minute=0, timezone=SH),
                      name="hourly_news", max_instances=1)

    # Every hour :05 — realtime prices
    scheduler.add_job(job_realtime,
                      CronTrigger(minute=5, timezone=SH),
                      name="hourly_realtime", max_instances=1)

    # Daily 03:00 — historical catch-up
    scheduler.add_job(job_catchup,
                      CronTrigger(hour=3, minute=0, timezone=SH),
                      name="daily_catchup", max_instances=1)

    # Daily 06:00 — US previous-day close
    scheduler.add_job(job_daily_us,
                      CronTrigger(hour=6, minute=0, timezone=SH),
                      name="daily_us", max_instances=1)

    # Daily 14:30 — futures rollover check (before CN close)
    scheduler.add_job(job_futures,
                      CronTrigger(hour=14, minute=30, timezone=SH),
                      name="daily_futures", max_instances=1)

    # Daily 15:30 — A-share / HK close
    scheduler.add_job(job_daily_cn_hk,
                      CronTrigger(hour=15, minute=30, timezone=SH),
                      name="daily_cn_hk", max_instances=1)

    # Daily 16:40 — crypto + FX
    scheduler.add_job(job_daily_crypto_fx,
                      CronTrigger(hour=16, minute=40, timezone=SH),
                      name="daily_crypto_fx", max_instances=1)

    # Daily 16:50 — commodities
    scheduler.add_job(job_daily_commodities,
                      CronTrigger(hour=16, minute=50, timezone=SH),
                      name="daily_commodities", max_instances=1)

    # Startup: immediate one-shot catch-up
    scheduler.add_job(job_catchup,
                      DateTrigger(run_date=datetime.now(SH)),
                      name="startup_catchup")

    logger.info("Scheduler starting ...")
    scheduler.start()


if __name__ == "__main__":
    main()
