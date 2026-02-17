# Docker 部署指南

本文档说明如何使用 Docker 部署 FinancialMarketWatchdog Web 服务。

## 系统架构

FinancialMarketWatchdog 是基于 FastAPI 的 Web 服务，包含：
- **FastAPI Web 服务**：提供 RESTful API 接口（端口 8000）
- **后台定时任务**：APScheduler 调度器
- **数据爬取模块**：自动采集市场数据
- **MySQL 数据库**：存储历史数据

---

## 快速开始

### 前提条件

- Docker 和 Docker Compose 已安装
- MySQL 数据库（本地或远程）
- 配置好 `.env` 文件

### 1. 准备配置文件

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env  # Linux/Mac
notepad .env  # Windows
```

**必须配置的项**：
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` - 数据库连接
- `DING_WEBHOOK`, `DING_SECRET` - 钉钉机器人（可选）
- `AI_API_KEY` - 通义千问 API Key（用于 RSS 分析，可选）

### 2. 启动服务

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f watchdog

# 验证服务
curl http://localhost:8000/api/system/health
```

### 3. 访问服务

- **API 文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/api/system/health

---

## 配置说明

### .env 文件配置

```env
# 数据库配置（必填）
DB_HOST=47.95.221.184
DB_PORT=18453
DB_USER=root
DB_PASSWORD=YOUR_PASSWORD
DB_NAME=watchdog_db

# 钉钉通知（选填）
DING_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
DING_SECRET=YOUR_SECRET

# AI 配置（选填）
AI_API_KEY=YOUR_DASHSCOPE_API_KEY
AI_MODEL=qwen-plus
AI_ENABLE_SEARCH=true

# RSS Feed（选填）
RSS_FEED_URL=https://example.com/rss

# 服务配置
TIMEZONE=Asia/Shanghai
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

### docker-compose.yml 说明

```yaml
version: '3.3'

services:
  watchdog:
    build: .
    container_name: investment_watchdog
    restart: unless-stopped
    ports:
      - "8000:8000"        # API 端口映射
    volumes:
      - ./data:/data       # 数据持久化
    env_file:
      - .env               # 环境变量
    environment:
      - TZ=Asia/Shanghai   # 时区
      - PYTHONUNBUFFERED=1 # Python 输出实时显示
    logging:
      driver: "json-file"
      options:
        max-size: "10m"    # 单个日志文件最大 10MB
        max-file: "3"      # 最多保留 3 个日志文件
```

---

## 常见问题与故障排查

### 问题1: 容器无法启动

**症状**: 容器启动后立即退出

**排查步骤**:

```bash
# 1. 查看容器状态
docker-compose ps

# 2. 查看日志
docker-compose logs watchdog

# 3. 检查配置文件
cat .env
```

**常见原因**:
- `.env` 文件不存在或格式错误
- 数据库连接失败
- 端口 8000 被占用

**解决方案**:
```bash
# 确保 .env 存在
cp .env.example .env

# 测试数据库连接
docker-compose run --rm watchdog python -c "
from data_crawler.db.connection import get_db_connection
conn = get_db_connection()
print('Database connection OK')
conn.close()
"

# 检查端口占用
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac
```

---

### 问题2: 数据库连接失败

**错误日志**:
```
pymysql.err.OperationalError: (1045, "Access denied for user 'root'@'x.x.x.x' (using password: YES)")
```

**检查清单**:
1. ✅ 数据库地址、端口、用户名、密码是否正确
2. ✅ 数据库是否允许远程连接
3. ✅ 防火墙是否开放数据库端口
4. ✅ MySQL 用户是否有权限从容器 IP 连接

**测试数据库连接**:
```bash
# 在容器内测试
docker-compose exec watchdog python -c "
from app.config import get_settings
s = get_settings()
print(f'DB_HOST: {s.db_host}')
print(f'DB_PORT: {s.db_port}')
print(f'DB_NAME: {s.db_name}')
"
```

---

### 问题3: API 接口超时

**症状**:
- `GET /api/market/a-share` 超时
- `GET /api/market/us-stock` 超时

**原因**: 这些接口需要实时获取大量股票数据

**解决方案**:
- 使用 POST 接口触发异步任务
- 添加缓存（正在优化中）
- 增加请求超时时间

```python
# 使用异步触发
import requests

# 不推荐：同步获取（可能超时）
# response = requests.get("http://localhost:8000/api/market/a-share")

# 推荐：异步触发
response = requests.post("http://localhost:8000/api/market/a-share/report")
# 响应立即返回，任务在后台执行
```

---

### 问题4: 定时任务未执行

**检查定时任务状态**:
```bash
# 查看所有任务
curl http://localhost:8000/api/system/jobs

# 手动触发任务（测试）
curl -X POST http://localhost:8000/api/system/jobs/trigger \
  -H "Content-Type: application/json" \
  -d '{"job_id": "a_share_daily_report"}'
```

**检查日志**:
```bash
# 查看 scheduler 相关日志
docker-compose logs watchdog | grep scheduler
docker-compose logs watchdog | grep "job_id"
```

---

### 问题5: 网络超时

**症状**: 日志中出现 `requests.exceptions.ReadTimeout`

**原因**:
- 外部 API（东方财富、新浪财经等）响应慢
- DNS 解析问题
- 网络限制

**解决方案**:

**方案A: 配置 DNS**
```yaml
# docker-compose.yml
services:
  watchdog:
    dns:
      - 114.114.114.114
      - 8.8.8.8
```

**方案B: 容器内诊断**
```bash
# 进入容器
docker-compose exec watchdog /bin/bash

# 测试 DNS
ping -c 3 push2.eastmoney.com

# 测试 Python 网络
python -c "import requests; print(requests.get('https://www.baidu.com').status_code)"
```

**方案C: 使用代理**
```env
# .env
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080
```

---

## Docker 命令速查

### 容器管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart watchdog

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f watchdog
docker-compose logs --tail=100 watchdog

# 进入容器
docker-compose exec watchdog /bin/bash
```

### 镜像管理

```bash
# 重新构建
docker-compose build

# 无缓存重新构建
docker-compose build --no-cache

# 查看镜像
docker images | grep investment_watchdog

# 删除旧镜像
docker image prune
```

### 数据管理

```bash
# 备份 data 目录
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# 恢复数据
tar -xzf backup-20260217.tar.gz

# 导出容器数据
docker cp investment_watchdog:/data ./data_backup
```

---

## 生产环境建议

### 1. 资源限制

```yaml
# docker-compose.yml
services:
  watchdog:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '1.0'
          memory: 512M
```

### 2. 自动重启策略

```yaml
services:
  watchdog:
    restart: unless-stopped  # 推荐
    # 或使用: restart: always
```

### 3. 健康检查

```yaml
services:
  watchdog:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/system/health"]
      interval: 1m
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 4. 反向代理（Nginx）

```nginx
# nginx.conf
server {
    listen 80;
    server_name watchdog.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # 增加超时
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### 5. HTTPS 配置（Let's Encrypt）

```bash
# 安装 certbot
apt-get install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d watchdog.example.com

# 自动续期
crontab -e
0 0 * * * certbot renew --quiet
```

---

## 监控和日志

### 1. 查看实时日志

```bash
# 实时跟踪
docker-compose logs -f

# 过滤关键字
docker-compose logs -f | grep ERROR
docker-compose logs -f | grep "job_id"

# 保存到文件
docker-compose logs > logs/docker-$(date +%Y%m%d).log
```

### 2. 日志轮转

已配置自动日志轮转（每个文件最大 10MB，保留 3 个文件）

如需调整：
```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "50m"  # 增大到 50MB
    max-file: "5"    # 保留 5 个文件
```

### 3. 监控工具

推荐使用：
- **Portainer** - Web UI 管理 Docker
- **Prometheus + Grafana** - 监控和可视化
- **cAdvisor** - 容器指标收集

---

## 更新和维护

### 更新代码

```bash
# 1. 停止服务
docker-compose down

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建并启动
docker-compose up -d --build

# 4. 验证服务
curl http://localhost:8000/api/system/health
```

### 数据库迁移

```bash
# 备份数据库
docker-compose exec -T watchdog python -c "
from data_crawler.db.init_tables import init_all_tables
from data_crawler.db.stock_history_tables import init_stock_history_tables
init_all_tables()
init_stock_history_tables()
print('Database tables initialized')
"
```

### 完全重建（紧急修复）

```bash
# 1. 完全停止并删除
docker-compose down -v
docker rmi $(docker images | grep investment_watchdog | awk '{print $3}')

# 2. 清理数据（可选）
# rm -rf data/*

# 3. 重新构建
docker-compose up -d --build

# 4. 查看日志
docker-compose logs -f
```

---

## 性能优化

### 1. 减小镜像大小

已使用 `python:3.11-slim` 基础镜像

创建 `.dockerignore`:
```
__pycache__
*.pyc
*.pyo
*.log
.git
.gitignore
.vscode
.idea
*.md
test/
.env
data/
```

### 2. 使用构建缓存

```bash
# 使用缓存（快）
docker-compose build

# 不使用缓存（慢但干净）
docker-compose build --no-cache
```

### 3. 多阶段构建（可选）

编辑 `Dockerfile`:
```dockerfile
# 构建阶段
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
WORKDIR /app
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 故障排查清单

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| 容器立即退出 | 配置错误 | 检查 `.env` 和日志 |
| 数据库连接失败 | 密码错误/网络问题 | 验证数据库配置 |
| API 超时 | 数据量大 | 使用异步接口 |
| 定时任务未执行 | 时区/调度器问题 | 检查 `/api/system/jobs` |
| 端口被占用 | 8000 已使用 | 修改 `ports` 映射 |
| 内存不足 | 资源限制 | 增加内存限制 |

---

## 参考资料

- **项目主文档**: [README.md](README.md)
- **API 文档**: http://localhost:8000/docs
- **Docker 官方文档**: https://docs.docker.com/
- **Docker Compose 文档**: https://docs.docker.com/compose/
- **FastAPI 文档**: https://fastapi.tiangolo.com/

---

## 技术支持

如遇问题：
1. 查看 [README.md](README.md) 了解系统功能
2. 检查日志: `docker-compose logs -f`
3. 查看 API 文档: http://localhost:8000/docs
4. 提交 Issue: https://github.com/mengwuzhi/FinancialMarketWatchdog/issues
