# 数据爬虫模块集成指南

本文档说明如何使用 `feature/data-crawler-integration` 分支集成的数据采集功能。

## 分支说明

### main 分支
- **定位**：实时监控 + 通知系统
- **功能**：LOF监控、A股/美股日报、RSS AI分析
- **输出**：钉钉通知
- **存储**：JSON状态文件

### feature/data-crawler-integration 分支
- **定位**：main分支 + 数据采集模块
- **新增**：历史数据存储、新闻爬虫、期货移仓信号
- **输出**：钉钉通知 + MySQL数据库
- **存储**：JSON + MySQL

## 快速开始

### 1. 切换到集成分支

```bash
# 查看所有分支
git branch -a

# 切换到集成分支
git checkout feature/data-crawler-integration

# 查看新增的目录
ls -la data_crawler/
```

### 2. 查看新增功能

```bash
# 查看数据爬虫模块文档
cat data_crawler/README.md

# 查看目录结构
tree data_crawler/
```

### 3. 配置数据库（可选）

如果需要使用数据采集功能：

```bash
# 复制环境变量配置
cd data_crawler
cp .env.example .env

# 编辑数据库配置
vim .env
```

配置内容：
```bash
DB_HOST=your_mysql_host
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=watchdog_db
TIMEZONE=Asia/Shanghai
LOG_LEVEL=INFO
```

### 4. 初始化数据库表

```bash
cd data_crawler
pip install -r requirements.txt

# 创建数据库表
python -c "from db.init_tables import init_all_tables; init_all_tables()"
```

### 5. 运行数据采集器

```bash
# 方式1：直接运行
python scheduler/main.py

# 方式2：使用Docker
docker-compose -f docker-compose.crawler.yml up -d
```

## 使用场景

### 场景1：仅使用通知功能（main分支）

**适合**：个人投资者，只需要实时告警

```bash
git checkout main
docker-compose up -d
```

**特点**：
- ✅ 轻量级，无数据库
- ✅ 部署简单
- ✅ LOF/A股/美股实时监控
- ✅ AI分析RSS文章
- ❌ 无历史数据

### 场景2：通知 + 数据采集（集成分支）

**适合**：量化研究员，需要历史数据分析

```bash
git checkout feature/data-crawler-integration

# 运行主监控系统（钉钉通知）
docker-compose up -d

# 运行数据采集器（MySQL存储）
cd data_crawler
docker-compose -f docker-compose.crawler.yml up -d
```

**特点**：
- ✅ 完整的通知功能
- ✅ 历史数据存储（MySQL）
- ✅ 新闻自动采集
- ✅ 期货移仓信号
- ⚠️ 需要MySQL数据库

### 场景3：仅数据采集（无通知）

**适合**：构建数据仓库，后续分析使用

```bash
git checkout feature/data-crawler-integration
cd data_crawler
python scheduler/main.py
```

**特点**：
- ✅ 专注数据采集
- ✅ 轻量级运行
- ❌ 无实时告警

## 数据流向

### Main分支数据流
```
数据源 → 实时监控 → 钉钉通知
         ↓
      state.json
```

### 集成分支数据流
```
┌─────────────────┐
│  主监控系统      │  → 钉钉通知
│  (main功能)     │  → state.json
└─────────────────┘

┌─────────────────┐
│  数据采集模块    │  → MySQL数据库
│  (data_crawler) │     ├─ 新闻表
└─────────────────┘     ├─ K线表
                        ├─ 实时价格表
                        └─ 期货信号表
```

### 完整集成数据流（推荐）
```
           ┌──────────────┐
           │ 数据源API     │
           └──────┬───────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
  ┌──────────┐      ┌──────────────┐
  │主监控系统│      │数据采集模块   │
  │(实时告警)│      │(历史存储)     │
  └────┬─────┘      └──────┬───────┘
       │                   │
       ▼                   ▼
  ┌─────────┐      ┌──────────────┐
  │钉钉通知 │      │MySQL数据库    │
  └─────────┘      └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │数据分析/回测  │
                   └──────────────┘
```

## 功能对比

| 功能 | main分支 | 集成分支 |
|------|---------|---------|
| LOF实时监控 | ✅ | ✅ |
| A股市场日报 | ✅ | ✅ |
| 美股市场日报 | ✅ | ✅ |
| RSS AI分析 | ✅ | ✅ |
| 钉钉通知 | ✅ | ✅ |
| **新闻采集** | ❌ | ✅ |
| **历史K线数据** | ❌ | ✅ |
| **期货移仓信号** | ❌ | ✅ |
| **实时价格快照** | ❌ | ✅ |
| **MySQL存储** | ❌ | ✅ |

## 合并策略建议

### 方案A：保持分支独立（推荐新手）

```bash
# main分支用于生产环境（稳定）
git checkout main

# 集成分支用于测试新功能
git checkout feature/data-crawler-integration
```

**优点**：
- 互不影响，风险隔离
- 可以随时切换
- 适合评估阶段

### 方案B：合并到main（推荐高级用户）

```bash
# 确认集成分支功能正常
git checkout feature/data-crawler-integration
# ... 测试 ...

# 合并到main
git checkout main
git merge feature/data-crawler-integration

# 解决可能的冲突
git status
```

**优点**：
- 统一管理
- 功能完整
- 适合长期使用

### 方案C：选择性集成（推荐定制化）

只集成需要的功能模块：

```bash
git checkout main

# 只复制期货爬虫
git checkout feature/data-crawler-integration -- data_crawler/crawlers/futures_crawler.py
git checkout feature/data-crawler-integration -- data_crawler/db/

# 自行调整集成到主项目
```

## 配置文件说明

### 主项目配置（data/config.json）
```json
{
  "dingtalk": {...},      // 钉钉通知配置
  "lof": {...},           // LOF监控配置
  "ai": {...},            // AI分析配置
  "rss": {...}            // RSS订阅配置
}
```

### 数据采集配置（data_crawler/.env）
```bash
DB_HOST=...             # 数据库主机
DB_PASSWORD=...         # 数据库密码
TIMEZONE=Asia/Shanghai  # 时区
LOG_LEVEL=INFO          # 日志级别
```

## Docker部署

### 单独部署

```bash
# 主监控系统
docker-compose up -d

# 数据采集模块
cd data_crawler
docker-compose -f docker-compose.crawler.yml up -d
```

### 统一部署（需自行配置）

创建 `docker-compose.unified.yml`：
```yaml
version: '3.8'

services:
  # 主监控系统
  watchdog:
    build: .
    container_name: investment_watchdog
    restart: unless-stopped
    volumes:
      - ./data:/app/data
    environment:
      - TZ=Asia/Shanghai

  # 数据采集模块
  crawler:
    build:
      context: data_crawler
      dockerfile: Dockerfile.crawler
    container_name: data_crawler
    restart: unless-stopped
    env_file:
      - data_crawler/.env
    volumes:
      - ./data_crawler/logs:/app/logs
    depends_on:
      - mysql

  # MySQL数据库
  mysql:
    image: mysql:8.0
    container_name: watchdog_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: your_password
      MYSQL_DATABASE: watchdog_db
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

volumes:
  mysql_data:
```

## 数据查询示例

### 查询最新新闻

```sql
SELECT title, source, publish_time
FROM news
ORDER BY created_at DESC
LIMIT 10;
```

### 查询指数K线

```sql
SELECT index_code, trade_date, close_price, change_pct
FROM index_daily_kline
WHERE index_code = 'SHCI'
  AND trade_date >= '2024-01-01'
ORDER BY trade_date DESC;
```

### 查询期货移仓信号

```sql
SELECT contract_type, check_date,
       volume_ratio, oi_ratio,
       rollover_signal, signal_reason
FROM futures_rollover
WHERE rollover_signal = 1
ORDER BY check_date DESC;
```

### 查询实时价格趋势

```sql
SELECT symbol, record_time, price, change_24h
FROM realtime_prices
WHERE symbol = 'BTC'
  AND record_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY record_time;
```

## 故障排查

### 问题1：数据采集器启动失败

```bash
# 检查MySQL连接
python -c "from data_crawler.db.connection import execute_query; execute_query('SELECT 1')"

# 查看日志
tail -f data_crawler/logs/watchdog.log
```

### 问题2：主监控和数据采集冲突

如果两个系统都在抓取相同数据源：
- 调整定时任务避免同时执行
- 使用不同的数据源API
- 增加请求延迟

### 问题3：MySQL存储空间不足

```sql
-- 查看表大小
SELECT
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'watchdog_db'
ORDER BY (data_length + index_length) DESC;

-- 定期清理旧数据
DELETE FROM news WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);
DELETE FROM realtime_prices WHERE record_time < DATE_SUB(NOW(), INTERVAL 1 MONTH);
```

## 后续开发建议

### 短期（1-2周）
1. ✅ 测试数据采集模块稳定性
2. ✅ 优化数据库查询性能（添加索引）
3. ✅ 集成期货移仓信号到钉钉通知

### 中期（1个月）
1. 📊 开发数据分析接口
2. 📈 添加K线图表生成
3. 🔔 基于历史数据的异常检测告警

### 长期（3个月）
1. 🤖 机器学习预测模型
2. 📱 Web可视化界面
3. 🔄 策略回测系统

## 总结

- **main分支**：轻量级，专注实时通知
- **集成分支**：完整功能，包含数据存储
- **推荐**：先测试集成分支，稳定后合并或独立使用

选择适合你需求的方案，开始使用吧！🚀
