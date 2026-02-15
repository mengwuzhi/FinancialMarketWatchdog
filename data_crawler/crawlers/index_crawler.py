"""
Stock index daily K-line via yfinance.
Covers 11 indices (A-share / HK / US).
Idempotent: ON DUPLICATE KEY UPDATE — re-running never creates duplicates.
"""
import logging
from datetime import datetime, date, timedelta

import pandas as pd
import yfinance as yf

from data_crawler.config.settings import INDEX_CONFIG
from data_crawler.db.connection   import execute_query, executemany

logger = logging.getLogger(__name__)

_UPSERT = """
INSERT INTO index_daily_kline
    (index_code, index_name, trade_date,
     open_price, high_price, low_price, close_price, change_pct, volume)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    open_price  = VALUES(open_price),
    high_price  = VALUES(high_price),
    low_price   = VALUES(low_price),
    close_price = VALUES(close_price),
    change_pct  = VALUES(change_pct),
    volume      = VALUES(volume)
"""


def _latest_date(code):
    """Query latest trade_date for this index from DB."""
    rows = execute_query(
        "SELECT MAX(trade_date) FROM index_daily_kline WHERE index_code=%s",
        (code,), fetch=True
    )
    v = rows[0][0] if rows else None
    if v is None:
        return None
    return v if isinstance(v, date) else datetime.strptime(str(v), "%Y-%m-%d").date()


def _flatten(df):
    """Handle MultiIndex columns in newer yfinance versions."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def fetch_index_data(cfg, start_date=None):
    """Download single index, return inserted row count."""
    code, name, ticker = cfg["code"], cfg["name"], cfg["ticker"]

    if start_date is None:
        latest = _latest_date(code)
        start_date = (latest + timedelta(days=1)).isoformat() if latest else cfg["start_date"]

    if start_date > datetime.now().isoformat()[:10]:
        logger.info("%s: up to date", name)
        return 0

    end_date = (datetime.now() + timedelta(days=1)).isoformat()
    logger.info("fetch %s from %s", name, start_date)

    try:
        df = yf.download(ticker, start=start_date, end=end_date,
                         progress=False, auto_adjust=True)
        df = _flatten(df)
        if df.empty:
            logger.warning("%s: empty from yfinance", name)
            return 0

        df = df.reset_index()
        rows = []
        for _, r in df.iterrows():
            td = r["Date"]
            td = td.date() if hasattr(td, "date") else datetime.strptime(str(td)[:10], "%Y-%m-%d").date()
            o  = float(r["Open"])
            c  = float(r["Close"])
            pct = round((c - o) / o * 100, 4) if o != 0 else 0.0
            vol = int(r["Volume"]) if pd.notna(r.get("Volume", 0)) else 0
            rows.append((
                code, name, td,
                round(float(r["Open"]),  4),
                round(float(r["High"]),  4),
                round(float(r["Low"]),   4),
                round(c, 4), pct, vol
            ))

        if rows:
            executemany(_UPSERT, rows)
        logger.info("%s: %d rows upserted", name, len(rows))
        return len(rows)

    except Exception as e:
        logger.error("fetch %s: %s", name, e)
        return 0


def fetch_all_indices(start_date=None):
    """Fetch all 11 indices. Returns total rows upserted."""
    total = 0
    for cfg in INDEX_CONFIG:
        total += fetch_index_data(cfg, start_date)
    logger.info("indices total: %d", total)
    return total


def fetch_today_indices():
    """Fetch only today's data for all indices."""
    return fetch_all_indices(start_date=datetime.now().isoformat()[:10])
