"""
Financial news crawler — multi-source aggregation.
Sources: Sina Finance / JRJ / NetEase / Reuters RSS
Dedup:   MD5(url) -> url_hash, INSERT IGNORE
"""
import hashlib
import logging
import time
from datetime import datetime
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

from config.settings import DEFAULT_HEADERS
from db.connection   import executemany

logger = logging.getLogger(__name__)

_INSERT = """
INSERT IGNORE INTO news
    (title, summary, source, url, publish_time, category, url_hash)
VALUES
    (%s, %s, %s, %s, %s, %s, %s)
"""

_FIN_KW = {
    "market", "stock", "economy", "finance", "bank", "trade",
    "oil", "gold", "crypto", "bitcoin", "inflation", "gdp", "fed",
    "经济", "金融", "股市", "贸易", "美元", "人民币", "指数",
}


def _md5(s):
    return hashlib.md5(s.strip().encode("utf-8")).hexdigest()


# ─── Source scrapers ──────────────────────────────────────────
def _sina():
    """新浪财经"""
    items = []
    try:
        resp = requests.get("https://finance.sina.com.cn/",
                            headers=DEFAULT_HEADERS, timeout=12)
        resp.encoding = "utf-8"
        for a in BeautifulSoup(resp.text, "lxml").find_all("a", href=True):
            href  = a["href"]
            title = a.get_text(strip=True)
            if not (10 <= len(title) <= 200):
                continue
            if "finance.sina" not in href and "/a/" not in href:
                continue
            if not href.startswith("http"):
                href = "https://finance.sina.com.cn" + href
            items.append(("新浪财经", title, href, "A股"))
    except Exception as e:
        logger.warning("sina: %s", e)
    return items


def _jrj():
    """证券之家"""
    items = []
    try:
        resp = requests.get("https://www.jrj.com/",
                            headers=DEFAULT_HEADERS, timeout=12)
        resp.encoding = "utf-8"
        for a in BeautifulSoup(resp.text, "lxml").find_all("a", href=True):
            href  = a["href"]
            title = a.get_text(strip=True)
            if not (8 <= len(title) <= 200):
                continue
            if not href.startswith("http"):
                href = urljoin("https://www.jrj.com/", href)
            if any(kw in href for kw in ("/newsinfo/", "/info/", "/news/")):
                items.append(("证券之家", title, href, "市场"))
    except Exception as e:
        logger.warning("jrj: %s", e)
    return items


def _netease():
    """网易财经"""
    items = []
    try:
        resp = requests.get("https://money.163.com/",
                            headers=DEFAULT_HEADERS, timeout=12)
        resp.encoding = "utf-8"
        for a in BeautifulSoup(resp.text, "lxml").find_all("a", href=True):
            href  = a["href"]
            title = a.get_text(strip=True)
            if not (8 <= len(title) <= 200):
                continue
            if "money.163.com" not in href:
                continue
            items.append(("网易财经", title, href, "财经"))
    except Exception as e:
        logger.warning("netease: %s", e)
    return items


_RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://feeds.reuters.com/reuters/topNews",
]


def _reuters():
    """Reuters RSS — filtered by financial keywords"""
    items = []
    for url in _RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:25]:
                title   = getattr(entry, "title",   "")
                summary = getattr(entry, "summary", "")
                link    = getattr(entry, "link",    "")
                if not title or not link:
                    continue
                if not any(k in (title + " " + summary).lower() for k in _FIN_KW):
                    continue
                pub = None
                pub_s = getattr(entry, "published", "")
                if pub_s:
                    try:
                        from email.utils import parsedate_to_datetime
                        pub = parsedate_to_datetime(pub_s)
                    except Exception:
                        pass
                items.append(("Reuters", title[:200], link, "international", summary[:500], pub))
        except Exception as e:
            logger.warning("rss %s: %s", url, e)
    return items


# ─── Public API ───────────────────────────────────────────────
def fetch_all_news():
    """Pull from all sources, dedup, INSERT IGNORE. Returns new-row count."""
    logger.info("news fetch start")

    # Chinese sources return (source, title, url, category)
    raw_cn = []
    for label, fn in [("新浪", _sina), ("JRJ", _jrj), ("网易", _netease)]:
        try:
            batch = fn()
            logger.info("  %s: %d items", label, len(batch))
            raw_cn.extend(batch)
            time.sleep(1.5)
        except Exception as e:
            logger.error("  %s: %s", label, e)

    # Reuters returns (source, title, url, category, summary, pub_time)
    raw_en = []
    try:
        raw_en = _reuters()
        logger.info("  Reuters: %d items", len(raw_en))
    except Exception as e:
        logger.error("  Reuters: %s", e)

    # Dedup by url hash
    seen = set()
    rows = []
    for src, title, url, cat in raw_cn:
        h = _md5(url)
        if h in seen:
            continue
        seen.add(h)
        rows.append((title, "", src, url, None, cat, h))

    for src, title, url, cat, summary, pub in raw_en:
        h = _md5(url)
        if h in seen:
            continue
        seen.add(h)
        rows.append((title, summary, src, url, pub, cat, h))

    logger.info("news after dedup: %d", len(rows))
    if not rows:
        return 0
    try:
        cnt = executemany(_INSERT, rows)
        logger.info("news saved: %d new", cnt)
        return cnt
    except Exception as e:
        logger.error("news save: %s", e)
        return 0
