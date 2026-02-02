"""
手动触发RSS文章分析并发送到钉钉

不依赖定时任务，立即分析并发送今天的最新文章
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import Settings
from storage.state_manager import StateManager
from analyzers.ai_analyzer import AIAnalyzer
from analyzers.rss_fetcher import RSSFetcher
from notifiers.dingtalk import DingTalkNotifier


def main():
    """手动运行RSS检查和分析"""
    print("=" * 80)
    print("手动触发RSS文章分析")
    print("=" * 80)
    print()

    # 加载配置
    config_file = os.path.join("data", "config.json")
    settings = Settings(config_file)

    # 初始化状态管理器
    state_file = os.path.join("data", "state.json")
    state_manager = StateManager(state_file)

    # 初始化钉钉通知器
    notifier = DingTalkNotifier(
        webhook=settings.ding_webhook,
        secret=settings.ding_secret
    )

    # 初始化AI分析器
    ai_analyzer = AIAnalyzer(
        provider=settings.ai_provider,
        api_key=settings.ai_api_key,
        api_base_url=settings.ai_api_base_url,
        model=settings.ai_model,
        enable_search=settings.ai_enable_search,
    )

    # 初始化RSS监控器
    rss_fetcher = RSSFetcher(
        feed_url=settings.rss_feed_url,
        state_manager=state_manager,
        ai_analyzer=ai_analyzer,
        notifier=notifier,
    )

    # 执行检查和分析
    print(f"RSS源: {settings.rss_feed_url}")
    print(f"AI模型: {settings.ai_model} (搜索: {'启用' if settings.ai_enable_search else '禁用'})")
    print()

    rss_fetcher.check_and_analyze()

    print()
    print("=" * 80)
    print("完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
