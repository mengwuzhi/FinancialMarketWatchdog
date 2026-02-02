"""
美股股票代码配置

配置说明：
- 可以添加、删除或修改股票代码
- 支持多个分组，每个分组在日报中单独显示
- 修改后重启定时任务生效
"""

# 美股股票配置
US_STOCKS_CONFIG = {
    # 热门科技股
    "tech_stocks": [
        "AAPL",   # 苹果
        "MSFT",   # 微软
        "NVDA",   # 英伟达
        "TSLA",   # 特斯拉
        "GOOGL",  # 谷歌
        "AMZN",   # 亚马逊
        "META",   # Meta（Facebook）
        "NFLX",   # Netflix
        "INTC",   # 英特尔
        "AMD",    # 超威半导体
    ],

    # 中概股
    "chinese_stocks": [
        "BABA",   # 阿里巴巴
        "PDD",    # 拼多多
        "JD",     # 京东
        "BIDU",   # 百度
        "NTES",   # 网易
        "NIO",    # 蔚来
    ],
}

# 分组显示名称（用于日报中的标题）
GROUP_DISPLAY_NAMES = {
    "tech_stocks": "热门科技股",
    "chinese_stocks": "中概股",
}


def get_us_stocks_config():
    """获取美股配置"""
    return US_STOCKS_CONFIG


def get_all_symbols():
    """获取所有股票代码（扁平列表）"""
    all_symbols = []
    for symbols in US_STOCKS_CONFIG.values():
        all_symbols.extend(symbols)
    return all_symbols


def get_group_name(group_key):
    """获取分组显示名称"""
    return GROUP_DISPLAY_NAMES.get(group_key, group_key)
