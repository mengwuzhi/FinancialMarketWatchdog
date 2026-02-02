"""
测试RSS最新文章分析

不依赖时间，直接获取RSS源的最新文章并进行AI分析
"""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import feedparser
from analyzers.ai_analyzer import AIAnalyzer
from config.settings import Settings


def format_analysis_result(analysis: dict, entry: dict):
    """格式化输出分析结果"""
    print("=" * 80)
    print("文章信息")
    print("=" * 80)
    print(f"标题: {entry.get('title', 'N/A')}")
    print(f"链接: {entry.get('link', 'N/A')}")
    print(f"发布时间: {entry.get('published', 'N/A')}")
    print()

    print("=" * 80)
    print("AI分析结果")
    print("=" * 80)
    print()

    # 核心观点总结
    if analysis.get("core_summary"):
        print("【核心观点总结】")
        print(analysis["core_summary"])
        print()

    # 市场观点
    print(f"【市场观点】{analysis.get('market_view', '未知')}")
    print()

    # 相关项目
    related_items = analysis.get("related_items", {})

    # 股票
    stocks = related_items.get("stocks", [])
    if stocks:
        print("【相关股票】")
        for stock in stocks:
            code = stock.get("code", "")
            name = stock.get("name", "")
            reason = stock.get("reason", "")
            print(f"  • {code} {name}")
            if reason:
                print(f"    原因: {reason}")
        print()

    # 行业
    industries = related_items.get("industries", [])
    if industries:
        print("【相关行业】")
        for industry in industries:
            name = industry.get("name", "")
            reason = industry.get("reason", "")
            print(f"  • {name}")
            if reason:
                print(f"    原因: {reason}")
        print()

    # 投资主题
    themes = related_items.get("investment_themes", [])
    if themes:
        print("【投资主题】")
        for theme in themes:
            name = theme.get("name", "")
            reason = theme.get("reason", "")
            print(f"  • {name}")
            if reason:
                print(f"    传导逻辑: {reason}")
        print()

    # 基金
    funds = related_items.get("funds", [])
    if funds:
        print("【相关基金】")
        for fund in funds:
            code = fund.get("code", "")
            name = fund.get("name", "")
            reason = fund.get("reason", "")
            print(f"  • {code} {name}")
            if reason:
                print(f"    原因: {reason}")
        print()

    # 潜在影响
    impact = analysis.get("potential_impact", {})
    positive = impact.get("positive", [])
    negative = impact.get("negative", [])
    neutral = impact.get("neutral", [])

    if positive or negative or neutral:
        print("【潜在影响分析】")

        if positive:
            print("  正面影响:")
            for item in positive:
                print(f"    + {item}")

        if negative:
            print("  负面影响:")
            for item in negative:
                print(f"    - {item}")

        if neutral:
            print("  中性观察:")
            for item in neutral:
                print(f"    • {item}")
        print()

    # 投资启示
    insights = analysis.get("investment_insights", [])
    if insights:
        print("【投资启示】")
        for i, insight in enumerate(insights, 1):
            print(f"  {i}. {insight}")
        print()

    # 延伸分析（结合搜索）
    extended = analysis.get("extended_analysis", {})
    market_trends = extended.get("market_trends", [])

    if market_trends:
        print("=" * 80)
        print("延伸分析（结合网络搜索）")
        print("=" * 80)
        print()

        for trend in market_trends:
            item = trend.get("item", "")
            current_view = trend.get("current_view", "")
            latest_info = trend.get("latest_info", "")
            opportunity = trend.get("opportunity", "")
            risk = trend.get("risk", "")

            print(f"【{item}】")
            if current_view:
                print(f"  市场观点: {current_view}")
            if latest_info:
                print(f"  最新信息: {latest_info}")
            if opportunity:
                print(f"  投资机会: {opportunity}")
            if risk:
                print(f"  风险提示: {risk}")
            print()

        summary = extended.get("summary", "")
        if summary:
            print("【综合分析】")
            print(summary)
            print()


def extract_content(entry) -> str:
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

    return ""


def test_rss_latest_article():
    """测试RSS最新文章分析"""
    print("=" * 80)
    print("RSS最新文章AI分析测试")
    print("=" * 80)
    print()

    # 1. 加载配置
    config_file = os.path.join("data", "config.json")
    if not os.path.exists(config_file):
        print(f"[ERROR] 配置文件不存在: {config_file}")
        print("请先运行主程序生成配置文件，或手动创建配置文件")
        print()
        print("配置文件示例:")
        print(json.dumps({
            "ai": {
                "provider": "qwen",
                "api_key": "YOUR_API_KEY",
                "api_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model": "qwen-turbo"
            },
            "rss": {
                "feed_url": "https://example.com/rss"
            }
        }, ensure_ascii=False, indent=2))
        return

    settings = Settings(config_file)

    # 验证配置
    if not settings.rss_feed_url:
        print("[ERROR] RSS feed URL 未配置")
        print(f"请在 {config_file} 中配置 rss.feed_url")
        return

    if not settings.ai_api_key:
        print("[ERROR] AI API Key 未配置")
        print(f"请在 {config_file} 中配置 ai.api_key")
        return

    print(f"RSS源: {settings.rss_feed_url}")
    print(f"AI提供商: {settings.ai_provider}")
    print(f"AI模型: {settings.ai_model}")
    print()

    # 2. 获取RSS文章
    print("正在获取RSS文章...")
    try:
        feed = feedparser.parse(settings.rss_feed_url)
    except Exception as e:
        print(f"[ERROR] RSS解析失败: {e}")
        return

    if not feed.entries:
        print("[ERROR] RSS源中没有文章")
        return

    # 获取第一篇文章（最新）
    entry = feed.entries[0]
    print(f"找到最新文章: {entry.get('title', 'N/A')}")
    print()

    # 3. 提取内容
    content = extract_content(entry)
    if not content:
        print("[ERROR] 无法提取文章内容")
        return

    print(f"文章内容长度: {len(content)} 字符")
    print()

    # 4. AI分析
    print("正在进行AI分析...")
    print("(这可能需要几秒钟，请耐心等待...)")
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

    except Exception as e:
        print(f"[ERROR] AI分析失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. 输出结果
    print()
    format_analysis_result(analysis, entry)

    # 6. 输出原始JSON（可选）
    print("=" * 80)
    print("原始JSON结果")
    print("=" * 80)
    print(json.dumps(analysis, ensure_ascii=False, indent=2))
    print()


if __name__ == "__main__":
    test_rss_latest_article()

    print("=" * 80)
    print("测试完成")
    print("=" * 80)
