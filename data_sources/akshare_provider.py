import akshare as ak
import pandas as pd
from typing import Optional
from utils.retry_helper import retry_on_failure
import requests
from http.client import RemoteDisconnected


class AKShareProvider:
    """AKShare数据提供者（已添加重试机制）"""

    @staticmethod
    @retry_on_failure(
        max_attempts=3,
        delay=5.0,
        exceptions=(
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException,
            RemoteDisconnected,
            ConnectionResetError,
            ConnectionAbortedError,
        ),
    )
    def get_a_share_indices() -> Optional[pd.DataFrame]:
        """获取A股指数行情（带3次重试，支持网络中断恢复）"""
        try:
            return ak.stock_zh_index_spot_em()
        except Exception as e:
            print(f"[ERROR] Failed to get A-share indices: {e}")
            raise

    @staticmethod
    @retry_on_failure(
        max_attempts=3,
        delay=5.0,
        exceptions=(
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException,
            RemoteDisconnected,
            ConnectionResetError,
            ConnectionAbortedError,
        ),
    )
    def get_a_share_stocks() -> Optional[pd.DataFrame]:
        """获取A股个股行情（带3次重试，支持网络中断恢复）"""
        try:
            return ak.stock_zh_a_spot_em()
        except Exception as e:
            print(f"[ERROR] Failed to get A-share stocks: {e}")
            raise

    @staticmethod
    def get_industry_boards() -> Optional[pd.DataFrame]:
        """获取行业板块"""
        try:
            return ak.stock_board_industry_name_em()
        except Exception as e:
            print(f"[ERROR] Failed to get industry boards: {e}")
            return None

    @staticmethod
    def get_concept_boards() -> Optional[pd.DataFrame]:
        """获取概念板块"""
        try:
            return ak.stock_board_concept_name_em()
        except Exception as e:
            print(f"[ERROR] Failed to get concept boards: {e}")
            return None

    @staticmethod
    def get_main_fund_flow() -> Optional[pd.DataFrame]:
        """获取主力资金流向"""
        try:
            return ak.stock_individual_fund_flow_rank(indicator="今日")
        except Exception as e:
            print(f"[ERROR] Failed to get main fund flow: {e}")
            return None

    @staticmethod
    def get_global_indices() -> Optional[pd.DataFrame]:
        """获取全球指数"""
        try:
            return ak.index_global_spot_em()
        except Exception as e:
            print(f"[ERROR] Failed to get global indices: {e}")
            return None

    @staticmethod
    def get_trading_calendar() -> Optional[pd.DataFrame]:
        """获取交易日历"""
        try:
            return ak.tool_trade_date_hist_sina()
        except Exception as e:
            print(f"[ERROR] Failed to get trading calendar: {e}")
            return None
