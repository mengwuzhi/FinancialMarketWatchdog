"""FinancialMarketWatchdog — Central Config"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Database ─────────────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST",     "47.95.221.184")
DB_PORT     = int(os.getenv("DB_PORT", "18453"))
DB_USER     = os.getenv("DB_USER",     "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "RLCs9.Y3.mSG3@")
DB_NAME     = os.getenv("DB_NAME",     "watchdog_db")

# ─── Timezone / Logging ───────────────────────────────────────
TIMEZONE  = os.getenv("TIMEZONE", "Asia/Shanghai")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ─── Stock Index Config (yfinance tickers) ────────────────────
INDEX_CONFIG = [
    # A-Share
    {"code": "SHCI",     "name": "上证指数",     "ticker": "000001.SS", "start_date": "2014-01-01"},
    {"code": "SZCI",     "name": "深成综指",     "ticker": "399001.SZ", "start_date": "2014-01-01"},
    {"code": "CHINEXT",  "name": "创业板指数",   "ticker": "399102.SZ", "start_date": "2014-01-01"},
    {"code": "SH50",     "name": "上证50",       "ticker": "000016.SS", "start_date": "2014-01-01"},
    {"code": "CSI300",   "name": "沪深300",      "ticker": "000300.SS", "start_date": "2014-01-01"},
    {"code": "CSI500",   "name": "中证500",      "ticker": "000905.SS", "start_date": "2014-01-01"},
    # HK
    {"code": "HSI",      "name": "恒生指数",     "ticker": "^HSI",      "start_date": "2014-01-01"},
    {"code": "HSTECH",   "name": "恒生科技指数", "ticker": "^HSTECH",   "start_date": "2014-01-01"},
    # US
    {"code": "NASDAQ",   "name": "纳斯达克指数", "ticker": "^IXIC",     "start_date": "2014-01-01"},
    {"code": "DOWJONES", "name": "道琼斯指数",   "ticker": "^DJI",      "start_date": "2014-01-01"},
    {"code": "SP500",    "name": "标普500指数",  "ticker": "^GSPC",     "start_date": "2014-01-01"},
]

# ─── Crypto & FX Config ───────────────────────────────────────
CRYPTO_FX_CONFIG = [
    {"symbol": "USD_CNH", "name": "美元兑离岸人民币", "type": "fx",     "start_date": "2020-01-01"},
    {"symbol": "BTC",     "name": "比特币",          "type": "crypto", "ccxt_pair": "BTC/USDT",  "start_date": "2020-01-01"},
    {"symbol": "ETH",     "name": "以太坊",          "type": "crypto", "ccxt_pair": "ETH/USDT",  "start_date": "2020-01-01"},
    {"symbol": "BNB",     "name": "币安币",          "type": "crypto", "ccxt_pair": "BNB/USDT",  "start_date": "2020-01-01"},
]

# ─── Commodity Config ─────────────────────────────────────────
COMMODITY_CONFIG = [
    {"symbol": "GOLD",   "name": "黄金价格", "ticker": "GC=F", "start_date": "2020-01-01"},
    {"symbol": "SILVER", "name": "白银价格", "ticker": "SI=F", "start_date": "2020-01-01"},
]

# ─── Realtime Price Config ────────────────────────────────────
REALTIME_CONFIG = [
    {"symbol": "USD_CNH", "name": "美元兑离岸人民币"},
    {"symbol": "BTC",     "name": "比特币"},
    {"symbol": "ETH",     "name": "以太坊"},
    {"symbol": "GOLD",    "name": "黄金价格"},
    {"symbol": "SILVER",  "name": "白银价格"},
]

# ─── HTTP Headers ─────────────────────────────────────────────
DEFAULT_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
}

# ─── CoinGecko ID Map ─────────────────────────────────────────
COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binance-coin",
}
