from datetime import date, datetime, timedelta
from typing import Optional, Set

import akshare as ak
import pandas as pd


class TradingCalendar:
    """交易日历管理器"""

    def __init__(self):
        self._a_share_calendar: Optional[Set[date]] = None
        self._last_update: Optional[datetime] = None
        self._update_interval_days = 7

    def is_a_share_trading_day(self, check_date: Optional[date] = None) -> bool:
        """
        判断是否为A股交易日

        Args:
            check_date: 要检查的日期，None表示今天

        Returns:
            是否为交易日
        """
        if check_date is None:
            check_date = date.today()

        # 快速检查：周末不是交易日
        if check_date.weekday() >= 5:  # 5=周六, 6=周日
            return False

        # 刷新日历（如果需要）
        if self._should_refresh_calendar():
            self._load_a_share_calendar()

        # 检查是否在交易日列表中
        if self._a_share_calendar is None:
            print("[WARN] Trading calendar not loaded, assuming trading day")
            return True

        return check_date in self._a_share_calendar

    def is_us_trading_day(self, check_date: Optional[date] = None) -> bool:
        """
        判断是否为美股交易日（包含节假日判断）

        Args:
            check_date: 要检查的日期，None表示今天

        Returns:
            是否为交易日
        """
        if check_date is None:
            check_date = date.today()

        # 1. 快速检查：周末不是交易日
        if check_date.weekday() >= 5:  # 5=周六, 6=周日
            return False

        # 2. 检查是否为美股节假日
        if self._is_us_market_holiday(check_date):
            return False

        return True

    def _should_refresh_calendar(self) -> bool:
        """判断是否需要刷新日历"""
        if self._a_share_calendar is None:
            return True

        if self._last_update is None:
            return True

        days_since_update = (datetime.now() - self._last_update).days
        return days_since_update >= self._update_interval_days

    def _load_a_share_calendar(self):
        """加载A股交易日历"""
        try:
            print("[INFO] Loading A-share trading calendar...")
            df = ak.tool_trade_date_hist_sina()

            if df is None or df.empty:
                print("[WARN] Failed to load trading calendar")
                return

            # 将trade_date列转换为date对象
            dates = pd.to_datetime(df["trade_date"]).dt.date
            self._a_share_calendar = set(dates)
            self._last_update = datetime.now()

            print(
                f"[INFO] Trading calendar loaded: {len(self._a_share_calendar)} trading days"
            )
        except Exception as e:
            print(f"[ERROR] Failed to load trading calendar: {e}")
            self._a_share_calendar = None

    def get_recent_trading_days(self, count: int = 5) -> list[date]:
        """
        获取最近的交易日

        Args:
            count: 数量

        Returns:
            交易日列表
        """
        if self._should_refresh_calendar():
            self._load_a_share_calendar()

        if self._a_share_calendar is None:
            return []

        today = date.today()
        recent_days = []

        # 从今天往前查找
        check_date = today
        while len(recent_days) < count and check_date > today - timedelta(days=30):
            if check_date in self._a_share_calendar:
                recent_days.append(check_date)
            check_date -= timedelta(days=1)

        return recent_days

    def _is_us_market_holiday(self, check_date: date) -> bool:
        """
        判断是否为美股市场节假日

        包含以下节假日:
        - 新年 (New Year's Day) - 1月1日
        - 马丁·路德·金纪念日 (MLK Day) - 1月第三个星期一
        - 总统日 (Presidents' Day) - 2月第三个星期一
        - 耶稣受难日 (Good Friday) - 复活节前的星期五
        - 阵亡将士纪念日 (Memorial Day) - 5月最后一个星期一
        - 独立日 (Independence Day) - 7月4日
        - 劳动节 (Labor Day) - 9月第一个星期一
        - 感恩节 (Thanksgiving) - 11月第四个星期四
        - 圣诞节 (Christmas) - 12月25日

        Args:
            check_date: 要检查的日期

        Returns:
            是否为节假日
        """
        year = check_date.year
        month = check_date.month
        day = check_date.day

        # 新年（1月1日，如遇周末顺延）
        new_year = self._adjust_weekend_holiday(date(year, 1, 1))
        if check_date == new_year:
            return True

        # 马丁·路德·金纪念日（1月第三个星期一）
        mlk_day = self._get_nth_weekday(year, 1, 0, 3)  # 0=Monday
        if check_date == mlk_day:
            return True

        # 总统日（2月第三个星期一）
        presidents_day = self._get_nth_weekday(year, 2, 0, 3)
        if check_date == presidents_day:
            return True

        # 耶稣受难日（复活节前的星期五）
        good_friday = self._get_good_friday(year)
        if check_date == good_friday:
            return True

        # 阵亡将士纪念日（5月最后一个星期一）
        memorial_day = self._get_last_weekday(year, 5, 0)
        if check_date == memorial_day:
            return True

        # 独立日（7月4日，如遇周末顺延）
        independence_day = self._adjust_weekend_holiday(date(year, 7, 4))
        if check_date == independence_day:
            return True

        # 劳动节（9月第一个星期一）
        labor_day = self._get_nth_weekday(year, 9, 0, 1)
        if check_date == labor_day:
            return True

        # 感恩节（11月第四个星期四）
        thanksgiving = self._get_nth_weekday(year, 11, 3, 4)  # 3=Thursday
        if check_date == thanksgiving:
            return True

        # 圣诞节（12月25日，如遇周末顺延）
        christmas = self._adjust_weekend_holiday(date(year, 12, 25))
        if check_date == christmas:
            return True

        return False

    def _get_nth_weekday(self, year: int, month: int, weekday: int, n: int) -> date:
        """
        获取某月第N个星期X

        Args:
            year: 年份
            month: 月份
            weekday: 星期几（0=周一, 6=周日）
            n: 第几个（1-5）

        Returns:
            日期
        """
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()

        # 计算第一个目标星期几是几号
        if weekday >= first_weekday:
            first_target = 1 + (weekday - first_weekday)
        else:
            first_target = 1 + (7 - first_weekday + weekday)

        # 计算第N个目标星期几
        target_day = first_target + (n - 1) * 7

        return date(year, month, target_day)

    def _get_last_weekday(self, year: int, month: int, weekday: int) -> date:
        """
        获取某月最后一个星期X

        Args:
            year: 年份
            month: 月份
            weekday: 星期几（0=周一, 6=周日）

        Returns:
            日期
        """
        # 获取下个月的第一天
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)

        # 往前推到上个月的最后一天
        last_day = next_month - timedelta(days=1)

        # 往前找到最后一个目标星期几
        while last_day.weekday() != weekday:
            last_day -= timedelta(days=1)

        return last_day

    def _adjust_weekend_holiday(self, holiday: date) -> date:
        """
        调整周末节假日（周六顺延到周一，周日顺延到周一）

        Args:
            holiday: 原始节假日

        Returns:
            调整后的节假日
        """
        if holiday.weekday() == 5:  # 周六
            return holiday + timedelta(days=2)  # 顺延到周一
        elif holiday.weekday() == 6:  # 周日
            return holiday + timedelta(days=1)  # 顺延到周一
        return holiday

    def _get_good_friday(self, year: int) -> date:
        """
        计算耶稣受难日（复活节前的星期五）
        使用Meeus/Jones/Butcher算法计算复活节

        Args:
            year: 年份

        Returns:
            耶稣受难日
        """
        # 使用高斯算法计算复活节日期
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1

        easter = date(year, month, day)

        # 耶稣受难日是复活节前的星期五（往前推2天）
        good_friday = easter - timedelta(days=2)

        return good_friday
