from datetime import datetime
from typing import Optional

from notifiers.dingtalk import DingTalkNotifier
from data_sources.akshare_provider import AKShareProvider
from data_sources.external_data import ExternalDataProvider
from utils.formatters import MessageFormatter
from config.us_stocks_config import get_us_stocks_config


class USStockDailyReporter:
    """美股市场日报生成器"""

    def __init__(self, notifier: Optional[DingTalkNotifier] = None):
        self.notifier = notifier
        self.data_provider = AKShareProvider()
        self.external_provider = ExternalDataProvider()
        self.formatter = MessageFormatter()

        # 从配置文件加载美股股票代码
        self.us_stock_config = get_us_stocks_config()

    def collect_data(self) -> dict:
        """收集美股市场数据（供API返回JSON）"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] US Stock Data Collection")

        data = {}
        data["indices"] = self._get_indices()

        all_stocks_data = self._get_all_us_stocks()
        data["tech_stocks"] = all_stocks_data.get("tech_stocks", {})
        data["chinese_stocks"] = all_stocks_data.get("chinese_stocks", {})

        data["global"] = self._get_global_data()
        return data

    def generate_report(self):
        """生成美股市场日报并发送通知（供定时任务调用）"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] US Stock Daily Report")

        try:
            data = self.collect_data()

            # 格式化并发送消息
            message = self.formatter.format_us_stock_report(data)
            if self.notifier:
                self.notifier.send_text(message)
            print("US stock daily report sent")

        except Exception as e:
            print(f"[ERROR] Failed to generate US stock report: {e}")
            raise

    def _get_indices(self) -> list:
        """获取主要指数"""
        df = self.data_provider.get_global_indices()
        if df is None or df.empty:
            return []

        index_names = {
            "道琼斯": "道琼斯工业指数",
            "纳斯达克": "纳斯达克指数",
            "标普500": "标普500指数",
        }

        result = []
        for key, name in index_names.items():
            row = df[df["名称"].str.contains(key, na=False)]
            if not row.empty:
                result.append({
                    "name": name,
                    "price": row["最新价"].values[0],
                    "change": row["涨跌幅"].values[0],
                })

        return result

    def _get_all_us_stocks(self) -> dict:
        """
        一次性获取所有美股数据（科技股+中概股）

        优化：将多次API调用合并为一次，避免重复获取全市场数据

        Returns:
            dict: {
                "tech_stocks": {symbol: {name, price, change_pct}, ...},
                "chinese_stocks": {symbol: {name, price, change_pct}, ...}
            }
        """
        result = {
            "tech_stocks": {},
            "chinese_stocks": {}
        }

        # 合并所有需要获取的股票代码
        all_symbols = []
        for group in self.us_stock_config.values():
            all_symbols.extend(group)

        print(f"[INFO] 准备获取 {len(all_symbols)} 只美股数据")
        print(f"[INFO] 科技股: {', '.join(self.us_stock_config['tech_stocks'])}")
        print(f"[INFO] 中概股: {', '.join(self.us_stock_config['chinese_stocks'])}")

        # 一次性获取所有股票数据
        all_data = self.external_provider.get_us_stocks(all_symbols)

        if not all_data:
            print("[WARN] 未能获取任何美股数据")
            return result

        # 按分组分配数据
        for symbol in self.us_stock_config["tech_stocks"]:
            if symbol in all_data:
                result["tech_stocks"][symbol] = all_data[symbol]

        for symbol in self.us_stock_config["chinese_stocks"]:
            if symbol in all_data:
                result["chinese_stocks"][symbol] = all_data[symbol]

        print(f"[INFO] 科技股获取成功: {len(result['tech_stocks'])}/{len(self.us_stock_config['tech_stocks'])}")
        print(f"[INFO] 中概股获取成功: {len(result['chinese_stocks'])}/{len(self.us_stock_config['chinese_stocks'])}")

        return result

    def _get_global_data(self) -> dict:
        """获取全球市场数据"""
        result = {}

        # 离岸人民币汇率
        rmb = self.external_provider.get_offshore_rmb_rate()
        if rmb:
            result["rmb"] = rmb

        # 数字货币
        crypto = self.external_provider.get_crypto_prices()
        if crypto:
            result["crypto"] = crypto

        # 贵金属
        metals = self.external_provider.get_precious_metals()
        if metals:
            result["metals"] = metals

        return result
