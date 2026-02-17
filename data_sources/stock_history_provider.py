"""Stock history data provider using Eastmoney and AKShare APIs."""

import logging
from datetime import datetime, date
from typing import List, Dict, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class StockHistoryProvider:
    """Stock history data provider."""

    @staticmethod
    def get_cn_stock_history(
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> Optional[List[Dict]]:
        """
        获取A股历史K线数据

        Args:
            symbol: 股票代码（如 600000, 000001）
            start_date: 开始日期 (YYYYMMDD 或 YYYY-MM-DD)
            end_date: 结束日期 (YYYYMMDD 或 YYYY-MM-DD)
            adjust: 复权类型 (qfq=前复权, hfq=后复权, 空=不复权)

        Returns:
            List of dict with keys: date, open, high, low, close, volume, amount, etc.
        """
        try:
            import akshare as ak

            # 格式化日期
            start = start_date.replace("-", "")
            end = end_date.replace("-", "")

            logger.info(f"Fetching CN stock {symbol} from {start} to {end}, adjust={adjust}")

            # 使用akshare获取A股历史数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start,
                end_date=end,
                adjust=adjust
            )

            if df is None or df.empty:
                logger.warning(f"No data found for CN stock {symbol}")
                return None

            # 转换列名为英文
            column_mapping = {
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "change_pct",
                "涨跌额": "change_amount",
                "换手率": "turnover_rate",
            }

            df = df.rename(columns=column_mapping)

            # 选择需要的列
            required_cols = ["date", "open", "high", "low", "close", "volume"]
            optional_cols = ["amount", "change_pct", "change_amount", "turnover_rate"]

            selected_cols = [c for c in required_cols + optional_cols if c in df.columns]
            df = df[selected_cols]

            # 转换为字典列表
            result = df.to_dict("records")

            logger.info(f"Successfully fetched {len(result)} records for CN stock {symbol}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch CN stock {symbol}: {e}")
            return None

    @staticmethod
    def get_us_stock_history(
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> Optional[List[Dict]]:
        """
        获取美股历史K线数据

        Args:
            symbol: 股票代码（如 AAPL, MSFT）
            start_date: 开始日期 (YYYYMMDD 或 YYYY-MM-DD)
            end_date: 结束日期 (YYYYMMDD 或 YYYY-MM-DD)

        Returns:
            List of dict with keys: date, open, high, low, close, volume, etc.
        """
        try:
            import akshare as ak

            # 格式化日期
            start = start_date.replace("-", "")
            end = end_date.replace("-", "")

            logger.info(f"Fetching US stock {symbol} from {start} to {end}")

            # 尝试多个市场代码
            markets = ["105", "106", "107"]  # 纳斯达克、纽交所、其他
            df = None

            for market in markets:
                try:
                    symbol_with_market = f"{market}.{symbol}"
                    df = ak.stock_us_hist(
                        symbol=symbol_with_market,
                        period="daily",
                        start_date=start,
                        end_date=end,
                        adjust="qfq"
                    )

                    if df is not None and not df.empty:
                        logger.info(f"Found US stock {symbol} in market {market}")
                        break
                except Exception as e:
                    logger.debug(f"Market {market} failed for {symbol}: {e}")
                    continue

            if df is None or df.empty:
                logger.warning(f"No data found for US stock {symbol} in any market")
                return None

            # 转换列名为英文
            column_mapping = {
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "涨跌幅": "change_pct",
                "涨跌额": "change_amount",
            }

            df = df.rename(columns=column_mapping)

            # 选择需要的列
            required_cols = ["date", "open", "high", "low", "close", "volume"]
            optional_cols = ["change_pct", "change_amount"]

            selected_cols = [c for c in required_cols + optional_cols if c in df.columns]
            df = df[selected_cols]

            # 转换为字典列表
            result = df.to_dict("records")

            logger.info(f"Successfully fetched {len(result)} records for US stock {symbol}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch US stock {symbol}: {e}")
            return None

    @staticmethod
    def save_cn_stock_to_db(symbol: str, name: str, data: List[Dict]) -> int:
        """
        保存A股历史数据到数据库

        Args:
            symbol: 股票代码
            name: 股票名称
            data: 历史数据列表

        Returns:
            插入/更新的记录数
        """
        if not data:
            return 0

        from data_crawler.db.connection import executemany

        sql = """
        INSERT INTO stock_cn_history
            (symbol, name, trade_date, open_price, high_price, low_price, close_price,
             volume, amount, change_pct, change_amount, turnover_rate)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            open_price = VALUES(open_price),
            high_price = VALUES(high_price),
            low_price = VALUES(low_price),
            close_price = VALUES(close_price),
            volume = VALUES(volume),
            amount = VALUES(amount),
            change_pct = VALUES(change_pct),
            change_amount = VALUES(change_amount),
            turnover_rate = VALUES(turnover_rate)
        """

        params = []
        for row in data:
            params.append((
                symbol,
                name,
                row.get("date"),
                row.get("open"),
                row.get("high"),
                row.get("low"),
                row.get("close"),
                row.get("volume"),
                row.get("amount"),
                row.get("change_pct"),
                row.get("change_amount"),
                row.get("turnover_rate"),
            ))

        try:
            count = executemany(sql, params)
            logger.info(f"Saved {count} records for CN stock {symbol} to database")
            return count
        except Exception as e:
            logger.error(f"Failed to save CN stock {symbol} to database: {e}")
            raise

    @staticmethod
    def save_us_stock_to_db(symbol: str, name: str, data: List[Dict]) -> int:
        """
        保存美股历史数据到数据库

        Args:
            symbol: 股票代码
            name: 股票名称
            data: 历史数据列表

        Returns:
            插入/更新的记录数
        """
        if not data:
            return 0

        from data_crawler.db.connection import executemany

        sql = """
        INSERT INTO stock_us_history
            (symbol, name, trade_date, open_price, high_price, low_price, close_price,
             volume, change_pct, change_amount)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            open_price = VALUES(open_price),
            high_price = VALUES(high_price),
            low_price = VALUES(low_price),
            close_price = VALUES(close_price),
            volume = VALUES(volume),
            change_pct = VALUES(change_pct),
            change_amount = VALUES(change_amount)
        """

        params = []
        for row in data:
            params.append((
                symbol,
                name,
                row.get("date"),
                row.get("open"),
                row.get("high"),
                row.get("low"),
                row.get("close"),
                row.get("volume"),
                row.get("change_pct"),
                row.get("change_amount"),
            ))

        try:
            count = executemany(sql, params)
            logger.info(f"Saved {count} records for US stock {symbol} to database")
            return count
        except Exception as e:
            logger.error(f"Failed to save US stock {symbol} to database: {e}")
            raise
