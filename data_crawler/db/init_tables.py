"""Database table initialization"""
import logging

from data_crawler.db.connection import execute_query

logger = logging.getLogger(__name__)

# ─── 1. Financial News ────────────────────────────────────────
CREATE_NEWS = """
CREATE TABLE IF NOT EXISTS news (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    title         VARCHAR(500)  NOT NULL,
    summary       TEXT,
    source        VARCHAR(100),
    url           VARCHAR(1000),
    publish_time  DATETIME,
    category      VARCHAR(50)   DEFAULT 'general',
    url_hash      VARCHAR(64)   NOT NULL  COMMENT 'MD5(url) dedup key',
    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_url_hash (url_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财经新闻';
"""

# ─── 2. Stock Index Daily K-Line ──────────────────────────────
CREATE_INDEX_KLINE = """
CREATE TABLE IF NOT EXISTS index_daily_kline (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    index_code    VARCHAR(30)   NOT NULL,
    index_name    VARCHAR(100),
    trade_date    DATE          NOT NULL,
    open_price    DECIMAL(14,4),
    high_price    DECIMAL(14,4),
    low_price     DECIMAL(14,4),
    close_price   DECIMAL(14,4),
    change_pct    DECIMAL(8,4)  COMMENT '涨跌幅%',
    volume        BIGINT,
    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_code_date (index_code, trade_date),
    INDEX idx_code (index_code),
    INDEX idx_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票指数日K线';
"""

# ─── 3. Crypto & FX Daily K-Line ──────────────────────────────
CREATE_CRYPTO_FX_KLINE = """
CREATE TABLE IF NOT EXISTS crypto_fx_daily_kline (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    symbol        VARCHAR(30)   NOT NULL,
    symbol_name   VARCHAR(100),
    trade_date    DATE          NOT NULL,
    open_price    DECIMAL(20,8),
    high_price    DECIMAL(20,8),
    low_price     DECIMAL(20,8),
    close_price   DECIMAL(20,8),
    volume        DECIMAL(28,8),
    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_symbol_date (symbol, trade_date),
    INDEX idx_symbol (symbol),
    INDEX idx_date   (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='加密货币和汇率日K线';
"""

# ─── 4. Commodity Daily K-Line ────────────────────────────────
CREATE_COMMODITY_KLINE = """
CREATE TABLE IF NOT EXISTS commodity_daily_kline (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    commodity       VARCHAR(30)   NOT NULL,
    commodity_name  VARCHAR(100),
    trade_date      DATE          NOT NULL,
    open_price      DECIMAL(16,6),
    high_price      DECIMAL(16,6),
    low_price       DECIMAL(16,6),
    close_price     DECIMAL(16,6),
    volume          BIGINT,
    created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_commodity_date (commodity, trade_date),
    INDEX idx_commodity (commodity),
    INDEX idx_date      (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='贵金属日K线';
"""

# ─── 5. Futures Rollover Signal ───────────────────────────────
CREATE_FUTURES_ROLLOVER = """
CREATE TABLE IF NOT EXISTS futures_rollover (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    contract_type       VARCHAR(10)   NOT NULL  COMMENT 'IC or IM',
    check_date          DATE          NOT NULL,
    main_contract       VARCHAR(20)             COMMENT '主力合约',
    main_volume         BIGINT                  COMMENT '主力成交量',
    main_open_interest  BIGINT                  COMMENT '主力持仓量',
    next_contract       VARCHAR(20)             COMMENT '远月合约',
    next_volume         BIGINT                  COMMENT '远月成交量',
    next_open_interest  BIGINT                  COMMENT '远月持仓量',
    volume_ratio        DECIMAL(8,4)            COMMENT '量比=远月/主力',
    oi_ratio            DECIMAL(8,4)            COMMENT '仓比=远月/主力',
    rollover_signal     TINYINT(1)   DEFAULT 0  COMMENT '1=建议移仓',
    signal_reason       TEXT                    COMMENT '信号说明',
    created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_type_date (contract_type, check_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='IC/IM期货滚动移仓信号';
"""

# ─── 6. Realtime Prices (hourly) ──────────────────────────────
CREATE_REALTIME = """
CREATE TABLE IF NOT EXISTS realtime_prices (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    symbol        VARCHAR(30)   NOT NULL,
    symbol_name   VARCHAR(100),
    price         DECIMAL(20,8),
    change_24h    DECIMAL(8,4)           COMMENT '24h变动%',
    record_time   DATETIME     NOT NULL,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol (symbol),
    INDEX idx_time   (record_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='实时价格(每小时)';
"""

_TABLES = [
    ("news",                  CREATE_NEWS),
    ("index_daily_kline",     CREATE_INDEX_KLINE),
    ("crypto_fx_daily_kline", CREATE_CRYPTO_FX_KLINE),
    ("commodity_daily_kline", CREATE_COMMODITY_KLINE),
    ("futures_rollover",      CREATE_FUTURES_ROLLOVER),
    ("realtime_prices",       CREATE_REALTIME),
]


def init_all_tables():
    """Ensure all tables exist in watchdog_db."""
    for name, sql in _TABLES:
        try:
            execute_query(sql)
            logger.info("table '%s' OK", name)
        except Exception as exc:
            logger.error("create table '%s': %s", name, exc)
