"""
Hourly realtime price collection.
  Crypto:  CoinGecko simple/price API (free, no key needed)
  FX:      exchangerate-api.com (free)
  Metals:  goldprice.org scrape -> yfinance fallback
Each call appends a new row (no dedup — full hourly time series).
"""
import logging
import time
from datetime import datetime

import requests

from config.settings import DEFAULT_HEADERS, REALTIME_CONFIG, COINGECKO_IDS
from db.connection   import executemany

logger = logging.getLogger(__name__)

_INSERT = """
INSERT INTO realtime_prices
    (symbol, symbol_name, price, change_24h, record_time)
VALUES (%s,%s,%s,%s,%s)
"""


# ─── Crypto (CoinGecko) ──────────────────────────────────────
def _crypto_prices():
    """Return {symbol: {"price": float, "change_24h": float}}"""
    out = {}
    ids = list(COINGECKO_IDS.values())
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": ",".join(ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        id2sym = {v: k for k, v in COINGECKO_IDS.items()}
        for cg_id, info in data.items():
            sym = id2sym.get(cg_id)
            if sym:
                out[sym] = {
                    "price":      info.get("usd", 0),
                    "change_24h": round(info.get("usd_24h_change", 0), 4),
                }
    except Exception as e:
        logger.warning("coingecko: %s", e)
    return out


# ─── USD / CNH ────────────────────────────────────────────────
def _usd_cnh():
    """Fetch USD->CNY rate (public API, close to CNH)."""
    try:
        resp = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD",
            timeout=10,
        )
        resp.raise_for_status()
        rate = resp.json().get("rates", {}).get("CNY")
        if rate:
            return {"price": round(rate, 4), "change_24h": 0.0}
    except Exception as e:
        logger.warning("exchangerate-api: %s", e)
    return None


# ─── Gold / Silver ────────────────────────────────────────────
def _gold_silver():
    """Scrape goldprice.org; yfinance fallback for missing symbols."""
    import re
    out = {}
    try:
        resp = requests.get("https://www.goldprice.org/gold-price.html",
                            headers=DEFAULT_HEADERS, timeout=10)
        resp.raise_for_status()
        from bs4 import BeautifulSoup
        text = BeautifulSoup(resp.text, "lxml").get_text()
        g = re.search(r"[Gg]old.*?(\d{1,2},?\d{3}(?:\.\d+)?)", text)
        if g:
            out["GOLD"] = {"price": float(g.group(1).replace(",", "")), "change_24h": 0.0}
        s = re.search(r"[Ss]ilver.*?(\d{2,3}(?:\.\d+)?)", text)
        if s:
            out["SILVER"] = {"price": float(s.group(1)), "change_24h": 0.0}
    except Exception as e:
        logger.debug("goldprice.org: %s", e)

    # yfinance fallback for any missing symbol
    if "GOLD" not in out or "SILVER" not in out:
        try:
            import yfinance as yf
            for sym, tick in [("GOLD", "GC=F"), ("SILVER", "SI=F")]:
                if sym in out:
                    continue
                hi = yf.Ticker(tick).history(period="1d")
                if not hi.empty:
                    out[sym] = {"price": round(float(hi["Close"].iloc[-1]), 6), "change_24h": 0.0}
        except Exception as e:
            logger.debug("yfinance metals fallback: %s", e)
    return out


# ─── Public API ───────────────────────────────────────────────
def fetch_all_realtime():
    """Collect all realtime prices and INSERT. Returns row count."""
    logger.info("realtime fetch start")
    now = datetime.now()

    crypto = _crypto_prices()
    time.sleep(1)
    fx     = _usd_cnh()
    time.sleep(1)
    metals = _gold_silver()

    # Merge all sources
    prices = {}
    prices.update(crypto)    # BTC, ETH, BNB
    prices.update(metals)    # GOLD, SILVER
    if fx:
        prices["USD_CNH"] = fx

    # Build insert rows according to REALTIME_CONFIG order
    name_map = {c["symbol"]: c["name"] for c in REALTIME_CONFIG}
    rows = []
    for sym, info in prices.items():
        rows.append((
            sym,
            name_map.get(sym, sym),
            info["price"],
            info.get("change_24h", 0.0),
            now,
        ))
        logger.info("  %s = %.6f (24h: %.2f%%)", sym, info["price"], info.get("change_24h", 0))

    if rows:
        try:
            executemany(_INSERT, rows)
            logger.info("realtime: %d rows inserted", len(rows))
        except Exception as e:
            logger.error("realtime save: %s", e)
    return len(rows)
