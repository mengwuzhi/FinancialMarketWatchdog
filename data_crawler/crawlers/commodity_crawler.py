"""
Commodity (Gold / Silver) daily K-line via yfinance.
  GC=F  -> Gold futures
  SI=F  -> Silver futures
Idempotent: ON DUPLICATE KEY UPDATE
"""
import logging
from datetime import datetime, date, timedelta

import pandas as pd
import yfinance as yf

from data_crawler.config.settings import COMMODITY_CONFIG
from data_crawler.db.connection   import execute_query, executemany

logger = logging.getLogger(__name__)

_UPSERT = """
INSERT INTO commodity_daily_kline
    (commodity, commodity_name, trade_date,
     open_price, high_price, low_price, close_price, volume)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    open_price  = VALUES(open_price),
    high_price  = VALUES(high_price),
    low_price   = VALUES(low_price),
    close_price = VALUES(close_price),
    volume      = VALUES(volume)
"""


def _latest_date(symbol):
    rows = execute_query(
        "SELECT MAX(trade_date) FROM commodity_daily_kline WHERE commodity=%s",
        (symbol,), fetch=True
    )
    v = rows[0][0] if rows else None
    if v is None:
        return None
    return v if isinstance(v, date) else datetime.strptime(str(v), "%Y-%m-%d").date()


def _flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def fetch_commodity_data(cfg, start_date=None):
    """Download single commodity. Returns inserted row count."""
    symbol = cfg["symbol"]
    name   = cfg["name"]
    ticker = cfg["ticker"]

    if start_date is None:
        latest = _latest_date(symbol)
        start_date = (latest + timedelta(days=1)).isoformat() if latest else cfg["start_date"]

    if start_date > datetime.now().isoformat()[:10]:
        logger.info("%s: up to date", symbol)
        return 0

    end = (datetime.now() + timedelta(days=1)).isoformat()
    logger.info("commodity %s from %s", symbol, start_date)

    try:
        df = yf.download(ticker, start=start_date, end=end,
                         progress=False, auto_adjust=True)
        df = _flatten(df)
        if df.empty:
            logger.warning("%s: empty from yfinance", symbol)
            return 0

        df = df.reset_index()
        rows = []
        for _, r in df.iterrows():
            td  = r["Date"]
            td  = td.date() if hasattr(td, "date") else datetime.strptime(str(td)[:10], "%Y-%m-%d").date()
            vol = int(r["Volume"]) if pd.notna(r.get("Volume", 0)) else 0
            rows.append((symbol, name, td,
                         round(float(r["Open"]),  6),
                         round(float(r["High"]),  6),
                         round(float(r["Low"]),   6),
                         round(float(r["Close"]), 6),
                         vol))

        if rows:
            executemany(_UPSERT, rows)
        logger.info("%s: %d rows", symbol, len(rows))
        return len(rows)

    except Exception as e:
        logger.error("commodity %s: %s", symbol, e)
        return 0


def fetch_all_commodities(start_date=None):
    """Fetch all commodities."""
    total = 0
    for cfg in COMMODITY_CONFIG:
        total += fetch_commodity_data(cfg, start_date)
    logger.info("commodities total: %d", total)
    return total


def fetch_today_commodities():
    """Fetch only today's commodity data."""
    return fetch_all_commodities(start_date=datetime.now().isoformat()[:10])
