from datetime import datetime, timedelta
from typing import Dict, Optional

import requests


class ExternalDataProvider:
    """
    外部数据提供者（汇率、数字货币、贵金属、美股）

    数据源：
    - 离岸人民币：东方财富 / 新浪财经
    - 加密货币：Gate.io
    - 美股：东方财富（stock_us_spot_em）
    - 贵金属：新浪财经（COMEX）
    """

    @staticmethod
    def get_offshore_rmb_rate() -> Optional[Dict]:
        """
        获取离岸人民币汇率（USD/CNH）
        Returns: {'rate': 7.25, 'change_pct': -0.1}
        """
        try:
            # 方案1: 使用东方财富API（最准确的离岸人民币CNH数据）
            try:
                url = "https://push2.eastmoney.com/api/qt/stock/get"
                params = {
                    "secid": "133.USDCNH",  # 离岸人民币
                    "fields": "f43,f44,f45,f46,f169,f170"  # f43=最新价, f46=昨收, f169=涨跌额, f170=涨跌幅
                }
                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if "data" in data and data["data"] and "f43" in data["data"]:
                        rate = data["data"]["f43"] / 10000  # 东财返回的是放大10000倍的值
                        change_pct = data["data"].get("f170", 0) / 100 if "f170" in data["data"] else 0.0  # 涨跌幅（百分比）

                        print(f"[DEBUG] 东方财富USDCNH汇率: {rate:.4f} ({change_pct:+.2f}%)")
                        return {"rate": rate, "change_pct": change_pct, "timestamp": datetime.now()}
            except Exception as e:
                print(f"[DEBUG] 东方财富API获取失败: {e}")

            # 方案2: 使用新浪财经API（备选离岸人民币数据）
            try:
                url = "https://hq.sinajs.cn/list=fx_susdcnh"
                headers = {"Referer": "https://finance.sina.com.cn"}
                response = requests.get(url, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.text
                    # 格式: var hq_str_fx_susdcnh="时间,买入价,卖出价,昨收,..."
                    if "fx_susdcnh=" in data:
                        parts = data.split("=")[1].strip('"\n').split(",")
                        if len(parts) >= 4:
                            rate = float(parts[1])  # 买入价
                            prev_close = float(parts[3]) if parts[3] else rate
                            change_pct = ((rate - prev_close) / prev_close * 100) if prev_close > 0 else 0.0

                            print(f"[DEBUG] 新浪财经USDCNH汇率: {rate:.4f} ({change_pct:+.2f}%)")
                            return {"rate": rate, "change_pct": change_pct, "timestamp": datetime.now()}
            except Exception as e:
                print(f"[DEBUG] 新浪财经API获取失败: {e}")

            # 方案3: 使用akshare的在岸人民币数据（CNY，作为近似）
            try:
                import akshare as ak
                df = ak.fx_spot_quote()
                if df is not None and not df.empty:
                    # 查找USD/CNY
                    usd_cny = df[df.iloc[:, 0].str.contains("USD/CNY", na=False)]
                    if not usd_cny.empty:
                        rate = usd_cny.iloc[0, 1]  # 买入价
                        print(f"[DEBUG] akshare USD/CNY汇率: {rate:.4f} (在岸CNY)")
                        return {"rate": rate, "change_pct": 0.0, "timestamp": datetime.now()}
            except Exception as e:
                print(f"[DEBUG] akshare获取失败: {e}")

            # 方案4: 使用固定汇率作为最后兜底
            print("[WARN] 所有汇率数据源都失败，使用固定汇率7.00")
            return {"rate": 7.00, "change_pct": 0.0, "timestamp": datetime.now()}

        except Exception as e:
            print(f"[ERROR] Failed to get offshore RMB rate: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_crypto_prices() -> Optional[Dict]:
        """
        获取数字货币价格（BTC、ETH）
        使用 Gate.io API（国内服务器可访问）
        Returns: {'BTC': {'price': 45000, 'change_pct': 2.3}, 'ETH': {...}}
        """
        try:
            url = "https://api.gateio.ws/api/v4/spot/tickers"
            response = requests.get(url, timeout=10)
            data = response.json()

            result = {}
            for ticker in data:
                if ticker.get('currency_pair') == 'BTC_USDT':
                    result["BTC"] = {
                        "price": float(ticker['last']),
                        "change_pct": float(ticker.get('change_percentage', 0)),
                    }
                elif ticker.get('currency_pair') == 'ETH_USDT':
                    result["ETH"] = {
                        "price": float(ticker['last']),
                        "change_pct": float(ticker.get('change_percentage', 0)),
                    }

            if result:
                return result
            else:
                print("[WARN] Gate.io 返回数据中未找到 BTC/ETH")
                return None
        except Exception as e:
            print(f"[ERROR] 获取加密货币数据失败: {e}")
            return None

    @staticmethod
    def get_precious_metals() -> Optional[Dict]:
        """
        获取贵金属价格（COMEX黄金白银）
        Returns: {'gold': {'price': 2600, 'change_pct': 0.5, 'source': 'COMEX'}, 'silver': {...}, 'gold_silver_ratio': 85.2}
        """
        try:
            result = {}

            # 方案1: 使用新浪财经API获取COMEX黄金白银（最可靠）
            try:
                headers = {"Referer": "https://finance.sina.com.cn"}

                # 获取COMEX黄金
                url_gold = "https://hq.sinajs.cn/list=hf_GC"
                response = requests.get(url_gold, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.text
                    # 格式: var hq_str_hf_GC="价格,字段2,昨收,开盘,最高,最低,时间,买价,卖价,..."
                    if "hf_GC=" in data:
                        parts = data.split("=")[1].strip('"\n').split(",")
                        if len(parts) >= 4:
                            price = float(parts[0])  # 当前价
                            prev_close = float(parts[2]) if parts[2] else price  # 昨收
                            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0.0

                            result["gold"] = {
                                "price": price,
                                "change_pct": change_pct,
                                "source": "COMEX",
                            }
                            print(f"[DEBUG] 新浪COMEX黄金: ${price:.2f}/盎司 ({change_pct:+.2f}%)")

                # 获取COMEX白银
                url_silver = "https://hq.sinajs.cn/list=hf_SI"
                response = requests.get(url_silver, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.text
                    if "hf_SI=" in data:
                        parts = data.split("=")[1].strip('"\n').split(",")
                        if len(parts) >= 4:
                            price = float(parts[0])
                            prev_close = float(parts[2]) if parts[2] else price
                            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0.0

                            result["silver"] = {
                                "price": price,
                                "change_pct": change_pct,
                                "source": "COMEX",
                            }
                            print(f"[DEBUG] 新浪COMEX白银: ${price:.2f}/盎司 ({change_pct:+.2f}%)")

            except Exception as e:
                print(f"[DEBUG] 新浪财经贵金属获取失败: {e}")

            # 方案2: 尝试东方财富API（备选）
            if not result:
                try:
                    # 尝试获取黄金
                    url = "https://push2.eastmoney.com/api/qt/stock/get"
                    params = {"secid": "113.GC00Y", "fields": "f43,f46,f170"}
                    response = requests.get(url, params=params, timeout=10)
                    if response.status_code == 200 and response.json().get("data"):
                        data = response.json()["data"]
                        price = data.get("f43", 0) / 100
                        change_pct = data.get("f170", 0) / 100
                        if price > 0:
                            result["gold"] = {
                                "price": price,
                                "change_pct": change_pct,
                                "source": "COMEX",
                            }
                except Exception as e:
                    print(f"[DEBUG] 东方财富贵金属获取失败: {e}")

            # 计算金银比
            if "gold" in result and "silver" in result:
                gold_price = result["gold"]["price"]
                silver_price = result["silver"]["price"]
                if gold_price > 0 and silver_price > 0:
                    result["gold_silver_ratio"] = gold_price / silver_price
                    print(f"[DEBUG] 金银比: {result['gold_silver_ratio']:.2f}")

            return result if result else None
        except Exception as e:
            print(f"[ERROR] Failed to get precious metals: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_us_stocks(symbols: list) -> Optional[Dict]:
        """
        获取美股个股数据（使用东方财富接口）

        国内服务器可直接访问，无需代理

        Args:
            symbols: 股票代码列表，如['AAPL', 'MSFT', 'NVDA']
        Returns: {'AAPL': {'price': 180.5, 'change_pct': 1.2, 'name': 'Apple Inc.'}, ...}
        """
        try:
            import akshare as ak
            import time

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
                    # 精确匹配优先（优化：避免匹配到ETF等衍生品）
                    # 尝试多种匹配方式：
                    # 1. 精确匹配代码
                    # 2. 匹配带交易所前缀的代码（如 "105.AAPL"）
                    # 3. 匹配代码末尾（避免匹配到 "AMD" 时匹配到 "GAMD"）

                    row = None

                    # 方法1: 精确匹配（最优先）
                    exact_match = df[df["代码"] == symbol]
                    if not exact_match.empty:
                        row = exact_match

                    # 方法2: 匹配交易所前缀格式（如 "105.AAPL"）
                    if row is None or row.empty:
                        prefix_match = df[df["代码"].str.match(f"^\d+\.{symbol}$", na=False, case=False)]
                        if not prefix_match.empty:
                            row = prefix_match

                    # 方法3: 精确匹配代码末尾（包含点号分隔符）
                    if row is None or row.empty:
                        suffix_match = df[df["代码"].str.endswith(f".{symbol}", na=False)]
                        if not suffix_match.empty:
                            row = suffix_match

                    if row is not None and not row.empty:
                        # 如果找到多个匹配，取第一个
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
