from datetime import datetime, timedelta
from typing import Optional

from notifiers.dingtalk import DingTalkNotifier
from data_sources.akshare_provider import AKShareProvider
from data_sources.external_data import ExternalDataProvider
from utils.formatters import MessageFormatter


class AShareDailyReporter:
    """A股市场日报生成器"""

    def __init__(self, notifier: Optional[DingTalkNotifier] = None):
        self.notifier = notifier
        self.data_provider = AKShareProvider()
        self.external_provider = ExternalDataProvider()
        self.formatter = MessageFormatter()

    def collect_data(self) -> dict:
        """收集A股市场数据（供API返回JSON）"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] A-Share Data Collection")

        data = {}
        data["indices"] = self._get_indices()
        data["market"] = self._get_market_summary()
        data["sectors"] = self._get_hot_sectors()
        data["funds"] = self._get_fund_flow()
        data["global"] = self._get_global_data()
        return data

    def generate_report(self):
        """生成A股市场日报并发送通知（供定时任务调用）"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] A-Share Daily Report")

        try:
            data = self.collect_data()

            # 格式化并发送消息
            message = self.formatter.format_a_share_report(data)
            if self.notifier:
                self.notifier.send_text(message)
            print("A-Share daily report sent")

        except Exception as e:
            print(f"[ERROR] Failed to generate A-share report: {e}")
            raise

    def _get_indices(self) -> list:
        """获取主要指数"""
        import akshare as ak

        result = []

        # 定义需要获取的指数，按重要性和关注度排序
        indices_config = [
            ("000001", "上证指数"),    # 上海证券交易所主要指数
            ("399001", "深证成指"),    # 深圳证券交易所主要指数
            ("399006", "创业板指"),    # 创业板市场指数
            ("000300", "沪深300"),     # 沪深两市大盘股指数
            ("000905", "中证500"),     # 中盘股指数
            ("000688", "科创50"),      # 科创板指数
            ("000016", "上证50"),      # 上证大盘蓝筹指数
            ("000852", "中证1000"),    # 小盘股指数
            ("899050", "北证50"),      # 北交所指数
            ("399005", "中小100"),    # 中小板指数（已停止编制）
        ]

        # 获取实时行情数据
        try:
            df = ak.stock_zh_index_spot_em()
            if df is not None and not df.empty:
                for code, name in indices_config:
                    row = df[df["代码"] == code]
                    if not row.empty:
                        latest_price = row["最新价"].values[0]
                        change_pct = row["涨跌幅"].values[0]
                        change_amount = row["涨跌额"].values[0] if "涨跌额" in row.columns else 0
                        result.append({
                            "name": name,
                            "price": latest_price,
                            "change_pct": change_pct,
                            "change_amount": change_amount,
                        })
                    else:
                        # 未找到的指数，尝试使用备选方法（index_zh_a_hist 获取当日数据）
                        print(f"[DEBUG] 指数 {code} {name} 未在主接口找到，尝试备选方法")
                        try:
                            # 使用 index_zh_a_hist 获取最近几天的数据（包括今天）
                            today = datetime.now().strftime("%Y%m%d")
                            start_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")

                            idx_df = ak.index_zh_a_hist(
                                symbol=code,
                                period="daily",
                                start_date=start_date,
                                end_date=today
                            )

                            if idx_df is not None and not idx_df.empty:
                                latest = idx_df.iloc[-1]
                                latest_date = latest["日期"]
                                close = float(latest["收盘"])

                                # 计算涨跌幅和涨跌额
                                if len(idx_df) > 1:
                                    prev = idx_df.iloc[-2]
                                    prev_close = float(prev["收盘"])
                                    change_amount = close - prev_close
                                    change_pct = (change_amount / prev_close * 100) if prev_close > 0 else 0
                                else:
                                    change_amount = 0
                                    change_pct = 0

                                result.append({
                                    "name": name,
                                    "price": close,
                                    "change_pct": change_pct,
                                    "change_amount": change_amount,
                                })
                                print(f"[DEBUG] 通过备选方法获取到 {code} {name}，数据日期: {latest_date}")
                        except Exception as e:
                            print(f"[DEBUG] 备选方法也失败: {e}")
        except Exception as e:
            print(f"[ERROR] 获取指数数据失败: {e}")

        return result

    def _get_market_summary(self) -> dict:
        """获取市场概况"""
        df = self.data_provider.get_a_share_stocks()
        if df is None or df.empty:
            return {}

        return {
            "up": len(df[df["涨跌幅"] > 0]),
            "down": len(df[df["涨跌幅"] < 0]),
            "limit_up": len(df[df["涨跌幅"] >= 9.9]),
            "limit_down": len(df[df["涨跌幅"] <= -9.9]),
        }

    def _get_hot_sectors(self) -> dict:
        """获取热点板块"""
        result = {}

        # 行业板块
        df_industry = self.data_provider.get_industry_boards()
        if df_industry is not None and not df_industry.empty:
            result["industry"] = df_industry.nlargest(5, "涨跌幅").to_dict("records")

        # 概念板块
        df_concept = self.data_provider.get_concept_boards()
        if df_concept is not None and not df_concept.empty:
            result["concept"] = df_concept.nlargest(5, "涨跌幅").to_dict("records")

        return result

    def _get_fund_flow(self) -> dict:
        """获取资金流向"""
        result = {}

        # 主力资金
        try:
            df_main = self.data_provider.get_main_fund_flow()
            print(f"[DEBUG] 主力资金获取结果: {df_main is not None}, 是否为空: {df_main.empty if df_main is not None else 'N/A'}")

            if df_main is not None and not df_main.empty:
                print(f"[DEBUG] 主力资金数据形状: {df_main.shape}")
                print(f"[DEBUG] 主力资金数据列名: {df_main.columns.tolist()}")
                print(f"[DEBUG] 主力资金前3行:")
                print(df_main.head(3))

                # 处理主力资金数据，确保有正确的列名
                main_fund_list = []
                for idx, row in df_main.head(10).iterrows():
                    # 尝试多个可能的列名
                    code = None
                    name = None
                    for code_col in ["代码", "股票代码", "symbol"]:
                        if code_col in df_main.columns:
                            code = row[code_col]
                            break

                    for name_col in ["名称", "股票名称", "name"]:
                        if name_col in df_main.columns:
                            name = row[name_col]
                            break

                    # 主力净流入可能的列名（优先匹配带"今日"前缀的）
                    net_inflow = 0
                    used_col = None
                    for col in ["今日主力净流入-净额", "主力净流入-净额", "主力净流入", "主力净额", "主力资金"]:
                        if col in df_main.columns:
                            try:
                                net_inflow = float(row[col])
                                used_col = col
                                break
                            except (ValueError, TypeError) as e:
                                # 值转换失败，尝试下一个列名
                                print(f"[DEBUG] 第{idx}行 列'{col}'转换失败: {row[col]} (类型: {type(row[col])})")
                                continue

                    if used_col is None:
                        print(f"[WARN] 第{idx}行未找到可用的主力资金列")

                    # 如果值很大，可能单位是元，需要转换为亿
                    if abs(net_inflow) > 1000000:
                        net_inflow = net_inflow / 100000000

                    if code and name:
                        main_fund_list.append({
                            "代码": str(code),
                            "名称": str(name),
                            "主力净流入": net_inflow,
                        })

                result["main_fund"] = main_fund_list
                print(f"[DEBUG] 成功处理 {len(main_fund_list)} 条主力资金数据")
            else:
                print("[WARN] 主力资金数据为空或获取失败")
        except Exception as e:
            print(f"[ERROR] 主力资金获取异常: {e}")
            import traceback
            traceback.print_exc()

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