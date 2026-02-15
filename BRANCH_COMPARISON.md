# 分支对比说明

本项目现在有两个分支，分别服务于不同的使用场景。

## 分支概览

### 📌 main 分支（通知为王）

**定位**：轻量级实时监控 + 智能通知系统

**核心功能**：
- ✅ LOF基金实时监控（涨跌停/急涨急跌/开板提醒）
- ✅ A股市场日报（指数/板块/资金流向）
- ✅ 美股市场日报（三大指数/科技股/中概股）
- ✅ RSS文章AI分析（通义千问智能摘要）
- ✅ 钉钉实时推送

**技术特点**：
- 无数据库依赖（JSON状态文件）
- Docker一键部署
- 完善的文档
- 低成本运行（¥35-70/月）

**适合人群**：
- 个人投资者
- 需要实时告警的短线交易者
- 对历史数据无强需求的用户

---

### 🚀 feature/data-crawler-integration 分支（数据为王）

**定位**：完整的金融数据平台 = 实时通知 + 历史数据

**包含main分支所有功能 +**：

**新增功能**：
- ✅ 多源财经新闻采集（新浪/证券之家/网易/Reuters）
- ✅ 全球指数历史K线（A股/港股/美股）
- ✅ 加密货币/汇率数据（BTC/ETH/USD_CNH）
- ✅ 贵金属价格（黄金/白银）
- ✅ IC/IM期货移仓信号检测
- ✅ 实时价格每小时快照
- ✅ MySQL数据库存储（6张表）

**技术特点**：
- MySQL历史数据存储
- 完整的爬虫系统（6个专业爬虫）
- 定时任务调度（9个任务）
- 数据分析和回测能力
- 高级功能成本（¥80-150/月含数据库）

**适合人群**：
- 量化研究员
- 需要历史数据回测的开发者
- 数据分析师
- 构建个人数据仓库的用户

---

## 快速对比

| 维度 | main分支 | 集成分支 |
|------|---------|---------|
| **部署难度** | ⭐⭐⭐⭐⭐ 简单 | ⭐⭐⭐ 中等（需MySQL） |
| **运行成本** | ⭐⭐⭐⭐⭐ 低 | ⭐⭐⭐ 中等 |
| **功能丰富度** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **数据能力** | ⭐⭐ 实时监控 | ⭐⭐⭐⭐⭐ 历史分析 |
| **通知能力** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **文档完善度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 使用建议

### 场景1：我只需要实时提醒
👉 使用 **main分支**

```bash
git checkout main
docker-compose up -d
```

### 场景2：我需要数据分析和历史回测
👉 使用 **集成分支**

```bash
git checkout feature/data-crawler-integration

# 运行主监控（通知）
docker-compose up -d

# 运行数据采集（存储）
cd data_crawler
docker-compose -f docker-compose.crawler.yml up -d
```

### 场景3：先测试再决定
👉 先用 **main分支** 体验通知功能，后续再切换到集成分支

```bash
# 第一阶段：测试通知
git checkout main
docker-compose up -d

# 第二阶段：需要数据时切换
git checkout feature/data-crawler-integration
```

---

## 分支切换

### 查看所有分支
```bash
git branch -a
```

### 切换到main分支
```bash
git checkout main
```

### 切换到集成分支
```bash
git checkout feature/data-crawler-integration
```

### 查看当前分支
```bash
git branch
```

---

## 文件结构对比

### main分支结构
```
FinancialMarketWatchdog_src/
├── analyzers/          # AI分析（RSS）
├── config/             # 配置管理
├── core/               # 调度+交易日
├── monitors/           # LOF/A股/美股监控
├── data_sources/       # 数据源封装
├── notifiers/          # 钉钉通知
├── storage/            # JSON状态
├── utils/              # 工具函数
├── db/                 # ⚠️ 数据库模块（未使用）
├── main.py             # 主程序
└── README.md           # 主文档
```

### 集成分支额外增加
```
FinancialMarketWatchdog_src/
├── ... (所有main分支文件)
├── data_crawler/               # 新增：数据采集模块
│   ├── config/                 # 数据库配置
│   ├── crawlers/               # 6个专业爬虫
│   │   ├── commodity_crawler.py
│   │   ├── crypto_fx_crawler.py
│   │   ├── futures_crawler.py
│   │   ├── index_crawler.py
│   │   ├── news_crawler.py
│   │   └── realtime_crawler.py
│   ├── db/                     # MySQL连接层
│   ├── scheduler/              # 定时任务
│   ├── scripts/                # 手动脚本
│   ├── logs/                   # 日志目录
│   ├── README.md               # 模块文档
│   └── requirements.txt        # 依赖
├── INTEGRATION_GUIDE.md        # 集成指南
└── BRANCH_COMPARISON.md        # 本文档
```

---

## 数据库表结构（仅集成分支）

| 表名 | 记录数（估算） | 用途 |
|------|--------------|------|
| `news` | ~5万条/年 | 财经新闻聚合 |
| `index_daily_kline` | ~2500条/年/指数 | 股指日K线 |
| `crypto_fx_daily_kline` | ~1500条/年/品种 | 加密货币/汇率K线 |
| `commodity_daily_kline` | ~250条/年/品种 | 贵金属K线 |
| `futures_rollover` | ~500条/年 | 期货移仓信号 |
| `realtime_prices` | ~4万条/年/品种 | 实时价格快照 |

---

## 成本对比

### main分支运行成本
```
服务器：         ¥30-50/月
通义千问API：    ¥5-20/月
数据库：         ¥0（无需）
─────────────────────────
总计：          ¥35-70/月
```

### 集成分支运行成本
```
服务器：         ¥30-50/月
通义千问API：    ¥5-20/月
MySQL云数据库：  ¥50-100/月
─────────────────────────
总计：          ¥85-170/月
```

**省钱技巧**：
- 使用本地MySQL：成本降至¥35-70/月
- 关闭AI搜索：通义千问费用降低50%

---

## 迁移路径

### 从main升级到集成分支

1. **备份当前数据**
   ```bash
   cp -r data/ data_backup/
   ```

2. **切换分支**
   ```bash
   git checkout feature/data-crawler-integration
   ```

3. **配置数据库**
   ```bash
   cd data_crawler
   cp .env.example .env
   vim .env  # 配置MySQL
   ```

4. **初始化表结构**
   ```bash
   python -c "from db.init_tables import init_all_tables; init_all_tables()"
   ```

5. **启动服务**
   ```bash
   # 主监控
   docker-compose up -d

   # 数据采集
   cd data_crawler
   docker-compose -f docker-compose.crawler.yml up -d
   ```

### 从集成分支降级到main

```bash
# 停止数据采集服务
cd data_crawler
docker-compose -f docker-compose.crawler.yml down

# 切换回main
cd ..
git checkout main

# 主监控继续运行（无需重启）
```

---

## 常见问题

### Q1: 两个分支可以同时运行吗？
**A**: 不建议。它们会争抢相同的端口和资源。应该选择一个分支运行。

### Q2: 数据会丢失吗？
**A**:
- main分支：`data/` 目录的JSON文件会保留
- 集成分支：MySQL数据库独立存储，切换分支不影响

### Q3: 我应该选哪个分支？
**A**:
- 只需要实时提醒 → main分支
- 需要历史数据分析 → 集成分支
- 不确定 → 先用main，随时可切换

### Q4: 集成分支会合并到main吗？
**A**:
- 短期：保持分支独立，方便选择
- 长期：根据用户反馈决定是否合并

### Q5: 如何查看分支差异？
**A**:
```bash
git diff main feature/data-crawler-integration
```

---

## 更新日志

### 2026-02-13
- ✅ 创建 feature/data-crawler-integration 分支
- ✅ 集成数据采集模块（来自FinancialMarketWatchdog项目）
- ✅ 添加完整文档（README + 集成指南 + 对比说明）
- ✅ 24个文件，1773行代码

---

## 总结

**main分支**：开箱即用，专注通知
**集成分支**：功能完整，面向未来

选择适合你的分支，开始使用吧！🎯

有问题查看：
- 主项目文档：[README.md](README.md)
- 数据模块文档：[data_crawler/README.md](data_crawler/README.md)
- 集成指南：[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
