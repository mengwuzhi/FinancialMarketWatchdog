# 定时任务配置

JOBS = [
    # LOF实时监控：交易日 09:00-15:00 每分钟执行
    {
        "job_id": "lof_realtime_monitor",
        "trigger": "cron",
        "day_of_week": "mon-fri",
        "hour": "9-15",
        "minute": "*/1",
        "trading_day_only": True,
    },
    # A股市场日报：交易日 18:30
    {
        "job_id": "a_share_daily_report",
        "trigger": "cron",
        "day_of_week": "mon-fri",
        "hour": 18,
        "minute": 30,
        "trading_day_only": True,
    },
    # 美股市场日报：周二至周六 08:00（对应美股周一至周五）
    {
        "job_id": "us_stock_daily_report",
        "trigger": "cron",
        "day_of_week": "tue-sat",
        "hour": 8,
        "minute": 0,
        "trading_day_only": False,
    },
    # RSS文章监控：每天 22:00-23:55 每5分钟
    {
        "job_id": "rss_article_monitor",
        "trigger": "cron",
        "hour": "22-23",
        "minute": "*/5",
        "trading_day_only": False,
    },
]
