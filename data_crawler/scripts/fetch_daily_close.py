#!/usr/bin/env python3
"""Standalone: fetch today's closing data for all categories."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from db.init_tables                import init_all_tables
from crawlers.index_crawler        import fetch_today_indices
from crawlers.crypto_fx_crawler    import fetch_today_crypto_fx
from crawlers.commodity_crawler    import fetch_today_commodities

if __name__ == "__main__":
    init_all_tables()
    print("=== 指数K线 ===")
    fetch_today_indices()
    print("=== 加密/汇率K线 ===")
    fetch_today_crypto_fx()
    print("=== 贵金属K线 ===")
    fetch_today_commodities()
    print("=== 完成 ===")
