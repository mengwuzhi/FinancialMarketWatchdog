# 投资监控系统 (Investment Watchdog)

综合投资监控平台，提供LOF基金监控、市场日报和RSS文章分析功能。

## 功能特性

### 1. LOF实时监控（保留原功能）
- **涨停跌停监控**：实时监控指定LOF基金的涨停跌停
- **急涨急跌监控**：监控短时间内的快速涨跌
- **开板提醒**：涨停跌停后开板提醒
- **运行时间**：交易日 09:00-15:00 每分钟检查

### 2. LOF溢价率监控（新增）
- **执行时间**：每天下午14:30
- **监控对象**：所有非QDII LOF基金
- **提醒条件**：溢价或折价 > 10%
- **数据来源**：akshare fund_lof_spot_em()

### 3. A股市场日报（新增）
- **执行时间**：交易日晚上18:30
- **报告内容**：
  - 主要指数（上证、深证、创业板、科创50、沪深300、中证500等）表现
  - 市场概况（涨跌家数、涨停跌停数量）
  - 热点板块TOP5（行业+概念）
  - 主力资金净流入TOP3
  - 全球市场（离岸人民币、BTC/ETH、COMEX黄金白银及金银比）

### 4. 美股市场日报（新增）
- **执行时间**：每天早上08:00
- **报告内容**：
  - 主要指数（道琼斯、纳斯达克、标普500）
  - 热门科技股（苹果、微软、英伟达等）
  - 中概股表现（阿里、拼多多、京东等）
  - VIX恐慌指数
  - 全球市场（汇率、数字货币、贵金属）

### 5. RSS文章监控与AI分析（新增）
- **执行时间**：每晚22:00-23:55 每5分钟
- **监控RSS**：配置的RSS Feed
- **AI分析**：使用通义千问分析文章
- **提取信息**：
  - 对市场的整体观点
  - 投资建议和策略
  - 提到的个股和基金代码
  - 核心观点摘要

## 快速开始

### 1. 配置文件

编辑 `data/config.json`：

```json
{
  "dingtalk": {
    "webhook": "你的钉钉机器人webhook",
    "secret": "你的钉钉机器人secret"
  },
  "lof": {
    "limit_pct": 9.9,
    "speed_window_minutes": 10.0,
    "speed_threshold_pct": 2.0,
    "premium_threshold_pct": 10.0,
    "limit_codes_file": "lof_limit_codes.txt",
    "speed_codes_file": "lof_speed_codes.txt"
  },
  "ai": {
    "provider": "qwen",
    "api_key": "你的通义千问API Key",
    "api_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen-turbo",
    "enable_search": false
  },
  "rss": {
    "feed_url": "你的RSS Feed URL",
    "check_interval_minutes": 5
  },
  "timezone": "Asia/Shanghai"
}
```

### 2. LOF代码配置

编辑 `data/lof_limit_codes.txt` 和 `data/lof_speed_codes.txt`：

```
161226
161225
# 一行一个代码，支持注释
```

### 3. 使用Docker Compose运行（推荐）

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

### 4. 直接运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 项目结构

```
lof_watchdog/
├── main.py                      # 主程序入口
├── config/
│   ├── settings.py              # 配置管理
│   ├── scheduler_config.py      # 定时任务配置
│   └── us_stocks_config.py      # 美股代码配置
├── core/
│   ├── scheduler.py             # 任务调度器
│   └── trading_calendar.py      # 交易日判断
├── monitors/
│   ├── lof_monitor.py           # LOF实时监控
│   ├── lof_premium_monitor.py   # LOF溢价率监控
│   ├── a_share_monitor.py       # A股日报
│   └── us_stock_monitor.py      # 美股日报
├── analyzers/
│   ├── rss_fetcher.py           # RSS文章获取
│   └── ai_analyzer.py           # AI分析引擎
├── data_sources/
│   ├── akshare_provider.py      # AKShare数据封装
│   ├── external_data.py         # 外部数据（汇率等）
│   └── us_stock_eastmoney.py    # 美股东方财富数据源
├── notifiers/
│   └── dingtalk.py              # 钉钉通知
├── utils/
│   ├── data_parser.py           # 数据解析工具
│   ├── formatters.py            # 消息格式化
│   └── retry_helper.py          # 重试机制辅助工具
├── storage/
│   └── state_manager.py         # 状态管理
└── data/                        # 数据目录（Volume挂载）
    ├── config.json              # 配置文件
    ├── lof_limit_codes.txt      # 涨跌停监控代码
    ├── lof_speed_codes.txt      # 急涨急跌监控代码
    ├── state.json               # 状态文件
    └── rss_history.json         # RSS历史记录
```

## 定时任务说明

| 任务 | 时间 | 交易日限制 | 说明 |
|------|------|-----------|------|
| LOF实时监控 | 周一至五 09:00-15:00 每分钟 | 是 | A股交易日 |
| LOF溢价率检查 | 周一至五 14:30 | 是 | A股交易日 |
| A股市场日报 | 周一至五 18:30 | 是 | A股交易日 |
| 美股市场日报 | 周二至六 08:00 | 否 | 美股时差+1天 |
| RSS文章监控 | 每天 22:00-23:55 每5分钟 | 否 | 发现新文章即分析 |

## 通义千问API配置

1. 访问[阿里云控制台](https://dashscope.console.aliyun.com/)
2. 创建API Key
3. 将API Key填入 `data/config.json` 的 `ai.api_key` 字段
4. **enable_search配置**：
   - `true`：启用网络搜索增强分析（费用较高，分析更深入）
   - `false`：仅基于文章内容分析（费用较低，推荐）

## 注意事项

1. **钉钉机器人配置**：需要创建自定义机器人并获取webhook和secret
2. **交易日判断**：
   - A股：系统会自动判断A股交易日，非交易日不执行相关任务
   - 美股：支持美股节假日判断（新年、独立日、感恩节、圣诞节等9个主要节假日）
3. **API限流**：注意各数据源的API调用频率限制
4. **AI费用**：使用AI分析会产生API调用费用，建议选择经济型模型
5. **数据准确性**：市场数据仅供参考，投资决策请谨慎

## 依赖库

- akshare>=1.18.0 - A股数据获取（主要数据源，包含美股数据）
- pandas>=2.0.0 - 数据处理
- requests>=2.31.0 - HTTP请求
- apscheduler>=3.10.0 - 定时任务调度
- feedparser>=6.0.0 - RSS解析
- openai>=1.0.0 - AI API调用（通义千问兼容）
- yfinance>=0.2.0 - 美股数据获取（备用数据源）
- python-dateutil>=2.8.0 - 日期处理
- pytz>=2023.3 - 时区处理

## 故障排查

### 1. LOF监控无数据
- 检查是否为交易时间
- 检查代码文件是否正确配置
- 检查akshare是否正常工作

### 2. 钉钉通知未收到
- 检查webhook和secret是否正确
- 检查钉钉机器人是否被禁用
- 查看日志是否有错误信息

### 3. AI分析失败
- 检查API Key是否正确
- 检查网络是否能访问API
- 检查API余额是否充足

### 4. Docker容器无法启动
- 检查data目录是否存在
- 检查配置文件是否正确
- 查看容器日志：`docker-compose logs`

## 技术支持

如有问题，请检查日志输出或提Issue。

## 许可证

MIT License
