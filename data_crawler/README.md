# Data Crawler Module

这是从 FinancialMarketWatchdog 项目集成的数据采集模块，提供完整的历史数据存储和分析能力。

## 功能特性

### 1. 数据采集能力

| 功能 | 频率 | 数据源 |
|------|------|--------|
| 财经新闻采集 | 每小时 :00 | 新浪/证券之家/网易/Reuters RSS |
| 实时价格采集 | 每小时 :05 | CoinGecko/Yahoo Finance |
| 历史数据补齐 | 每天 03:00 | yfinance + ccxt |
| 美股K线 | 每天 06:00 | yfinance |
| IC/IM期货移仓信号 | 每天 14:30 | AKShare + 新浪期货 |
| A股/港股K线 | 每天 15:30 | yfinance |
| 加密货币/汇率K线 | 每天 16:40 | ccxt |
| 贵金属K线 | 每天 16:50 | yfinance |

### 2. 数据库设计

#### MySQL表结构（6张表）

| 表名 | 用途 | 特点 |
|------|------|------|
| `news` | 财经新闻 | URL哈希去重 |
| `index_daily_kline` | 股指日K线 | OHLC + 涨跌幅 |
| `crypto_fx_daily_kline` | 加密/汇率K线 | 高精度价格 |
| `commodity_daily_kline` | 贵金属K线 | 黄金/白银 |
| `futures_rollover` | 期货移仓信号 | 量比/仓比分析 |
| `realtime_prices` | 实时价格 | 每小时快照 |

### 3. 核心特性

#### 期货移仓信号（IC/IM）
```python
# 移仓逻辑
- 强信号：量比 > 1.5 且 仓比 > 1.5
- 中信号：量比 > 1.0 且 仓比 > 1.0
- 量信号：量比 > 2.0
- 临近到期加权（<=10天）：量比或仓比 > 0.8
```

#### 新闻多源聚合
- **中文源**：新浪财经、证券之家、网易财经
- **英文源**：Reuters RSS（关键词过滤）
- **去重机制**：MD5(URL) -> INSERT IGNORE

#### 历史数据回填
- 启动时立即执行一次
- 每天凌晨3点补齐遗漏数据
- 支持断点续传（基于数据库已有记录）

## 目录结构

```
data_crawler/
├── config/
│   ├── settings.py          # 配置管理（数据库/数据源）
│   └── __init__.py
├── crawlers/
│   ├── commodity_crawler.py # 贵金属爬虫
│   ├── crypto_fx_crawler.py # 加密货币/汇率爬虫
│   ├── futures_crawler.py   # IC/IM期货移仓检测
│   ├── index_crawler.py     # 股指爬虫
│   ├── news_crawler.py      # 新闻爬虫（多源）
│   ├── realtime_crawler.py  # 实时价格爬虫
│   └── __init__.py
├── db/
│   ├── connection.py        # MySQL连接管理
│   ├── init_tables.py       # 表结构初始化
│   └── __init__.py
├── scheduler/
│   ├── main.py              # 定时任务主程序
│   └── __init__.py
├── scripts/                 # 手动执行脚本
│   ├── fetch_commodities.py
│   ├── fetch_crypto_fx.py
│   ├── fetch_daily_close.py
│   └── fetch_indices.py
├── logs/                    # 日志目录
├── .env.example             # 环境变量模板
├── requirements.txt         # 依赖包
├── Dockerfile.crawler       # Docker构建文件
└── docker-compose.crawler.yml
```

## 快速开始

### 1. 配置环境变量

复制并编辑配置文件：
```bash
cp .env.example .env
```

编辑 `.env`：
```bash
DB_HOST=your_mysql_host
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=watchdog_db
TIMEZONE=Asia/Shanghai
LOG_LEVEL=INFO
```

### 2. 安装依赖

```bash
cd data_crawler
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
# 自动创建所有表
python -c "from db.init_tables import init_all_tables; init_all_tables()"
```

### 4. 运行调度器

```bash
# 直接运行
python scheduler/main.py

# 或使用Docker
docker-compose -f docker-compose.crawler.yml up -d
```

## 手动执行脚本

### 测试单个爬虫
```bash
# 抓取指数数据
python scripts/fetch_indices.py

# 抓取加密货币/汇率
python scripts/fetch_crypto_fx.py

# 抓取贵金属
python scripts/fetch_commodities.py

# 抓取今日收盘价
python scripts/fetch_daily_close.py
```

## 依赖库

```
PyMySQL>=1.1.0           # MySQL连接
requests>=2.31.0         # HTTP请求
beautifulsoup4>=4.12.0   # HTML解析
feedparser>=6.0.0        # RSS解析
yfinance>=0.2.30         # 股票/指数数据
ccxt>=4.0.0              # 加密货币数据
APScheduler>=3.10.0      # 定时任务
python-dotenv>=1.0.0     # 环境变量
lxml>=4.9.0              # XML解析
pytz>=2023.3             # 时区处理
pandas>=2.0.0            # 数据处理
```

## 定时任务说明

| 时间 | 任务 | 说明 |
|------|------|------|
| 每小时 :00 | 新闻爬取 | 多源财经新闻 |
| 每小时 :05 | 实时价格 | USD/CNH, BTC, ETH, GOLD, SILVER |
| 每天 03:00 | 历史补齐 | 指数/加密/贵金属 |
| 每天 06:00 | 美股K线 | 前一交易日收盘 |
| 每天 14:30 | 期货检测 | IC/IM移仓信号 |
| 每天 15:30 | A股/港股K线 | 今日收盘 |
| 每天 16:40 | 加密/汇率K线 | 今日收盘 |
| 每天 16:50 | 贵金属K线 | 今日收盘 |
| 启动时 | 立即补齐 | 启动时执行一次 |

## 数据源配置

### 股票指数（settings.py）
```python
INDEX_CONFIG = [
    {"code": "SHCI",     "name": "上证指数",     "ticker": "000001.SS"},
    {"code": "SZCI",     "name": "深成综指",     "ticker": "399001.SZ"},
    {"code": "CHINEXT",  "name": "创业板指数",   "ticker": "399102.SZ"},
    {"code": "HSI",      "name": "恒生指数",     "ticker": "^HSI"},
    {"code": "NASDAQ",   "name": "纳斯达克指数", "ticker": "^IXIC"},
    # ... 更多配置
]
```

### 加密货币/汇率
```python
CRYPTO_FX_CONFIG = [
    {"symbol": "USD_CNH", "name": "美元兑离岸人民币", "type": "fx"},
    {"symbol": "BTC",     "name": "比特币", "type": "crypto", "ccxt_pair": "BTC/USDT"},
    {"symbol": "ETH",     "name": "以太坊", "type": "crypto", "ccxt_pair": "ETH/USDT"},
]
```

## 与主项目集成

### 方案1：独立运行
- 作为独立的数据采集服务
- 通过MySQL为主项目提供历史数据
- 主项目读取数据库进行分析和通知

### 方案2：模块集成
- 将爬虫功能集成到主项目的 `monitors/` 模块
- 复用主项目的调度器和通知系统
- 统一管理所有监控任务

### 方案3：混合模式（推荐）
```
data_crawler: 负责数据采集 -> MySQL
     ↓
主项目: 读取数据库 -> 分析 -> 钉钉通知
```

## 注意事项

1. **数据库配置**：
   - MySQL版本 >= 5.7
   - 字符集：utf8mb4
   - 时区：Asia/Shanghai

2. **网络要求**：
   - 访问Yahoo Finance（可能需要代理）
   - 访问加密货币交易所API
   - 访问中文财经网站

3. **爬虫限制**：
   - 新浪/网易可能有反爬机制
   - Reuters RSS有频率限制
   - 建议添加合理的延迟（已实现）

4. **存储空间**：
   - 新闻表增长较快（每天约100-300条）
   - K线数据每个品种每天1条
   - 实时价格每小时1条
   - 建议定期归档历史数据

5. **安全性**：
   - ⚠️ 不要将 `.env` 文件提交到Git
   - 数据库密码使用环境变量
   - 定期备份数据库

## 故障排查

### 1. 数据库连接失败
```bash
# 检查配置
cat .env

# 测试连接
python -c "from db.connection import execute_query; execute_query('SELECT 1')"
```

### 2. 爬虫无数据
```bash
# 查看日志
tail -f logs/watchdog.log

# 手动测试
python scripts/fetch_indices.py
```

### 3. Docker容器无法启动
```bash
# 查看日志
docker-compose -f docker-compose.crawler.yml logs -f

# 检查环境变量
docker-compose -f docker-compose.crawler.yml config
```

## 技术支持

如有问题，请检查：
1. 日志文件：`logs/watchdog.log`
2. 数据库连接：确认MySQL服务正常
3. 网络访问：确认可以访问数据源API

## 许可证

MIT License
