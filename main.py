import os
import sys

from analyzers.ai_analyzer import AIAnalyzer
from analyzers.rss_fetcher import RSSFetcher
from config.scheduler_config import JOBS
from config.settings import Settings, parse_codes_from_file
from core.scheduler import TaskScheduler, setup_logging
from monitors.a_share_monitor import AShareDailyReporter
from monitors.lof_monitor import LOFRealtimeMonitor
from monitors.us_stock_monitor import USStockDailyReporter
from notifiers.dingtalk import DingTalkNotifier
from storage.state_manager import StateManager


def main():
    """主程序入口"""
    # 设置日志
    setup_logging()

    # 加载配置
    config_file = os.path.join("data", "config.json")
    if not os.path.exists(config_file):
        print(f"[ERROR] Config file not found: {config_file}")
        print("Creating default config file...")
        settings = Settings(config_file)
        settings.save_default_config()
        print(f"Please edit {config_file} and restart")
        return 1

    settings = Settings(config_file)

    # 初始化通知器
    notifier = DingTalkNotifier(settings.ding_webhook, settings.ding_secret)

    # 初始化状态管理器
    state_file = os.path.join("data", "state.json")
    state_manager = StateManager(state_file)

    # 初始化调度器
    scheduler = TaskScheduler(timezone=settings.timezone)
    scheduler.set_notifier(notifier)

    # 加载LOF代码列表
    limit_codes_file = os.path.join("data", settings.lof_limit_codes_file)
    speed_codes_file = os.path.join("data", settings.lof_speed_codes_file)
    limit_codes = parse_codes_from_file(limit_codes_file)
    speed_codes = parse_codes_from_file(speed_codes_file)

    # 初始化LOF监控器
    lof_monitor = LOFRealtimeMonitor(
        notifier=notifier,
        state_manager=state_manager,
        limit_codes=limit_codes,
        speed_codes=speed_codes,
        limit_pct=settings.lof_limit_pct,
        speed_window_minutes=settings.lof_speed_window_minutes,
        speed_threshold_pct=settings.lof_speed_threshold_pct,
    )

    # 初始化A股日报监控器
    a_share_reporter = AShareDailyReporter(notifier=notifier)

    # 初始化美股日报监控器
    us_stock_reporter = USStockDailyReporter(notifier=notifier)

    # 初始化RSS监控器（如果配置了）
    rss_fetcher = None
    if settings.rss_feed_url and settings.ai_api_key:
        ai_analyzer = AIAnalyzer(
            provider=settings.ai_provider,
            api_key=settings.ai_api_key,
            api_base_url=settings.ai_api_base_url,
            model=settings.ai_model,
            enable_search=settings.ai_enable_search,
        )
        rss_fetcher = RSSFetcher(
            feed_url=settings.rss_feed_url,
            state_manager=state_manager,
            ai_analyzer=ai_analyzer,
            notifier=notifier,
        )
    else:
        print("[WARN] RSS monitoring disabled: missing feed_url or ai_api_key")

    # 任务函数映射
    job_functions = {
        "lof_realtime_monitor": lof_monitor.run_monitor,
        "a_share_daily_report": a_share_reporter.generate_report,
        "us_stock_daily_report": us_stock_reporter.generate_report,
        "rss_article_monitor": (
            rss_fetcher.check_and_analyze if rss_fetcher else lambda: None
        ),
    }

    # 注册所有任务
    for job_config in JOBS:
        job_id = job_config["job_id"]
        func = job_functions.get(job_id)

        if func is None:
            print(f"[WARN] Unknown job: {job_id}")
            continue

        # 提取参数
        trigger = job_config.pop("trigger")
        trading_day_only = job_config.pop("trading_day_only", False)

        # 添加任务
        scheduler.add_job(func=func, trigger=trigger, trading_day_only=trading_day_only, **job_config)

    print("=" * 50)
    print("Investment Watchdog System Started")
    print("=" * 50)
    print(f"Config: {config_file}")
    print(f"Timezone: {settings.timezone}")
    print(f"LOF Limit Codes: {len(limit_codes)}")
    print(f"LOF Speed Codes: {len(speed_codes)}")
    print(f"RSS Monitoring: {'Enabled' if rss_fetcher else 'Disabled'}")
    print(f"Registered Jobs: {len(JOBS)}")
    print("=" * 50)

    # 启动调度器
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        scheduler.shutdown()
        return 0


if __name__ == "__main__":
    sys.exit(main())
