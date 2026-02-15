"""
Crypto (BTC/ETH/BNB) + USD/CNH daily K-line.
  Crypto: ccxt -> Binance 1d candles
  FX:     yfinance  USDCNH=X  (fallback CNY=X)
Idempotent: ON DUPLICATE KEY UPDATE
"""
import logging
import time
from datetime import datetime, date, timedelta

import ccxt
import pandas as pd
import yfinance as yf

from config.settings import CRYPTO_FX_CONFIG
from db.connection   import execute_query, executemany

logger = logging.getLogger(__name__)

_UPSERT = """
INSERT INTO crypto_fx_daily_kline
    (symbol, symbol_name, trade_date,
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
        "SELECT MAX(trade_date) FROM crypto_fx_daily_kline WHERE symbol=%s",
        (symbol,), fetch=True
    )
    v = rows[0][0] if rows else None
    if v is None:
        return None
    return v if isinstance(v, date) else datetime.strptime(str(v), "%Y-%m-%d").date()


# ─── Crypto via ccxt ──────────────────────────────────────────
def _fetch_crypto(cfg):
    symbol = cfg["symbol"]
    pair   = cfg["ccxt_pair"]
    name   = cfg["name"]

    latest = _latest_date(symbol)
    start  = (latest + timedelta(days=1)) if latest \
             else datetime.strptime(cfg["start_date"], "%Y-%m-%d").date()

    if start > datetime.now().date():
        logger.info("%s: up to date", symbol)
        return 0

    logger.info("crypto %s from %s", symbol, start)
    exchange = ccxt.binance({"enableRateLimit": True})
    since_ms = int(datetime(start.year, start.month, start.day).timestamp() * 1000)
    rows = []

    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(pair, "1d", since=since_ms, limit=500)
        except Exception as e:
            logger.error("binance %s: %s", pair, e)
            break

        if not ohlcv:
            break

        for ts, o, h, l, c, v in ohlcv:
            d = datetime.utcfromtimestamp(ts / 1000).date()
            if d > datetime.now().date():
                continue
            if latest and d <= latest:
                continue
            rows.append((symbol, name, d,
                         round(o, 8), round(h, 8), round(l, 8), round(c, 8), round(v, 8)))

        last_d = datetime.utcfromtimestamp(ohlcv[-1][0] / 1000).date()
        if last_d >= datetime.now().date():
            break
        since_ms = ohlcv[-1][0] + 86_400_000   # +1 day in ms
        time.sleep(0.6)                         # rate-limit

    if rows:
        executemany(_UPSERT, rows)
    logger.info("%s: %d rows", symbol, len(rows))
    return len(rows)


# ─── USD/CNH via yfinance ─────────────────────────────────────
def _flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def _fetch_usd_cnh(cfg):
    symbol = cfg["symbol"]   # "USD_CNH"
    name   = cfg["name"]

    latest = _latest_date(symbol)
    start  = (latest + timedelta(days=1)).isoformat() if latest else cfg["start_date"]

    if start > datetime.now().isoformat()[:10]:
        logger.info("USD_CNH: up to date")
        return 0

    logger.info("USD_CNH from %s", start)
    end = (datetime.now() + timedelta(days=1)).isoformat()

    df = pd.DataFrame()
    for ticker in ("USDCNH=X", "CNY=X"):
        try:
            df = yf.download(ticker, start=start, end=end,
                             progress=False, auto_adjust=True)
            df = _flatten(df)
            if not df.empty:
                logger.info("USD_CNH using ticker: %s", ticker)
                break
        except Exception:
            continue

    if df.empty:
        logger.warning("USD_CNH: no data from yfinance")
        return 0

    df = df.reset_index()
    rows = []
    for _, r in df.iterrows():
        td = r["Date"]
        td = td.date() if hasattr(td, "date") else datetime.strptime(str(td)[:10], "%Y-%m-%d").date()
        rows.append((symbol, name, td,
                     round(float(r["Open"]),  6),
                     round(float(r["High"]),  6),
                     round(float(r["Low"]),   6),
                     round(float(r["Close"]), 6),
                     0))  # FX has no volume

    if rows:
        executemany(_UPSERT, rows)
    logger.info("USD_CNH: %d rows", len(rows))
    return len(rows)


# ─── Public API ───────────────────────────────────────────────
def fetch_all_crypto_fx():
    """Fetch all crypto + FX symbols."""
    total = 0
    for cfg in CRYPTO_FX_CONFIG:
        if   cfg["type"] == "crypto":
            total += _fetch_crypto(cfg)
        elif cfg["type"] == "fx":
            total += _fetch_usd_cnh(cfg)
    logger.info("crypto_fx total: %d", total)
    return total


def fetch_today_crypto_fx():
    """Fetch latest (auto-skips already-stored dates)."""
    return fetch_all_crypto_fx()
