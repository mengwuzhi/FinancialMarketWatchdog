# -*- coding: utf-8 -*-
"""测试美股交易日判断功能"""

from datetime import date
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.trading_calendar import TradingCalendar


def test_us_trading_days():
    """测试美股交易日判断"""
    calendar = TradingCalendar()

    # 2024年美股节假日测试
    test_cases = [
        # (日期, 是否为交易日, 节假日名称)
        (date(2024, 1, 1), False, "New Year's Day"),
        (date(2024, 1, 15), False, "MLK Day"),
        (date(2024, 2, 19), False, "Presidents' Day"),
        (date(2024, 3, 29), False, "Good Friday"),
        (date(2024, 5, 27), False, "Memorial Day"),
        (date(2024, 7, 4), False, "Independence Day"),
        (date(2024, 9, 2), False, "Labor Day"),
        (date(2024, 11, 28), False, "Thanksgiving"),
        (date(2024, 12, 25), False, "Christmas"),
        # 普通交易日
        (date(2024, 1, 2), True, "Normal Trading Day"),
        (date(2024, 3, 15), True, "Normal Trading Day"),
        (date(2024, 6, 10), True, "Normal Trading Day"),
        # 周末
        (date(2024, 1, 6), False, "Saturday"),
        (date(2024, 1, 7), False, "Sunday"),
    ]

    print("=" * 80)
    print("US Stock Market Trading Day Test")
    print("=" * 80)

    passed = 0
    failed = 0

    for test_date, expected_trading, description in test_cases:
        is_trading = calendar.is_us_trading_day(test_date)
        status = "[PASS]" if is_trading == expected_trading else "[FAIL]"

        if is_trading == expected_trading:
            passed += 1
        else:
            failed += 1

        expected_str = "Trading" if expected_trading else "Holiday"
        actual_str = "Trading" if is_trading else "Holiday"

        print(
            f"{status} | {test_date.strftime('%Y-%m-%d %A'):20s} | "
            f"Expected: {expected_str:7s} | Actual: {actual_str:7s} | {description}"
        )

    print("=" * 80)
    print(f"Test Result: Passed {passed} / Failed {failed} / Total {passed + failed}")
    print("=" * 80)

    # 2025年节假日测试
    print("\n2025 US Stock Market Holidays Test")
    print("-" * 80)

    test_cases_2025 = [
        (date(2025, 1, 1), False, "New Year's Day"),
        (date(2025, 1, 20), False, "MLK Day"),
        (date(2025, 2, 17), False, "Presidents' Day"),
        (date(2025, 4, 18), False, "Good Friday"),
        (date(2025, 5, 26), False, "Memorial Day"),
        (date(2025, 7, 4), False, "Independence Day"),
        (date(2025, 9, 1), False, "Labor Day"),
        (date(2025, 11, 27), False, "Thanksgiving"),
        (date(2025, 12, 25), False, "Christmas"),
    ]

    for test_date, expected_trading, description in test_cases_2025:
        is_trading = calendar.is_us_trading_day(test_date)
        status = "[PASS]" if is_trading == expected_trading else "[FAIL]"
        actual_str = "Trading" if is_trading else "Holiday"
        print(
            f"{status} | {test_date.strftime('%Y-%m-%d %A'):20s} | "
            f"{actual_str:7s} | {description}"
        )

    print("-" * 80)

    return passed == len(test_cases)


if __name__ == "__main__":
    success = test_us_trading_days()
    sys.exit(0 if success else 1)
