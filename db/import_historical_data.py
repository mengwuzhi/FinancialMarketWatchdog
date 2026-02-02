# -*- coding: utf-8 -*-
"""
股票历史数据导入工具
支持A股和美股10年历史数据批量导入
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from db import insert_many, insert_row, select_one, execute
import time

class StockDataImporter:
    """股票数据导入器"""

    def __init__(self):
        self.end_date = datetime.now().strftime('%Y%m%d')
        self.start_date_10y = (datetime.now() - timedelta(days=3650)).strftime('%Y%m%d')

    # ==================== A股数据导入 ====================

    def import_cn_stock_list(self):
        """导入A股股票列表"""
        print("\n[1/5] Importing CN stock list...")

        try:
            # 获取A股列表
            df = ak.stock_zh_a_spot_em()

            records = []
            for _, row in df.iterrows():
                records.append({
                    'symbol': row['代码'],
                    'name': row['名称'],
                    'market': 'CN_A',
                    'security_type': 'STOCK',
                    'exchange': 'SZSE' if row['代码'].startswith('0') or row['代码'].startswith('3') else 'SSE',
                    'is_active': 1
                })

            insert_many('stock_info', records)
            print(f"✓ Imported {len(records)} CN stocks")

        except Exception as e:
            print(f"✗ Error: {e}")

    def import_cn_stock_history(self, symbol: str, start_date: str = None, end_date: str = None):
        """导入单只A股历史数据"""
        if start_date is None:
            start_date = self.start_date_10y
        if end_date is None:
            end_date = self.end_date

        try:
            # 获取历史数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )

            if df is None or df.empty:
                return 0

            # 转换为数据库格式
            records = []
            for _, row in df.iterrows():
                records.append({
                    'symbol': symbol,
                    'trade_date': row['日期'],
                    'open': float(row['开盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'close': float(row['收盘']),
                    'volume': int(row['成交量']) if pd.notna(row['成交量']) else 0,
                    'amount': float(row['成交额']) if pd.notna(row['成交额']) else 0,
                    'change_pct': float(row['涨跌幅']) if pd.notna(row['涨跌幅']) else None,
                    'amplitude': float(row['振幅']) if '振幅' in row and pd.notna(row['振幅']) else None,
                    'turnover_rate': float(row['换手率']) if '换手率' in row and pd.notna(row['换手率']) else None
                })

            # 批量插入（忽略重复）
            if records:
                # 使用ON DUPLICATE KEY UPDATE避免重复
                sql = """
                    INSERT INTO cn_stock_daily
                    (symbol, trade_date, open, high, low, close, volume, amount,
                     change_pct, amplitude, turnover_rate)
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    open=VALUES(open), high=VALUES(high), low=VALUES(low),
                    close=VALUES(close), volume=VALUES(volume), amount=VALUES(amount),
                    change_pct=VALUES(change_pct), amplitude=VALUES(amplitude),
                    turnover_rate=VALUES(turnover_rate)
                """

                values = [
                    (r['symbol'], r['trade_date'], r['open'], r['high'], r['low'],
                     r['close'], r['volume'], r['amount'], r['change_pct'],
                     r['amplitude'], r['turnover_rate'])
                    for r in records
                ]

                from db.core import executemany
                executemany(sql, values)

            return len(records)

        except Exception as e:
            print(f"  ✗ Error importing {symbol}: {e}")
            return 0

    def batch_import_cn_stocks(self, limit: int = None):
        """批量导入A股历史数据"""
        print("\n[2/5] Importing CN stock historical data...")

        # 获取股票列表
        from db import select_rows
        stocks = select_rows(
            'stock_info',
            ['symbol', 'name'],
            {'market': 'CN_A', 'is_active': 1}
        )

        if limit:
            stocks = stocks[:limit]

        total = len(stocks)
        success_count = 0

        for idx, stock in enumerate(stocks, 1):
            symbol = stock['symbol']
            name = stock['name']

            print(f"[{idx}/{total}] {symbol} {name}...", end=' ')

            # 检查是否已有数据
            existing = select_one(
                'cn_stock_daily',
                ['COUNT(*) as count'],
                {'symbol': symbol}
            )

            if existing and existing['count'] > 0:
                print(f"(skip, {existing['count']} records exist)")
                continue

            count = self.import_cn_stock_history(symbol)

            if count > 0:
                print(f"✓ {count} records")
                success_count += 1
            else:
                print("✗ failed")

            # 避免请求过快
            time.sleep(0.5)

        print(f"\n✓ Successfully imported {success_count}/{total} stocks")

    # ==================== 美股数据导入 ====================

    def import_us_stock_list(self):
        """导入美股股票列表（示例）"""
        print("\n[3/5] Importing US stock list...")

        # 示例：手动添加常见美股
        us_stocks = [
            ('AAPL', 'Apple Inc.', 'NASDAQ'),
            ('MSFT', 'Microsoft Corporation', 'NASDAQ'),
            ('GOOGL', 'Alphabet Inc.', 'NASDAQ'),
            ('AMZN', 'Amazon.com Inc.', 'NASDAQ'),
            ('TSLA', 'Tesla Inc.', 'NASDAQ'),
            ('META', 'Meta Platforms Inc.', 'NASDAQ'),
            ('NVDA', 'NVIDIA Corporation', 'NASDAQ'),
            ('JPM', 'JPMorgan Chase & Co.', 'NYSE'),
            ('V', 'Visa Inc.', 'NYSE'),
            ('WMT', 'Walmart Inc.', 'NYSE'),
        ]

        records = []
        for symbol, name, exchange in us_stocks:
            records.append({
                'symbol': symbol,
                'name': name,
                'market': 'US',
                'security_type': 'STOCK',
                'exchange': exchange,
                'is_active': 1
            })

        insert_many('stock_info', records)
        print(f"✓ Imported {len(records)} US stocks")

    def import_us_stock_history(self, symbol: str, start_date: str = None, end_date: str = None):
        """导入单只美股历史数据"""
        if start_date is None:
            start_date = self.start_date_10y
        if end_date is None:
            end_date = self.end_date

        try:
            # 获取美股历史数据
            df = ak.stock_us_hist(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )

            if df is None or df.empty:
                return 0

            # 转换为数据库格式
            records = []
            for _, row in df.iterrows():
                records.append({
                    'symbol': symbol,
                    'trade_date': row['日期'],
                    'open': float(row['开盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'close': float(row['收盘']),
                    'volume': int(row['成交量']) if pd.notna(row['成交量']) else 0,
                    'change_pct': float(row['涨跌幅']) if '涨跌幅' in row and pd.notna(row['涨跌幅']) else None
                })

            # 批量插入
            if records:
                sql = """
                    INSERT INTO us_stock_daily
                    (symbol, trade_date, open, high, low, close, volume, change_pct)
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    open=VALUES(open), high=VALUES(high), low=VALUES(low),
                    close=VALUES(close), volume=VALUES(volume), change_pct=VALUES(change_pct)
                """

                values = [
                    (r['symbol'], r['trade_date'], r['open'], r['high'], r['low'],
                     r['close'], r['volume'], r['change_pct'])
                    for r in records
                ]

                from db.core import executemany
                executemany(sql, values)

            return len(records)

        except Exception as e:
            print(f"  ✗ Error importing {symbol}: {e}")
            return 0

    def batch_import_us_stocks(self):
        """批量导入美股历史数据"""
        print("\n[4/5] Importing US stock historical data...")

        from db import select_rows
        stocks = select_rows(
            'stock_info',
            ['symbol', 'name'],
            {'market': 'US', 'is_active': 1}
        )

        total = len(stocks)
        success_count = 0

        for idx, stock in enumerate(stocks, 1):
            symbol = stock['symbol']
            name = stock['name']

            print(f"[{idx}/{total}] {symbol} {name}...", end=' ')

            count = self.import_us_stock_history(symbol)

            if count > 0:
                print(f"✓ {count} records")
                success_count += 1
            else:
                print("✗ failed")

            time.sleep(1)  # 美股API较慢，增加间隔

        print(f"\n✓ Successfully imported {success_count}/{total} stocks")

    # ==================== 增量更新 ====================

    def daily_update_cn(self):
        """A股每日增量更新"""
        print("\n[5/5] Daily update for CN stocks...")

        from db import select_rows, fetch_one

        stocks = select_rows(
            'stock_info',
            ['symbol'],
            {'market': 'CN_A', 'is_active': 1}
        )

        today = datetime.now().strftime('%Y%m%d')
        update_count = 0

        for stock in stocks:
            symbol = stock['symbol']

            # 检查最后更新日期
            last = fetch_one(
                f"SELECT MAX(trade_date) as last_date FROM cn_stock_daily WHERE symbol = '{symbol}'"
            )

            if last and last['last_date']:
                # 从最后日期+1天开始更新
                last_date = last['last_date']
                start = (last_date + timedelta(days=1)).strftime('%Y%m%d')

                if start >= today:
                    continue  # 已是最新

                count = self.import_cn_stock_history(symbol, start, today)
                if count > 0:
                    update_count += 1
                    print(f"  {symbol}: +{count} records")

        print(f"✓ Updated {update_count} stocks")

    # ==================== 主流程 ====================

    def run_full_import(self, cn_stock_limit: int = None):
        """完整导入流程"""
        print("=" * 80)
        print("Stock Historical Data Import")
        print(f"Date Range: {self.start_date_10y} ~ {self.end_date}")
        print("=" * 80)

        # 1. 导入A股列表
        self.import_cn_stock_list()

        # 2. 导入A股历史数据
        self.batch_import_cn_stocks(limit=cn_stock_limit)

        # 3. 导入美股列表
        self.import_us_stock_list()

        # 4. 导入美股历史数据
        self.batch_import_us_stocks()

        print("\n" + "=" * 80)
        print("✓ Import completed!")
        print("=" * 80)


if __name__ == "__main__":
    importer = StockDataImporter()

    # 示例1：测试导入（只导入前10只股票）
    print("Running test import (first 10 stocks)...")
    importer.run_full_import(cn_stock_limit=10)

    # 示例2：完整导入（所有股票）
    # importer.run_full_import()

    # 示例3：每日增量更新
    # importer.daily_update_cn()
