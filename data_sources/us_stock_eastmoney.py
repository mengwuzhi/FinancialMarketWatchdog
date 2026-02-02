"""
美股数据获取 - 东方财富接口

替代yfinance，使用东方财富接口获取美股数据
国内服务器可直接访问，无需代理
"""
from typing import Optional, Dict
import time


class EastMoneyUSStockProvider:
    """东方财富美股数据提供者"""

    @staticmethod
    def get_us_stocks(symbols: list) -> Optional[Dict]:
        """
        获取美股个股数据（使用东方财富接口）

        Args:
            symbols: 股票代码列表，如 ["AAPL", "MSFT", "BABA"]

        Returns:
            dict: {
                "AAPL": {
                    "name": "Apple Inc.",
                    "price": 256.28,
                    "change_pct": -0.75
                },
                ...
            }

        Notes:
            - 一次性获取所有美股数据，然后筛选目标股票
            - 比yfinance逐个请求更稳定
            - 首次获取可能需要30-60秒（获取全市场数据）
        """
        try:
            import akshare as ak

            print(f"[INFO] 正在从东方财富获取美股数据（共{len(symbols)}只）...")
            start_time = time.time()

            # 获取美股实时行情（一次性获取所有数据）
            df = ak.stock_us_spot_em()

            elapsed = time.time() - start_time
            print(f"[INFO] 东方财富数据获取完成，耗时 {elapsed:.1f} 秒")

            if df is None or df.empty:
                print("[ERROR] 东方财富美股数据为空")
                return None

            print(f"[INFO] 东方财富返回 {len(df)} 只美股数据")

            result = {}
            for symbol in symbols:
                try:
                    # 在数据中查找对应股票（不区分大小写）
                    # 代码列可能包含交易所前缀，如 "105.AAPL"
                    row = df[df["代码"].str.contains(symbol, na=False, case=False)]

                    if not row.empty:
                        # 如果找到多个匹配（不太可能），取第一个
                        first_row = row.iloc[0]

                        result[symbol] = {
                            "name": first_row["名称"],
                            "price": float(first_row["最新价"]),
                            "change_pct": float(first_row["涨跌幅"])
                        }

                        print(f"[SUCCESS] {symbol} ({result[symbol]['name']}): "
                              f"${result[symbol]['price']:.2f} "
                              f"({result[symbol]['change_pct']:+.2f}%)")
                    else:
                        print(f"[WARN] {symbol} 未在东方财富数据中找到")

                except Exception as e:
                    print(f"[ERROR] 处理 {symbol} 数据失败: {e}")
                    continue

            success_rate = len(result) / len(symbols) * 100 if symbols else 0
            print(f"[INFO] 成功获取 {len(result)}/{len(symbols)} 只股票 ({success_rate:.0f}%)")

            return result if result else None

        except ImportError:
            print("[ERROR] akshare未安装，请运行: pip install akshare")
            return None
        except Exception as e:
            print(f"[ERROR] 获取美股数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_us_stock_sina(symbol: str) -> Optional[Dict]:
        """
        使用新浪财经接口获取单只美股数据（备选方案）

        Args:
            symbol: 股票代码，如 "AAPL"

        Returns:
            dict: {"name": "苹果", "price": 256.28, "change_pct": -0.75}
        """
        try:
            import requests

            # 新浪美股接口
            url = f"https://hq.sinajs.cn/list=gb_{symbol.lower()}"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return None

            # 解析数据
            content = response.text
            if not content or '""' in content:
                return None

            # 数据格式: var hq_str_gb_aapl="苹果,256.28,256.82,..."
            data = content.split('="')[1].split('",')[0].split(',')

            if len(data) < 5:
                return None

            name = data[0]
            current_price = float(data[1])
            prev_close = float(data[2])
            change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0

            return {
                "name": name,
                "price": current_price,
                "change_pct": change_pct
            }

        except Exception as e:
            print(f"[ERROR] 新浪财经获取 {symbol} 失败: {e}")
            return None

    @staticmethod
    def get_us_stocks_with_fallback(symbols: list) -> Optional[Dict]:
        """
        获取美股数据 - 双数据源容错

        优先使用东方财富，如果失败或数据不完整，降级到新浪财经

        Args:
            symbols: 股票代码列表

        Returns:
            dict: 股票数据字典
        """
        # 优先使用东方财富
        result = EastMoneyUSStockProvider.get_us_stocks(symbols)

        if result and len(result) >= len(symbols) * 0.7:  # 成功率>70%
            return result

        # 降级使用新浪财经
        print("[INFO] 东方财富数据不完整，尝试新浪财经补充...")
        result_sina = result if result else {}

        # 只补充缺失的股票
        missing_symbols = [s for s in symbols if s not in result_sina]

        for symbol in missing_symbols:
            data = EastMoneyUSStockProvider.get_us_stock_sina(symbol)
            if data:
                result_sina[symbol] = data
                print(f"[SUCCESS] 新浪财经补充 {symbol}")
            time.sleep(1)  # 避免限流

        return result_sina if result_sina else None


if __name__ == "__main__":
    # 测试代码
    print("=" * 80)
    print("测试东方财富美股数据获取")
    print("=" * 80)
    print()

    provider = EastMoneyUSStockProvider()

    # 测试科技股和中概股
    symbols = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "BABA", "PDD", "JD", "BIDU"]

    data = provider.get_us_stocks(symbols)

    if data:
        print()
        print("=" * 80)
        print("获取结果汇总:")
        print("=" * 80)
        for symbol, info in data.items():
            print(f"{symbol:6} {info['name']:30} ${info['price']:8.2f} ({info['change_pct']:+6.2f}%)")
    else:
        print()
        print("❌ 获取失败")
