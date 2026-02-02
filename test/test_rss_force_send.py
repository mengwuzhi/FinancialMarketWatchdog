"""
强制分析并发送RSS最新文章（忽略日期和历史记录）

适用场景：
- 文章已经隔日，但想补发
- 需要重新分析已处理的文章
- 测试钉钉通知功能
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import feedparser
from config.settings import Settings
from analyzers.ai_analyzer import AIAnalyzer
from notifiers.dingtalk import DingTalkNotifier


def extract_content(entry):
    """提取文章内容"""
    if "content" in entry and entry.content:
        return entry.content[0].value
    if "summary" in entry:
        return entry.summary
    if "description" in entry:
        return entry.description
    return None


def format_notification(entry, analysis):
    """格式化钉钉通知消息"""
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
    stocks = analysis.get("related_items", {}).get("stocks", [])
    if stocks:
        lines.append("**相关股票**:")
        for stock in stocks[:5]:  # 最多显示5只
            code = stock.get("code", "")
            name = stock.get("name", "")
            market = stock.get("market", "")
            lines.append(f"- {code} {name} ({market})")
        lines.append("")

    # 投资主题
    themes = analysis.get("related_items", {}).get("investment_themes", [])
    if themes:
        lines.append("**投资主题**:")
        for theme in themes[:3]:  # 最多显示3个
            name = theme.get("name", "")
            lines.append(f"- {name}")
        lines.append("")

    # 延伸分析摘要
    extended = analysis.get("extended_analysis", {})
    if extended.get("summary"):
        lines.append("**市场分析**:")
        lines.append(extended["summary"][:200] + "...")  # 截取前200字
        lines.append("")

    # 投资启示
    insights = analysis.get("investment_insights", [])
    if insights:
        lines.append("**投资启示**:")
        for i, insight in enumerate(insights[:2], 1):  # 最多显示2条
            lines.append(f"{i}. {insight}")
        lines.append("")

    lines.append("---")
    lines.append("💡 *AI分析仅供参考，不构成投资建议*")

    return "\n".join(lines)


def main():
    """强制分析并发送最新文章"""
    print("=" * 80)
    print("强制分析并发送RSS最新文章")
    print("=" * 80)
    print()

    # 加载配置
    config_file = os.path.join("data", "config.json")
    settings = Settings(config_file)

    print(f"RSS源: {settings.rss_feed_url}")
    print(f"AI模型: {settings.ai_model} (搜索: {'启用' if settings.ai_enable_search else '禁用'})")
    print()

    # 获取RSS文章
    print("正在获取RSS文章...")
    try:
        feed = feedparser.parse(settings.rss_feed_url)
    except Exception as e:
        print(f"[ERROR] RSS解析失败: {e}")
        return

    if not feed.entries:
        print("[ERROR] RSS源中没有文章")
        return

    # 获取最新文章
    entry = feed.entries[0]
    print(f"找到最新文章: {entry.get('title', 'N/A')}")
    print(f"发布时间: {entry.get('published', 'N/A')}")
    print()

    # 提取内容
    content = extract_content(entry)
    if not content:
        print("[ERROR] 无法提取文章内容")
        return

    print(f"文章内容长度: {len(content)} 字符")
    print()

    # AI分析
    print("正在进行AI分析...")
    print("(这可能需要1-2分钟，请耐心等待...)")
    print()

    try:
        ai_analyzer = AIAnalyzer(
            provider=settings.ai_provider,
            api_key=settings.ai_api_key,
            api_base_url=settings.ai_api_base_url,
            model=settings.ai_model,
            enable_search=settings.ai_enable_search,
        )

        analysis = ai_analyzer.analyze(content)

        print("[SUCCESS] AI分析完成")
        print()

    except Exception as e:
        print(f"[ERROR] AI分析失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 发送钉钉通知
    print("正在发送钉钉通知...")

    try:
        notifier = DingTalkNotifier(
            webhook=settings.ding_webhook,
            secret=settings.ding_secret
        )

        message = format_notification(entry, analysis)
        notifier.send_text(message)

        print("[SUCCESS] 钉钉通知发送成功")
        print()

    except Exception as e:
        print(f"[ERROR] 钉钉通知发送失败: {e}")
        import traceback
        traceback.print_exc()
        return

    print("=" * 80)
    print("完成")
    print("=" * 80)
    print()
    print("提示:")
    print("- 此脚本不会更新 state.json")
    print("- 如需避免定时任务重复发送，请手动添加文章到 rss_history")


if __name__ == "__main__":
    main()
