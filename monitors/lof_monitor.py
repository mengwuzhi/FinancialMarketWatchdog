from collections import deque
from datetime import datetime
from typing import Deque, Dict, List, Optional, Tuple
import time

import akshare as ak
import pandas as pd

from notifiers.dingtalk import DingTalkNotifier
from storage.state_manager import StateManager
from utils.data_parser import (
    compute_pct_series,
    find_column,
    fmt_value,
    get_column_map,
    order_by_codes,
    prepare_lof_df,
    series_to_float,
)


class LOFRealtimeMonitor:
    """LOF实时监控器"""

    def __init__(
        self,
        notifier: DingTalkNotifier,
        state_manager: StateManager,
        limit_codes: List[str],
        speed_codes: List[str],
        limit_pct: float = 9.9,
        speed_window_minutes: float = 10.0,
        speed_threshold_pct: float = 2.0,
    ):
        self.notifier = notifier
        self.state_manager = state_manager
        self.limit_codes = limit_codes
        self.speed_codes = speed_codes
        self.limit_pct = limit_pct
        self.speed_window_minutes = speed_window_minutes
        self.speed_threshold_pct = speed_threshold_pct

        # 初始化状态
        self.state_manager.ensure_key("limit", {})
        self.state_manager.ensure_key("speed", {})

        # 速度监控历史数据
        self.speed_history: Dict[str, Deque[Tuple[float, float]]] = {}

    def run_monitor(self):
        """执行一次监控"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now_ts = time.time()

        try:
            df = ak.fund_lof_spot_em()
            print(f"\n[{timestamp}]")

            prepared = prepare_lof_df(df)
            if prepared is None:
                print("No data returned. Check codes or market hours.")
                return

            cols = get_column_map(prepared)

            if self.limit_codes:
                print("Limit watch running...")
                self._process_limit_alerts(prepared, cols, timestamp)

            if self.speed_codes:
                print("Speed watch running...")
                self._process_speed_alerts(prepared, cols, timestamp, now_ts)

        except Exception as exc:
            print(f"Fetch error: {exc}")

    def _process_limit_alerts(
        self, df: pd.DataFrame, cols: Dict[str, Optional[str]], timestamp: str
    ):
        """处理涨停跌停提醒"""
        if not self.limit_codes:
            return

        subset = df[df["_code"].isin(self.limit_codes)].copy()
        missing = sorted(set(self.limit_codes) - set(subset["_code"]))
        if missing:
            print(f"[WARN] Missing limit codes: {', '.join(missing)}")
        if subset.empty:
            return

        subset = order_by_codes(subset, self.limit_codes)
        status, pct_series = self._compute_limit_status(subset, cols)
        if status is None:
            print("[WARN] No columns available to determine limit status.")
            return

        price_series = None
        if cols["price"]:
            price_series = series_to_float(subset[cols["price"]])
        name_col = cols["name"]

        limit_state = self.state_manager.get("limit", {})

        for idx, code in subset["_code"].items():
            cur_status = status.at[idx]
            last_status = limit_state.get(code, "NORMAL")
            name = str(subset.at[idx, name_col]) if name_col else ""
            price = (
                float(price_series.at[idx])
                if price_series is not None and pd.notna(price_series.at[idx])
                else None
            )
            pct = (
                float(pct_series.at[idx])
                if pct_series is not None and pd.notna(pct_series.at[idx])
                else None
            )

            if pct_series is not None and pct is None:
                continue
            if pct_series is None and price is None:
                continue

            if cur_status != last_status:
                if cur_status in ("LIMIT_UP", "LIMIT_DOWN"):
                    content = self._build_limit_message(
                        cur_status, code, name, price, pct, timestamp
                    )
                    self.notifier.send_text(content)
                elif last_status in ("LIMIT_UP", "LIMIT_DOWN") and cur_status == "NORMAL":
                    content = self._build_open_board_message(
                        last_status, code, name, price, pct, timestamp
                    )
                    self.notifier.send_text(content)

            limit_state[code] = cur_status

        self.state_manager.set("limit", limit_state)

    def _process_speed_alerts(
        self,
        df: pd.DataFrame,
        cols: Dict[str, Optional[str]],
        timestamp: str,
        now_ts: float,
    ):
        """处理急涨急跌提醒"""
        if not self.speed_codes:
            return

        subset = df[df["_code"].isin(self.speed_codes)].copy()
        missing = sorted(set(self.speed_codes) - set(subset["_code"]))
        if missing:
            print(f"[WARN] Missing speed codes: {', '.join(missing)}")
        if subset.empty:
            return
        if not cols["price"]:
            print("[WARN] No price column available; speed watch skipped.")
            return

        subset = order_by_codes(subset, self.speed_codes)
        price_series = series_to_float(subset[cols["price"]])
        name_col = cols["name"]
        window_seconds = self.speed_window_minutes * 60.0

        speed_state = self.state_manager.get("speed", {})

        for idx, code in subset["_code"].items():
            price = price_series.at[idx]
            if pd.isna(price):
                continue
            price_val = float(price)
            if price_val <= 0:
                continue

            change_pct = self._update_speed_history(
                code, now_ts, price_val, window_seconds
            )
            if change_pct is None:
                continue

            last_status = speed_state.get(code, "NORMAL")
            if change_pct >= self.speed_threshold_pct:
                cur_status = "FAST_UP"
            elif change_pct <= -self.speed_threshold_pct:
                cur_status = "FAST_DOWN"
            else:
                cur_status = "NORMAL"

            if cur_status != last_status and cur_status in ("FAST_UP", "FAST_DOWN"):
                direction = "UP" if cur_status == "FAST_UP" else "DOWN"
                name = str(subset.at[idx, name_col]) if name_col else ""
                content = self._build_speed_message(
                    direction,
                    code,
                    name,
                    price_val,
                    change_pct,
                    self.speed_window_minutes,
                    timestamp,
                )
                self.notifier.send_text(content)

            speed_state[code] = cur_status

        self.state_manager.set("speed", speed_state)

    def _compute_limit_status(
        self, df: pd.DataFrame, cols: Dict[str, Optional[str]]
    ) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
        """计算涨停跌停状态"""
        pct_series = compute_pct_series(df, cols)
        if pct_series is not None:
            status = pd.Series(["NORMAL"] * len(df), index=df.index)
            status[pct_series >= self.limit_pct] = "LIMIT_UP"
            status[pct_series <= -self.limit_pct] = "LIMIT_DOWN"
            return status, pct_series

        if cols["price"] and (cols["limit_up"] or cols["limit_down"]):
            status = pd.Series(["NORMAL"] * len(df), index=df.index)
            price = series_to_float(df[cols["price"]])
            if cols["limit_up"]:
                up = series_to_float(df[cols["limit_up"]])
                status[price >= up] = "LIMIT_UP"
            if cols["limit_down"]:
                down = series_to_float(df[cols["limit_down"]])
                status[price <= down] = "LIMIT_DOWN"
            return status, None

        return None, None

    def _update_speed_history(
        self, code: str, now_ts: float, price: float, window_seconds: float
    ) -> Optional[float]:
        """更新速度监控历史数据"""
        dq = self.speed_history.setdefault(code, deque())
        dq.append((now_ts, price))
        while dq and now_ts - dq[0][0] > window_seconds:
            dq.popleft()
        if len(dq) < 2:
            return None
        base_ts, base_price = dq[0]
        if not base_price:
            return None
        return (price - base_price) / base_price * 100.0

    def _build_limit_message(
        self,
        status: str,
        code: str,
        name: str,
        price: Optional[float],
        pct: Optional[float],
        timestamp: str,
    ) -> str:
        """构建涨停跌停消息"""
        title = "涨停提醒" if status == "LIMIT_UP" else "跌停提醒"
        lines = [
            title,
            f"时间: {timestamp}",
            f"代码: {code}",
        ]
        if name:
            lines.append(f"名称: {name}")
        if price is not None:
            lines.append(f"现价: {fmt_value(price, 3)}")
        if pct is not None:
            lines.append(f"涨跌幅: {fmt_value(pct, 2)}%")
        return "\n".join(lines)

    def _build_open_board_message(
        self,
        last_status: str,
        code: str,
        name: str,
        price: Optional[float],
        pct: Optional[float],
        timestamp: str,
    ) -> str:
        """构建开板消息"""
        last_label = "涨停" if last_status == "LIMIT_UP" else "跌停"
        title = "开板提醒"
        lines = [
            title,
            f"时间: {timestamp}",
            f"代码: {code}",
            f"前状态: {last_label}",
        ]
        if name:
            lines.append(f"名称: {name}")
        if price is not None:
            lines.append(f"现价: {fmt_value(price, 3)}")
        if pct is not None:
            lines.append(f"涨跌幅: {fmt_value(pct, 2)}%")
        return "\n".join(lines)

    def _build_speed_message(
        self,
        direction: str,
        code: str,
        name: str,
        price: Optional[float],
        change_pct: float,
        window_minutes: float,
        timestamp: str,
    ) -> str:
        """构建急涨急跌消息"""
        title = "涨速过快提醒" if direction == "UP" else "跌速过快提醒"
        lines = [
            title,
            f"时间: {timestamp}",
            f"代码: {code}",
            f"窗口: {fmt_value(window_minutes, 1)} 分钟",
            f"区间涨跌幅: {fmt_value(change_pct, 2)}%",
        ]
        if name:
            lines.append(f"名称: {name}")
        if price is not None:
            lines.append(f"现价: {fmt_value(price, 3)}")
        return "\n".join(lines)
