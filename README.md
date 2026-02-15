# FinancialMarketWatchdog

投资监控与数据采集 Web 服务 - 提供市场监控、数据爬取、RSS分析等功能的FastAPI应用。

## 功能特性

### 1. 市场监控

- **A股市场日报**
  - 执行时间：交易日 18:30
  - 主要指数表现（上证、深证、创业板、科创50、沪深300、中证500等）
  - 市场概况（涨跌家数、涨停跌停数量）
  - 热点板块TOP5（行业+概念）
  - 主力资金净流入TOP3
  - 全球市场（离岸人民币、BTC/ETH、COMEX黄金白银）

- **美股市场日报**
  - 执行时间：周二至周六 08:00
  - 主要指数（道琼斯、纳斯达克、标普500）
  - 热门科技股（苹果、微软、英伟达等）
  - 中概股表现（阿里、拼多多、京东等）
  - 全球市场（汇率、数字货币、贵金属）

### 2. 数据爬取 (data_crawler)

- **财经新闻爬取**：每小时整点，多来源新闻（新浪、金融界、网易、路透）
- **实时价格采集**：每小时第5分钟，记录加密货币、外汇、贵金属价格快照
- **股票指数K线**：全球11个主要指数日K线（A股、港股、美股）
- **加密货币/外汇K线**：BTC/ETH/BNB + 美元兑离岸人民币
- **贵金属K线**：黄金、白银期货价格
- **IC/IM期货移仓信号**：每天14:30检测中证500/1000股指期货滚动信号
- **历史数据补齐**：每天凌晨3:00自动补齐缺失数据

### 3. RSS文章监控与AI分析

- **执行时间**：每晚 22:00-23:55 每5分钟
- **AI分析**：使用通义千问（Qwen）分析文章内容
- **提取信息**：
  - 市场整体观点（看多/看空/中性）
  - 相关股票、行业、基金、投资主题
  - 核心观点摘要
  - 投资启示

## 快速开始

### 1. 环境配置

复制配置模板并填写实际配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库配置
DB_HOST=47.95.221.184
DB_PORT=18453
DB_USER=root
DB_PASSWORD=YOUR_PASSWORD
DB_NAME=watchdog_db

# 钉钉通知
DING_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
DING_SECRET=YOUR_SECRET

# AI配置（通义千问）
AI_API_KEY=YOUR_DASHSCOPE_API_KEY
AI_MODEL=qwen-plus
AI_ENABLE_SEARCH=true

# RSS Feed
RSS_FEED_URL=https://example.com/rss

# API配置
API_HOST=0.0.0.0
API_PORT=8000
```

### 2. 使用Docker Compose运行（推荐）

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f watchdog

# 停止服务
docker-compose down
```

服务启动后访问：
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/system/health

### 3. 本地开发运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API接口说明

### 系统管理 (`/api/system`)

- `GET /api/system/health` - 健康检查
- `GET /api/system/jobs` - 查看所有定时任务
- `POST /api/system/jobs/trigger` - 手动触发任务
- `POST /api/system/jobs/{job_id}/pause` - 暂停任务
- `POST /api/system/jobs/{job_id}/resume` - 恢复任务

### 市场监控 (`/api/market`)

- `GET /api/market/a-share` - 获取A股市场数据（JSON）
- `POST /api/market/a-share/report` - 触发A股日报（发送钉钉通知）
- `GET /api/market/us-stock` - 获取美股市场数据（JSON）
- `POST /api/market/us-stock/report` - 触发美股日报（发送钉钉通知）

### 数据爬取 (`/api/crawler`)

- `POST /api/crawler/news` - 触发新闻爬取
- `POST /api/crawler/index` - 触发指数K线爬取（今日）
- `POST /api/crawler/crypto-fx` - 触发加密货币/外汇爬取（今日）
- `POST /api/crawler/commodity` - 触发贵金属爬取（今日）
- `POST /api/crawler/futures` - 触发期货移仓信号检测
- `POST /api/crawler/realtime` - 触发实时价格快照
- `POST /api/crawler/index/catchup` - 触发历史数据补齐
- `GET /api/crawler/news/query?limit=20` - 查询最新新闻

### RSS分析 (`/api/analysis`)

- `POST /api/analysis/rss/check` - 触发RSS检查和AI分析
- `POST /api/analysis/article` - 分析指定文章内容
  ```json
  {
    "content": "文章内容..."
  }
  ```

## 项目结构

```
FinancialMarketWatchdog_src/
├── app/                          # FastAPI应用
│   ├── main.py                   # 应用入口
│   ├── config.py                 # 统一配置（Pydantic BaseSettings）
│   ├── dependencies.py           # 依赖注入
│   ├── scheduler.py              # 后台定时任务调度器
│   └── routers/                  # API路由
│       ├── system.py             # 系统管理API
│       ├── market.py             # 市场监控API
│       ├── crawler.py            # 数据爬取API
│       └── analysis.py           # RSS分析API
├── data_crawler/                 # 数据爬取模块
│   ├── config/
│   │   └── settings.py           # 爬虫配置（代理自app.config）
│   ├── crawlers/
│   │   ├── news_crawler.py       # 财经新闻爬虫
│   │   ├── index_crawler.py      # 指数K线爬虫
│   │   ├── crypto_fx_crawler.py  # 加密货币/外汇爬虫
│   │   ├── commodity_crawler.py  # 贵金属爬虫
│   │   ├── futures_crawler.py    # 期货移仓信号
│   │   └── realtime_crawler.py   # 实时价格快照
│   ├── db/
│   │   ├── connection.py         # MySQL连接管理
│   │   └── init_tables.py        # 数据库表初始化
│   └── scripts/                  # 独立脚本
│       ├── fetch_indices.py      # 抓取指数历史数据
│       ├── fetch_crypto_fx.py    # 抓取加密/汇率历史
│       ├── fetch_commodities.py  # 抓取贵金属历史
│       └── fetch_daily_close.py  # 抓取今日收盘数据
├── monitors/                     # 市场监控器
│   ├── a_share_monitor.py        # A股日报生成器
│   └── us_stock_monitor.py       # 美股日报生成器
├── analyzers/                    # 分析器
│   ├── rss_fetcher.py            # RSS文章获取
│   └── ai_analyzer.py            # AI分析引擎（通义千问）
├── data_sources/                 # 数据源
│   ├── akshare_provider.py       # AKShare数据封装
│   ├── external_data.py          # 外部数据（汇率、加密货币等）
│   └── us_stock_eastmoney.py     # 美股东方财富数据源
├── notifiers/
│   └── dingtalk.py               # 钉钉通知
├── utils/
│   ├── data_parser.py            # 数据解析工具
│   ├── formatters.py             # 消息格式化
│   └── retry_helper.py           # 重试机制
├── storage/
│   └── state_manager.py          # 状态管理（JSON持久化）
├── core/
│   └── trading_calendar.py       # 交易日判断
├── config/
│   ├── scheduler_config.py       # 定时任务配置
│   └── us_stocks_config.py       # 美股代码配置
├── .env.example                  # 环境变量模板
├── requirements.txt              # Python依赖
├── Dockerfile                    # Docker镜像构建
├── docker-compose.yml            # Docker Compose配置
└── README.md                     # 本文件
```

## 定时任务说明

### 监控任务

| 任务ID | 时间 | 交易日限制 | 说明 |
|--------|------|-----------|------|
| a_share_daily_report | 周一至五 18:30 | 是 | A股市场日报 |
| us_stock_daily_report | 周二至六 08:00 | 否 | 美股市场日报 |
| rss_article_monitor | 每天 22:00-23:55 每5分钟 | 否 | RSS文章监控与AI分析 |

### 爬虫任务

| 任务ID | 时间 | 说明 |
|--------|------|------|
| crawler_news | 每小时整点 | 财经新闻爬取 |
| crawler_realtime | 每小时第5分钟 | 实时价格快照 |
| crawler_catchup | 每天凌晨3:00 | 历史数据补齐 |
| crawler_daily_us | 每天早上6:00 | 美股前日K线 |
| crawler_futures | 每天14:30 | IC/IM期货移仓信号 |
| crawler_daily_cn_hk | 每天15:30 | A股/港股今日K线 |
| crawler_daily_crypto_fx | 每天16:40 | 加密货币/汇率今日K线 |
| crawler_daily_commodities | 每天16:50 | 贵金属今日K线 |

## 数据库表结构

系统使用MySQL数据库存储爬取的数据，共6张表：

1. **news** - 财经新闻
2. **index_daily_kline** - 股票指数日K线
3. **crypto_fx_daily_kline** - 加密货币和汇率日K线
4. **commodity_daily_kline** - 贵金属日K线
5. **futures_rollover** - IC/IM期货移仓信号
6. **realtime_prices** - 实时价格（每小时快照）

服务启动时会自动创建所有表（如果不存在）。

## 技术栈

- **Web框架**: FastAPI + Uvicorn
- **任务调度**: APScheduler (BackgroundScheduler)
- **数据库**: MySQL (PyMySQL)
- **数据源**:
  - AKShare - A股数据
  - yfinance - 全球指数和贵金属
  - ccxt - 加密货币
  - CoinGecko API - 实时加密货币价格
  - 网页爬取 - 新闻、期货数据
- **AI分析**: 通义千问 (Qwen) via OpenAI SDK
- **配置管理**: Pydantic Settings + python-dotenv
- **通知**: 钉钉机器人

## 依赖库

```txt
# Web框架
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0

# 调度器
apscheduler>=3.10.0,<4.0.0

# 数据源
akshare>=1.18.0
yfinance>=0.2.0
ccxt>=4.0.0

# 数据库
pymysql>=1.1.0

# 数据处理
pandas>=2.0.0
python-dateutil>=2.8.0
pytz>=2023.3

# 网络/解析
requests>=2.31.0
feedparser>=6.0.0
beautifulsoup4>=4.12.0
lxml>=5.0.0

# AI
openai>=1.0.0
```

## 注意事项

1. **钉钉机器人配置**：需要创建自定义机器人并获取webhook和secret
2. **数据库配置**：确保MySQL数据库可访问，服务会自动创建表
3. **交易日判断**：
   - A股：自动判断A股交易日（节假日不执行）
   - 美股：支持美股节假日判断
4. **API限流**：注意各数据源的调用频率限制
5. **AI费用**：通义千问API会产生费用，建议选择经济型模型
6. **数据准确性**：市场数据仅供参考，投资决策请谨慎
7. **时区设置**：系统默认使用 Asia/Shanghai 时区

## 故障排查

### 1. 服务无法启动
- 检查`.env`文件是否正确配置
- 检查数据库连接是否正常
- 查看日志：`docker-compose logs -f`

### 2. 钉钉通知未收到
- 检查webhook和secret是否正确
- 检查钉钉机器人是否被禁用
- 查看API响应日志

### 3. 数据爬取失败
- 检查网络连接
- 检查数据源API是否可访问
- 查看爬虫日志输出

### 4. AI分析失败
- 检查AI_API_KEY是否正确
- 检查通义千问API余额
- 检查网络是否能访问API

### 5. 定时任务未执行
- 访问`/api/system/jobs`查看任务状态
- 检查任务是否被暂停
- 查看scheduler日志

## 开发与贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
