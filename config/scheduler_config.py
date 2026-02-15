# 定时任务配置

MONITOR_JOBS = [
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

CRAWLER_JOBS = [
    # 财经新闻爬取：每小时整点
    {
        "job_id": "crawler_news",
        "trigger": "cron",
        "minute": 0,
    },
    # 实时价格采集：每小时第5分钟
    {
        "job_id": "crawler_realtime",
        "trigger": "cron",
        "minute": 5,
    },
    # 历史数据补齐：每天凌晨3:00
    {
        "job_id": "crawler_catchup",
        "trigger": "cron",
        "hour": 3,
        "minute": 0,
    },
    # 美股前一交易日K线：每天早上6:00
    {
        "job_id": "crawler_daily_us",
        "trigger": "cron",
        "hour": 6,
        "minute": 0,
    },
    # IC/IM期货移仓信号：每天14:30
    {
        "job_id": "crawler_futures",
        "trigger": "cron",
        "hour": 14,
        "minute": 30,
    },
    # A股/港股今日K线：每天15:30
    {
        "job_id": "crawler_daily_cn_hk",
        "trigger": "cron",
        "hour": 15,
        "minute": 30,
    },
    # 加密货币/汇率今日K线：每天16:40
    {
        "job_id": "crawler_daily_crypto_fx",
        "trigger": "cron",
        "hour": 16,
        "minute": 40,
    },
    # 贵金属今日K线：每天16:50
    {
        "job_id": "crawler_daily_commodities",
        "trigger": "cron",
        "hour": 16,
        "minute": 50,
    },
]
