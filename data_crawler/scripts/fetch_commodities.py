#!/usr/bin/env python3
"""Standalone: fetch gold/silver daily K-line."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from db.init_tables               import init_all_tables
from crawlers.commodity_crawler   import fetch_all_commodities

if __name__ == "__main__":
    init_all_tables()
    fetch_all_commodities()
