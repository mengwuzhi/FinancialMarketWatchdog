"""
IC / IM Futures Rollover Signal Detection.
Data source: akshare (optional dep) -> sina futures (fallback)
Rollover logic (滚期指):
    volume_ratio = next_volume / main_volume
    oi_ratio     = next_oi     / main_oi
    Strong:      v_ratio > 1.5 AND o_ratio > 1.5
    Medium:      v_ratio > 1.0 AND o_ratio > 1.0
    Volume-only: v_ratio > 2.0
    Near-expiry (<=10 days to 3rd Friday): any ratio > 0.8 triggers
"""
import calendar
import logging
import re
import time
from datetime import datetime, date

import requests
from bs4 import BeautifulSoup

from data_crawler.config.settings import DEFAULT_HEADERS
from data_crawler.db.connection   import executemany

logger = logging.getLogger(__name__)

_UPSERT = """
INSERT INTO futures_rollover
    (contract_type, check_date,
     main_contract, main_volume, main_open_interest,
     next_contract, next_volume, next_open_interest,
     volume_ratio, oi_ratio, rollover_signal, signal_reason)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    main_contract       = VALUES(main_contract),
    main_volume         = VALUES(main_volume),
    main_open_interest  = VALUES(main_open_interest),
    next_contract       = VALUES(next_contract),
    next_volume         = VALUES(next_volume),
    next_open_interest  = VALUES(next_open_interest),
    volume_ratio        = VALUES(volume_ratio),
    oi_ratio            = VALUES(oi_ratio),
    rollover_signal     = VALUES(rollover_signal),
    signal_reason       = VALUES(signal_reason)
"""


def _third_friday(year, month):
    """Return day-number of the 3rd Friday of the given month."""
    weeks   = calendar.monthcalendar(year, month)
    fridays = [w[4] for w in weeks if w[4] != 0]
    return fridays[2]


def _contract_codes(ctype, today):
    """
    Return (main_contract_code, next_contract_code).
    Expiry = 3rd Friday of delivery month.
    After expiry -> main moves to next month.
    Contract code format: {IC|IM}{YY}{MM}  e.g. IC2602
    """
    y, m = today.year, today.month
    exp  = _third_friday(y, m)

    if today.day <= exp:
        main_m, main_y = m, y
    else:
        if m == 12:
            main_m, main_y = 1, y + 1
        else:
            main_m, main_y = m + 1, y

    # next = one month after main
    if main_m == 12:
        next_m, next_y = 1, main_y + 1
    else:
        next_m, next_y = main_m + 1, main_y

    main_code = f"{ctype}{str(main_y)[2:]}{str(main_m).zfill(2)}"
    next_code = f"{ctype}{str(next_y)[2:]}{str(next_m).zfill(2)}"
    return main_code, next_code


# ─── Data sources ─────────────────────────────────────────────
def _fetch_via_akshare(code):
    """Try akshare (optional dependency). Returns dict or None."""
    try:
        import akshare as ak  # noqa – optional
        df = ak.futures_quote()
        if df is None or df.empty:
            return None
        code_col = None
        for c in ("合约代码", "交易代码", "symbol", "code"):
            if c in df.columns:
                code_col = c
                break
        if code_col is None:
            return None
        row = df[df[code_col] == code]
        if row.empty:
            return None
        row = row.iloc[0]
        vol, oi = 0, 0
        for c in ("成交量", "成交手数", "volume"):
            if c in row.index:
                vol = int(row[c])
                break
        for c in ("持仓量", "持仓手数", "open_interest"):
            if c in row.index:
                oi = int(row[c])
                break
        return {"volume": vol, "open_interest": oi}
    except ImportError:
        return None
    except Exception as e:
        logger.debug("akshare %s: %s", code, e)
        return None


def _fetch_via_sina(code):
    """Fallback: scrape sina futures detail page."""
    url = f"https://finance.sina.com.cn/futures/detail/{code}.html"
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        resp.encoding = "utf-8"
        text = BeautifulSoup(resp.text, "lxml").get_text()
        vol_m = re.search(r"成交量[：:]\s*([\d,]+)", text)
        oi_m  = re.search(r"持仓量[：:]\s*([\d,]+)", text)
        vol = int(vol_m.group(1).replace(",", "")) if vol_m else 0
        oi  = int(oi_m.group(1).replace(",", ""))  if oi_m  else 0
        return {"volume": vol, "open_interest": oi}
    except Exception as e:
        logger.debug("sina futures %s: %s", code, e)
        return None


def _get_quote(code):
    """Get volume + OI: akshare -> sina -> zeros."""
    data = _fetch_via_akshare(code)
    if data is None:
        data = _fetch_via_sina(code)
    if data is None:
        logger.warning("no data for %s, using zeros", code)
        data = {"volume": 0, "open_interest": 0}
    return data


# ─── Rollover signal logic ────────────────────────────────────
def _check_signal(main_vol, main_oi, next_vol, next_oi, today):
    """Determine rollover signal. Returns dict."""
    v_ratio = round(next_vol / main_vol, 4) if main_vol > 0 else 0.0
    o_ratio = round(next_oi  / main_oi,  4) if main_oi  > 0 else 0.0

    signal  = False
    reasons = []

    if v_ratio > 1.5 and o_ratio > 1.5:
        signal = True
        reasons.append(f"强信号: 量比{v_ratio:.2f}>1.5 仓比{o_ratio:.2f}>1.5")
    elif v_ratio > 1.0 and o_ratio > 1.0:
        signal = True
        reasons.append(f"中信号: 量比{v_ratio:.2f}>1.0 仓比{o_ratio:.2f}>1.0")
    elif v_ratio > 2.0:
        signal = True
        reasons.append(f"量信号: 量比{v_ratio:.2f}>2.0")

    # Near-expiry boost
    exp = _third_friday(today.year, today.month)
    days_left = exp - today.day
    if 0 < days_left <= 10:
        reasons.append(f"临近到期({days_left}天,到期日={today.month}月{exp}日)")
        if not signal and (v_ratio > 0.8 or o_ratio > 0.8):
            signal = True
            reasons.append("临近到期加权触发")

    if not reasons:
        reasons.append(f"未触发: 量比{v_ratio:.2f} 仓比{o_ratio:.2f}")

    return {
        "signal":  signal,
        "v_ratio": v_ratio,
        "o_ratio": o_ratio,
        "reason":  "; ".join(reasons),
    }


# ─── Public API ───────────────────────────────────────────────
def check_and_save_rollover():
    """Check IC & IM rollover signals and persist. Returns processed count."""
    today = datetime.now().date()
    if today.weekday() >= 5:   # Weekend
        logger.info("futures rollover: weekend, skip")
        return 0

    rows = []
    for ctype in ("IC", "IM"):
        main_code, next_code = _contract_codes(ctype, today)
        logger.info("rollover %s: main=%s next=%s", ctype, main_code, next_code)

        main_q = _get_quote(main_code)
        time.sleep(0.8)
        next_q = _get_quote(next_code)

        sig = _check_signal(
            main_q["volume"],          main_q["open_interest"],
            next_q["volume"],          next_q["open_interest"],
            today
        )
        rows.append((
            ctype, today,
            main_code, main_q["volume"],          main_q["open_interest"],
            next_code, next_q["volume"],          next_q["open_interest"],
            sig["v_ratio"], sig["o_ratio"],
            1 if sig["signal"] else 0,
            sig["reason"],
        ))
        logger.info("  %s: signal=%s  %s", ctype, sig["signal"], sig["reason"])

    if rows:
        executemany(_UPSERT, rows)
    return len(rows)
