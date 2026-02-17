"""Stock history data table definitions"""

# A股历史K线表
CREATE_STOCK_CN_HISTORY = """
CREATE TABLE IF NOT EXISTS stock_cn_history (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    symbol          VARCHAR(10)   NOT NULL  COMMENT '股票代码（如600000）',
    name            VARCHAR(100)            COMMENT '股票名称',
    trade_date      DATE          NOT NULL  COMMENT '交易日期',
    open_price      DECIMAL(10,2)           COMMENT '开盘价',
    high_price      DECIMAL(10,2)           COMMENT '最高价',
    low_price       DECIMAL(10,2)           COMMENT '最低价',
    close_price     DECIMAL(10,2)           COMMENT '收盘价',
    volume          BIGINT                  COMMENT '成交量（手）',
    amount          DECIMAL(20,2)           COMMENT '成交额（元）',
    change_pct      DECIMAL(8,4)            COMMENT '涨跌幅（%）',
    change_amount   DECIMAL(10,2)           COMMENT '涨跌额（元）',
    turnover_rate   DECIMAL(8,4)            COMMENT '换手率（%）',
    created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_symbol_date (symbol, trade_date),
    INDEX idx_symbol (symbol),
    INDEX idx_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='A股历史K线数据';
"""

# 美股历史K线表
CREATE_STOCK_US_HISTORY = """
CREATE TABLE IF NOT EXISTS stock_us_history (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    symbol          VARCHAR(20)   NOT NULL  COMMENT '股票代码（如AAPL）',
    name            VARCHAR(100)            COMMENT '股票名称',
    trade_date      DATE          NOT NULL  COMMENT '交易日期',
    open_price      DECIMAL(12,4)           COMMENT '开盘价',
    high_price      DECIMAL(12,4)           COMMENT '最高价',
    low_price       DECIMAL(12,4)           COMMENT '最低价',
    close_price     DECIMAL(12,4)           COMMENT '收盘价',
    volume          BIGINT                  COMMENT '成交量（股）',
    change_pct      DECIMAL(8,4)            COMMENT '涨跌幅（%）',
    change_amount   DECIMAL(12,4)           COMMENT '涨跌额',
    created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_symbol_date (symbol, trade_date),
    INDEX idx_symbol (symbol),
    INDEX idx_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='美股历史K线数据';
"""

STOCK_HISTORY_TABLES = [
    ("stock_cn_history", CREATE_STOCK_CN_HISTORY),
    ("stock_us_history", CREATE_STOCK_US_HISTORY),
]


def init_stock_history_tables():
    """Initialize stock history tables."""
    import logging
    from data_crawler.db.connection import execute_query

    logger = logging.getLogger(__name__)

    for name, sql in STOCK_HISTORY_TABLES:
        try:
            execute_query(sql)
            logger.info(f"Stock history table '{name}' OK")
        except Exception as exc:
            logger.error(f"Create stock history table '{name}': {exc}")
