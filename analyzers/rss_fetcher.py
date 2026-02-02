import hashlib
import email.utils
from datetime import datetime
from typing import Dict, Optional

import feedparser

from analyzers.ai_analyzer import AIAnalyzer
from notifiers.dingtalk import DingTalkNotifier
from storage.state_manager import StateManager


class RSSFetcher:
    """RSS文章监控器"""

    def __init__(
        self,
        feed_url: str,
        state_manager: StateManager,
        ai_analyzer: AIAnalyzer,
        notifier: DingTalkNotifier,
    ):
        self.feed_url = feed_url
        self.state_manager = state_manager
        self.ai_analyzer = ai_analyzer
        self.notifier = notifier

        # 初始化历史记录
        self.state_manager.ensure_key("rss_history", {})

    def check_and_analyze(self):
        """检查新文章并分析"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] RSS Check")

        try:
            # 解析RSS Feed（添加超时）
            import socket
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(30)  # 30秒超时

            try:
                feed = feedparser.parse(self.feed_url)
            finally:
                socket.setdefaulttimeout(old_timeout)

            if not feed.entries:
                print("No entries in RSS feed")
                return

            # 仅处理当天文章
            today = datetime.now().date()
            today_entries = [
                entry for entry in feed.entries if self._is_entry_today(entry, today)
            ]
            if not today_entries:
                print("No articles for today")
                return

            # 遍历文章
            history = self.state_manager.get("rss_history", {})
            new_articles_found = False
            processed_count = 0
            max_articles_per_run = 1  # 单次只处理1篇文章，多篇文章会在后续运行中逐个处理

            for entry in today_entries:
                # 限制处理数量，避免任务时间过长
                if processed_count >= max_articles_per_run:
                    print(f"Reached max articles limit ({max_articles_per_run}), will process remaining in next run")
                    break

                article_id = self._generate_article_id(entry)

                # 检查是否已处理
                if article_id in history:
                    continue

                # 发现新文章
                new_articles_found = True
                print(f"Found new article: {entry.get('title', 'N/A')}")

                # 提取内容
                content = self._extract_content(entry)
                if not content:
                    print("Failed to extract content")
                    # 标记为已处理（避免重复尝试）
                    history[article_id] = {
                        "processed_at": datetime.now().isoformat(),
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "status": "no_content"
                    }
                    self.state_manager.set("rss_history", history)
                    continue

                # AI分析
                try:
                    analysis = self.ai_analyzer.analyze(content)

                    # 发送通知
                    self._send_notification(entry, analysis)

                    # 标记为已处理
                    history[article_id] = {
                        "processed_at": datetime.now().isoformat(),
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "status": "analyzed"
                    }
                    self.state_manager.set("rss_history", history)
                    processed_count += 1

                except Exception as e:
                    print(f"Analysis failed: {e}")
                    # 标记为失败，避免无限重试
                    history[article_id] = {
                        "processed_at": datetime.now().isoformat(),
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "status": "failed",
                        "error": str(e)
                    }
                    self.state_manager.set("rss_history", history)

            if not new_articles_found:
                print("No new articles found")
            else:
                print(f"Processed {processed_count} articles in this run")

        except Exception as e:
            print(f"[ERROR] RSS check failed: {e}")
            # 不要raise，让任务正常结束
            import traceback
            traceback.print_exc()

    def _generate_article_id(self, entry) -> str:
        """生成文章唯一ID"""
        if entry.get("id"):
            return entry["id"]

        # 使用link和title生成hash
        content = f"{entry.get('link', '')}{entry.get('title', '')}"
        return hashlib.md5(content.encode()).hexdigest()

    def _is_entry_today(self, entry, today) -> bool:
        """判断文章日期是否为当天"""
        entry_date = self._get_entry_date(entry)
        return entry_date == today if entry_date else False

    def _get_entry_date(self, entry) -> Optional[datetime.date]:
        """解析文章发布日期"""
        time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if time_struct:
            try:
                timestamp = feedparser.mktime_tz(time_struct)
                return datetime.fromtimestamp(timestamp).date()
            except Exception:
                try:
                    return datetime(*time_struct[:6]).date()
                except Exception:
                    return None

        date_str = entry.get("published") or entry.get("updated")
        if date_str:
            try:
                dt = email.utils.parsedate_to_datetime(date_str)
                if dt.tzinfo:
                    dt = dt.astimezone()
                return dt.date()
            except Exception:
                return None

        return None

    def _extract_content(self, entry) -> Optional[str]:
        """提取文章内容"""
        # 优先使用content
        if "content" in entry and entry.content:
            return entry.content[0].value

        # 其次使用summary
        if "summary" in entry:
            return entry.summary

        # 最后使用description
        if "description" in entry:
            return entry.description

        return None

    def _send_notification(self, entry, analysis: Dict):
        """发送分析结果通知"""
        lines = [
            "📰 RSS文章投资分析",
            "",
            f"**标题**: {entry.get('title', 'N/A')}",
            f"**链接**: {entry.get('link', 'N/A')}",
            f"**发布时间**: {entry.get('published', 'N/A')}",
            "",
            "---",
            "",
        ]

        # 核心观点
        if analysis.get("core_summary"):
            lines.append(f"**核心观点**: {analysis['core_summary']}")
            lines.append("")

        # 市场观点
        market_view = analysis.get("market_view", "未知")
        view_emoji = {"看多": "📈", "看空": "📉", "中性": "➡️"}.get(market_view, "❓")
        lines.append(f"**市场观点**: {view_emoji} {market_view}")
        lines.append("")

        # 相关股票
        related_items = analysis.get("related_items", {})
        stocks = related_items.get("stocks", [])
        if stocks:
            lines.append("**相关股票**:")
            for stock in stocks[:5]:  # 最多显示5只
                code = stock.get("code", "")
                name = stock.get("name", "")
                market = stock.get("market", "")
                lines.append(f"- {code} {name} ({market})")
            lines.append("")

        # 相关行业
        industries = related_items.get("industries", [])
        if industries:
            lines.append("**相关行业**:")
            for industry in industries[:3]:  # 最多显示3个
                name = industry.get("name", "")
                lines.append(f"- {name}")
            lines.append("")

        # 投资主题
        themes = related_items.get("investment_themes", [])
        if themes:
            lines.append("**投资主题**:")
            for theme in themes[:3]:  # 最多显示3个
                name = theme.get("name", "")
                lines.append(f"- {name}")
            lines.append("")

        # 相关基金
        funds = related_items.get("funds", [])
        if funds:
            lines.append("**相关基金**:")
            for fund in funds[:3]:  # 最多显示3个
                code = fund.get("code", "")
                name = fund.get("name", "")
                lines.append(f"- {code} {name}")
            lines.append("")

        # 延伸分析摘要
        extended = analysis.get("extended_analysis", {})
        if extended.get("summary"):
            lines.append("**市场分析**:")
            summary_text = extended["summary"]
            # 如果太长，截取前300字
            if len(summary_text) > 300:
                summary_text = summary_text[:300] + "..."
            lines.append(summary_text)
            lines.append("")

        # 投资启示
        insights = analysis.get("investment_insights", [])
        if insights:
            lines.append("**投资启示**:")
            for i, insight in enumerate(insights[:3], 1):  # 最多显示3条
                lines.append(f"{i}. {insight}")
            lines.append("")

        lines.append("---")
        lines.append("💡 *AI分析仅供参考，不构成投资建议*")

        message = "\n".join(lines)
        self.notifier.send_text(message)
