"""Crawler endpoints: trigger data crawlers and query crawled data."""

import logging
from threading import Thread

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/crawler", tags=["crawler"])


class DateRangeQuery(BaseModel):
    start_date: str
    end_date: str
    limit: int = 100


@router.post("/news")
def trigger_news_crawler():
    """Trigger news crawler."""
    def _run():
        try:
            from data_crawler.crawlers.news_crawler import fetch_all_news
            fetch_all_news()
        except Exception as e:
            logger.error("News crawler failed: %s", e)

    Thread(target=_run, daemon=True).start()
    return {"status": "accepted", "message": "News crawler started"}


@router.post("/index")
def trigger_index_crawler():
    """Trigger stock index K-line crawler (today's data)."""
    def _run():
        try:
            from data_crawler.crawlers.index_crawler import fetch_today_indices
            fetch_today_indices()
        except Exception as e:
            logger.error("Index crawler failed: %s", e)

    Thread(target=_run, daemon=True).start()
    return {"status": "accepted", "message": "Index crawler started"}


@router.post("/crypto-fx")
def trigger_crypto_fx_crawler():
    """Trigger crypto & FX K-line crawler (today's data)."""
    def _run():
        try:
            from data_crawler.crawlers.crypto_fx_crawler import fetch_today_crypto_fx
            fetch_today_crypto_fx()
        except Exception as e:
            logger.error("Crypto/FX crawler failed: %s", e)

    Thread(target=_run, daemon=True).start()
    return {"status": "accepted", "message": "Crypto/FX crawler started"}


@router.post("/commodity")
def trigger_commodity_crawler():
    """Trigger commodity K-line crawler (today's data)."""
    def _run():
        try:
            from data_crawler.crawlers.commodity_crawler import fetch_today_commodities
            fetch_today_commodities()
        except Exception as e:
            logger.error("Commodity crawler failed: %s", e)

    Thread(target=_run, daemon=True).start()
    return {"status": "accepted", "message": "Commodity crawler started"}


@router.post("/futures")
def trigger_futures_crawler():
    """Trigger futures rollover signal crawler."""
    def _run():
        try:
            from data_crawler.crawlers.futures_crawler import check_rollover_all
            check_rollover_all()
        except Exception as e:
            logger.error("Futures crawler failed: %s", e)

    Thread(target=_run, daemon=True).start()
    return {"status": "accepted", "message": "Futures crawler started"}


@router.post("/realtime")
def trigger_realtime_crawler():
    """Trigger realtime price snapshot crawler."""
    def _run():
        try:
            from data_crawler.crawlers.realtime_crawler import fetch_realtime_all
            fetch_realtime_all()
        except Exception as e:
            logger.error("Realtime crawler failed: %s", e)

    Thread(target=_run, daemon=True).start()
    return {"status": "accepted", "message": "Realtime crawler started"}


@router.post("/index/catchup")
def trigger_index_catchup():
    """Trigger index historical data catchup."""
    def _run():
        try:
            from data_crawler.crawlers.index_crawler import fetch_all_indices
            fetch_all_indices()
        except Exception as e:
            logger.error("Index catchup failed: %s", e)

    Thread(target=_run, daemon=True).start()
    return {"status": "accepted", "message": "Index catchup started"}


@router.get("/news/query")
def query_news(limit: int = 20):
    """Query recent news from database."""
    try:
        from data_crawler.db.connection import execute_query

        sql = """
            SELECT id, title, source, url, publish_time, category, created_at
            FROM news
            ORDER BY publish_time DESC, created_at DESC
            LIMIT %s
        """
        rows = execute_query(sql, (limit,), fetch=True)

        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "title": row[1],
                "source": row[2],
                "url": row[3],
                "publish_time": row[4].isoformat() if row[4] else None,
                "category": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
            })

        return {"status": "ok", "count": len(results), "data": results}
    except Exception as e:
        logger.error("Query news failed: %s", e)
        return {"status": "error", "message": str(e)}
