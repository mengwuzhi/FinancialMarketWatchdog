from datetime import datetime
from typing import Dict, List, Optional


class MessageFormatter:
    """消息格式化工具"""

    @staticmethod
    def format_a_share_report(data: Dict) -> str:
        """
        格式化A股市场日报

        Args:
            data: 包含所有数据的字典

        Returns:
            格式化后的消息
        """
        lines = [
            "=" * 30,
            f"A股市场日报 - {datetime.now().strftime('%Y-%m-%d')}",
            "=" * 30,
            "",
        ]

        # 主要指数
        if "indices" in data and data["indices"]:
            lines.append("【主要指数】")
            for idx in data["indices"]:
                name = idx.get("name", "")
                price = idx.get("price", 0)
                change_pct = idx.get("change_pct", 0)
                change_amount = idx.get("change_amount", 0)

                # 格式化涨跌点数和涨跌幅
                sign_pct = "+" if change_pct >= 0 else ""
                sign_amt = "+" if change_amount >= 0 else ""

                lines.append(
                    f"{name}：{price:.2f}  "
                    f"{sign_amt}{change_amount:.2f}点 "
                    f"({sign_pct}{change_pct:.2f}%)"
                )
            lines.append("")

        # 市场概况
        if "market" in data:
            market = data["market"]
            lines.append("【市场概况】")
            lines.append(f"上涨家数：{market.get('up', 0)}")
            lines.append(f"下跌家数：{market.get('down', 0)}")
            lines.append(f"涨停：{market.get('limit_up', 0)}家")
            lines.append(f"跌停：{market.get('limit_down', 0)}家")
            lines.append("")

        # 热点板块
        if "sectors" in data:
            sectors = data["sectors"]
            if "industry" in sectors and sectors["industry"]:
                lines.append("【热门行业板块】")
                for i, sector in enumerate(sectors["industry"][:5], 1):
                    name = sector.get("板块名称", "")
                    change = sector.get("涨跌幅", 0)
                    lines.append(f"{i}. {name} {change:+.2f}%")
                lines.append("")

            if "concept" in sectors and sectors["concept"]:
                lines.append("【热门概念板块】")
                for i, concept in enumerate(sectors["concept"][:5], 1):
                    name = concept.get("板块名称", "")
                    change = concept.get("涨跌幅", 0)
                    lines.append(f"{i}. {name} {change:+.2f}%")
                lines.append("")

        # 资金流向
        if "funds" in data:
            funds = data["funds"]
            if "main_fund" in funds and funds["main_fund"]:
                lines.append("【主力资金净流入TOP3】")
                for i, stock in enumerate(funds["main_fund"][:3], 1):
                    code = stock.get("代码", "")
                    name = stock.get("名称", "")
                    inflow = stock.get("主力净流入", 0)
                    lines.append(f"{i}. {code} {name} {inflow:+.2f}亿")
                lines.append("")

        # 全球市场
        if "global" in data:
            global_data = data["global"]
            lines.append("【全球市场（最近12小时）】")

            if "rmb" in global_data:
                rmb = global_data["rmb"]
                rate = rmb.get("rate", 0)
                change = rmb.get("change_pct", 0)
                lines.append(f"离岸人民币：{rate:.3f} ({change:+.2f}%)")

            if "crypto" in global_data:
                crypto = global_data["crypto"]
                if "BTC" in crypto:
                    btc = crypto["BTC"]
                    price = btc.get("price", 0)
                    change = btc.get("change_pct", 0)
                    lines.append(f"BTC：${price:,.0f} ({change:+.2f}%)")
                if "ETH" in crypto:
                    eth = crypto["ETH"]
                    price = eth.get("price", 0)
                    change = eth.get("change_pct", 0)
                    lines.append(f"ETH：${price:,.0f} ({change:+.2f}%)")

            if "metals" in global_data:
                metals = global_data["metals"]
                if "gold" in metals:
                    gold = metals["gold"]
                    price = gold.get("price", 0)
                    change = gold.get("change_pct", 0)
                    sign = "+" if change >= 0 else ""
                    lines.append(f"COMEX黄金：${price:,.2f}/盎司 ({sign}{change:.2f}%)")
                if "silver" in metals:
                    silver = metals["silver"]
                    price = silver.get("price", 0)
                    change = silver.get("change_pct", 0)
                    sign = "+" if change >= 0 else ""
                    lines.append(f"COMEX白银：${price:.2f}/盎司 ({sign}{change:.2f}%)")
                if "gold_silver_ratio" in metals:
                    ratio = metals["gold_silver_ratio"]
                    lines.append(f"金银比：{ratio:.2f}")

        return "\n".join(lines)

    @staticmethod
    def format_us_stock_report(data: Dict) -> str:
        """
        格式化美股市场日报

        Args:
            data: 包含所有数据的字典

        Returns:
            格式化后的消息
        """
        lines = [
            "=" * 30,
            f"美股市场日报 - {datetime.now().strftime('%Y-%m-%d')}",
            "=" * 30,
            "",
        ]

        # 主要指数
        if "indices" in data and data["indices"]:
            lines.append("【主要指数】")
            for idx in data["indices"]:
                name = idx.get("name", "")
                price = idx.get("price", 0)
                change = idx.get("change", 0)
                sign = "+" if change >= 0 else ""
                lines.append(f"{name}：{price:.2f} ({sign}{change:.2f}%)")
            lines.append("")

        # 热门科技股
        if "tech_stocks" in data and data["tech_stocks"]:
            lines.append("【热门科技股】")
            for symbol, stock in data["tech_stocks"].items():
                name = stock.get("name", symbol)
                price = stock.get("price", 0)
                change = stock.get("change_pct", 0)
                lines.append(f"{symbol} {name}：${price:.2f} ({change:+.2f}%)")
            lines.append("")

        # 中概股
        if "chinese_stocks" in data and data["chinese_stocks"]:
            lines.append("【中概股】")
            for symbol, stock in data["chinese_stocks"].items():
                name = stock.get("name", symbol)
                price = stock.get("price", 0)
                change = stock.get("change_pct", 0)
                lines.append(f"{symbol} {name}：${price:.2f} ({change:+.2f}%)")
            lines.append("")

        # 全球市场（复用A股的逻辑）
        if "global" in data:
            global_data = data["global"]
            lines.append("【全球市场（最近12小时）】")

            if "rmb" in global_data:
                rmb = global_data["rmb"]
                rate = rmb.get("rate", 0)
                change = rmb.get("change_pct", 0)
                lines.append(f"离岸人民币：{rate:.3f} ({change:+.2f}%)")

            if "crypto" in global_data:
                crypto = global_data["crypto"]
                if "BTC" in crypto:
                    btc = crypto["BTC"]
                    price = btc.get("price", 0)
                    change = btc.get("change_pct", 0)
                    lines.append(f"BTC：${price:,.0f} ({change:+.2f}%)")
                if "ETH" in crypto:
                    eth = crypto["ETH"]
                    price = eth.get("price", 0)
                    change = eth.get("change_pct", 0)
                    lines.append(f"ETH：${price:,.0f} ({change:+.2f}%)")

            if "metals" in global_data:
                metals = global_data["metals"]
                if "gold" in metals:
                    gold = metals["gold"]
                    price = gold.get("price", 0)
                    change = gold.get("change_pct", 0)
                    sign = "+" if change >= 0 else ""
                    lines.append(f"COMEX黄金：${price:,.2f}/盎司 ({sign}{change:.2f}%)")
                if "silver" in metals:
                    silver = metals["silver"]
                    price = silver.get("price", 0)
                    change = silver.get("change_pct", 0)
                    sign = "+" if change >= 0 else ""
                    lines.append(f"COMEX白银：${price:.2f}/盎司 ({sign}{change:.2f}%)")
                if "gold_silver_ratio" in metals:
                    ratio = metals["gold_silver_ratio"]
                    lines.append(f"金银比：{ratio:.2f}")

        return "\n".join(lines)
