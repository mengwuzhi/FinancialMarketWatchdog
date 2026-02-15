"""Market monitor endpoints: A-share and US stock reports."""

import logging
from threading import Thread

from fastapi import APIRouter, Depends

from app.dependencies import get_notifier
from monitors.a_share_monitor import AShareDailyReporter
from monitors.us_stock_monitor import USStockDailyReporter
from notifiers.dingtalk import DingTalkNotifier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/a-share")
def get_a_share_data():
    """Get A-share market data (JSON response)."""
    reporter = AShareDailyReporter()
    data = reporter.collect_data()
    return {"status": "ok", "data": data}


@router.post("/a-share/report")
def trigger_a_share_report(notifier: DingTalkNotifier = Depends(get_notifier)):
    """Trigger A-share daily report (async, sends DingTalk notification)."""
    def _run():
        try:
            reporter = AShareDailyReporter(notifier=notifier)
            reporter.generate_report()
        except Exception as e:
            logger.error("A-share report failed: %s", e)

    Thread(target=_run, daemon=True).start()
    return {"status": "accepted", "message": "A-share report task started"}


@router.get("/us-stock")
def get_us_stock_data():
    """Get US stock market data (JSON response)."""
    reporter = USStockDailyReporter()
    data = reporter.collect_data()
    return {"status": "ok", "data": data}


@router.post("/us-stock/report")
def trigger_us_stock_report(notifier: DingTalkNotifier = Depends(get_notifier)):
    """Trigger US stock daily report (async, sends DingTalk notification)."""
    def _run():
        try:
            reporter = USStockDailyReporter(notifier=notifier)
            reporter.generate_report()
        except Exception as e:
            logger.error("US stock report failed: %s", e)

    Thread(target=_run, daemon=True).start()
    return {"status": "accepted", "message": "US stock report task started"}
