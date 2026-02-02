# Docker部署指南

本文档说明如何使用Docker部署投资监控系统。

## 快速开始

### Windows用户

```bash
# 运行启动脚本（会自动创建所需文件和目录）
docker-start.bat
```

### Linux/Mac用户

```bash
# 添加执行权限
chmod +x docker-start.sh

# 运行启动脚本
./docker-start.sh
```

## 手动启动步骤

如果不使用启动脚本，按以下步骤操作：

### 1. 创建data目录

```bash
mkdir -p data
```

### 2. 准备配置文件

```bash
# 复制示例配置
cp data/config.json.example data/config.json

# 编辑配置文件
notepad data/config.json  # Windows
vim data/config.json      # Linux/Mac
```

必须填写：
- `dingtalk.webhook` - 钉钉机器人webhook
- `dingtalk.secret` - 钉钉机器人secret
- `ai.api_key` - AI API密钥（如果使用RSS分析）

### 3. 准备LOF代码文件

```bash
# 创建涨跌停监控代码文件
cat > data/lof_limit_codes.txt << EOF
# LOF涨跌停监控代码，一行一个
161226
161225
EOF

# 创建急涨急跌监控代码文件
cat > data/lof_speed_codes.txt << EOF
# LOF急涨急跌监控代码，一行一个
161725
EOF
```

### 4. 启动容器

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

## 常见问题与故障排查

### 问题1: "Config file not found"（配置文件循环错误）

**错误症状**:
```
investment_watchdog | [ERROR] Config file not found: data/config.json
investment_watchdog | Creating default config file...
investment_watchdog | [ERROR] Failed to save default config: [Errno 2] No such file or directory
```

容器不断重启，无法正常运行。

**问题原因**:

路径不匹配导致容器内找不到配置文件：
```
容器工作目录：/app
代码期望路径：/app/data/config.json
原挂载路径：./data → /data （错误）
结果：main.py 在 /app/data/ 找文件，但文件在 /data/
```

**已修复**: docker-compose.yml 已更新为正确的挂载路径：
```yaml
# 修复前（错误）
volumes:
  - ./data:/data

# 修复后（正确）✅
volumes:
  - ./data:/app/data
```

**解决方案A - 使用启动脚本（推荐）**:
```bash
# Windows
docker-start.bat

# Linux/Mac
./docker-start.sh
```

**解决方案B - 手动修复**:
```bash
# 1. 停止容器
docker-compose down

# 2. 确保本地有data目录和配置文件
mkdir -p data
cp data/config.json.example data/config.json
# 编辑 data/config.json 填写必需信息

# 3. 创建LOF代码文件
touch data/lof_limit_codes.txt
touch data/lof_speed_codes.txt

# 4. 重新构建并启动
docker-compose up -d --build

# 5. 查看日志验证
docker-compose logs -f
```

**验证修复成功**:

容器状态正常：
```bash
$ docker-compose ps
NAME                      STATUS
investment_watchdog       Up 5 minutes
```

日志输出正常：
```
==================================================
Investment Watchdog System Started
==================================================
Config: data/config.json
Timezone: Asia/Shanghai
LOF Limit Codes: 5
LOF Speed Codes: 3
RSS Monitoring: Enabled
Registered Jobs: 5
==================================================
```

### 问题2: 容器一直重启

**检查日志**:
```bash
docker-compose logs investment_watchdog
```

**常见原因和解决**:

1. **配置文件格式错误**
   ```bash
   # 验证JSON格式
   python -m json.tool data/config.json
   ```
   如果报错，说明JSON格式有问题（可能是逗号、括号不对）

2. **依赖包安装失败**
   ```bash
   # 重新构建镜像
   docker-compose build --no-cache
   ```

3. **权限问题**
   ```bash
   # Linux/Mac: 修改data目录权限
   chmod -R 777 data
   ```

4. **docker-compose.yml路径配置**
   ```bash
   # 验证挂载路径
   grep "app/data" docker-compose.yml
   ```
   应该看到：`- ./data:/app/data`

5. **检查挂载是否正确**
   ```bash
   # 进入容器检查
   docker-compose exec watchdog ls -la /app/data/
   # 应该看到config.json等文件
   ```

### 问题3: 网络超时和连接问题

**症状**: 日志中出现网络超时错误
```
requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='88.push2.eastmoney.com', port=443): Read timed out
```

**原因分析**:
- 东方财富网免费API在交易高峰期响应慢
- DNS解析问题
- 防火墙或网络限制

**解决方案**:

**方案A: 配置DNS服务器**
```yaml
# docker-compose.yml
services:
  watchdog:
    # ... 其他配置
    dns:
      - 114.114.114.114
      - 8.8.8.8
```

**方案B: 容器内诊断**
```bash
# 进入容器
docker-compose exec watchdog /bin/bash

# 测试DNS
ping -c 3 88.push2.eastmoney.com

# 测试Python网络
python -c "import akshare as ak; print(ak.fund_lof_spot_em().shape)"
```

**方案C: 系统已内置重试机制**

代码中已添加重试装饰器（见 `utils/retry_helper.py`），会自动重试3次。如果持续失败：
- 检查是否在交易时间
- 非高峰期测试
- 检查防火墙设置

**方案D: 网络问题详细排查**

1. **DNS问题**
   ```bash
   # Windows
   ipconfig /flushdns
   nslookup 88.push2.eastmoney.com

   # Linux
   systemd-resolve --flush-caches
   nslookup 88.push2.eastmoney.com
   ```

2. **防火墙检查**
   - Windows: 控制面板 → Windows Defender防火墙 → 允许应用通过防火墙
   - 确保Docker有网络权限

3. **代理设置检查**
   ```bash
   # Windows
   echo %HTTP_PROXY%
   echo %HTTPS_PROXY%

   # 如果设置了不需要的代理，取消它
   set HTTP_PROXY=
   set HTTPS_PROXY=
   ```

### 问题4: 容器时区不正确

**已在Dockerfile中设置为Asia/Shanghai**

如需修改，编辑Dockerfile:
```dockerfile
RUN ln -snf /usr/share/zoneinfo/YOUR_TIMEZONE /etc/localtime && \
    echo YOUR_TIMEZONE > /etc/timezone
```

### 问题5: 日志太多占用空间

**已配置日志轮转**:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

每个容器最多保留3个文件，每个文件最大10MB

### 问题6: 完全重建（紧急修复方案）

如果上述方法都不行：

```bash
# 1. 完全停止并删除
docker-compose down -v
docker rmi lof_watchdog-watchdog

# 2. 清理并重新准备
rm -rf data/
mkdir -p data
cp data/config.json.example data/config.json
# 编辑 data/config.json

# 3. 重新构建和启动
docker-compose up -d --build

# 4. 查看日志
docker-compose logs -f
```

## Docker命令速查

### 容器管理

```bash
# 启动容器
docker-compose up -d

# 停止容器
docker-compose down

# 重启容器
docker-compose restart

# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100

# 进入容器shell
docker-compose exec watchdog /bin/bash
```

### 镜像管理

```bash
# 重新构建镜像
docker-compose build

# 无缓存重新构建
docker-compose build --no-cache

# 查看镜像
docker images | grep investment_watchdog

# 删除旧镜像
docker image prune
```

### 数据卷管理

```bash
# 查看挂载的数据卷
docker volume ls

# 查看容器的卷挂载
docker inspect investment_watchdog
```

### 清理

```bash
# 停止并删除容器（保留数据）
docker-compose down

# 删除容器和镜像（保留数据）
docker-compose down --rmi all

# 删除所有（包括数据卷）
docker-compose down -v

# 清理未使用的资源
docker system prune
```

## 生产环境建议

### 1. 资源限制

编辑 `docker-compose.yml`:

```yaml
services:
  watchdog:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### 2. 自动重启策略

```yaml
services:
  watchdog:
    restart: unless-stopped  # 已配置
    # 或使用
    # restart: always
```

### 3. 健康检查

```yaml
services:
  watchdog:
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 1m
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 4. 使用环境变量（推荐）

避免敏感信息写在配置文件中：

```yaml
services:
  watchdog:
    environment:
      - DINGTALK_WEBHOOK=${DINGTALK_WEBHOOK}
      - DINGTALK_SECRET=${DINGTALK_SECRET}
      - AI_API_KEY=${AI_API_KEY}
```

创建 `.env` 文件：
```
DINGTALK_WEBHOOK=your_webhook
DINGTALK_SECRET=your_secret
AI_API_KEY=your_api_key
```

**注意**: 将 `.env` 添加到 `.gitignore`

### 5. 监控和告警

使用Docker监控工具：

- **Portainer** - Web UI管理Docker
- **Prometheus + Grafana** - 监控和可视化
- **cAdvisor** - 容器指标收集

## 更新和备份

### 更新代码

```bash
# 1. 停止容器
docker-compose down

# 2. 拉取最新代码
git pull

# 3. 重新构建并启动
docker-compose up -d --build
```

### 备份数据

```bash
# 备份data目录
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# 恢复
tar -xzf backup-20260113.tar.gz
```

### 数据迁移

```bash
# 导出容器数据
docker cp investment_watchdog:/data ./data_backup

# 导入到新容器
docker cp ./data_backup/. investment_watchdog:/data
```

## 性能优化

### 1. 使用多阶段构建（可选）

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
CMD ["python", "main.py"]
```

### 2. 使用镜像缓存加速构建

```bash
# 使用构建缓存
docker-compose build

# 不使用缓存（完全重建）
docker-compose build --no-cache
```

### 3. 减小镜像大小

- 使用 `python:3.11-slim` 而非 `python:3.11`（已使用）
- 清理apt缓存（已实现）
- 使用 `.dockerignore` 排除不必要文件

创建 `.dockerignore`:
```
__pycache__
*.pyc
*.pyo
*.log
.git
.gitignore
.vscode
test_*.py
*.md
data/
```

## 故障排查

### 查看完整日志

```bash
# 实时日志
docker-compose logs -f

# 保存日志到文件
docker-compose logs > docker.log
```

### 进入容器调试

```bash
# 进入运行中的容器
docker-compose exec watchdog /bin/bash

# 查看Python环境
python --version
pip list

# 查看data目录
ls -la /data

# 测试网络
ping -c 3 88.push2.eastmoney.com

# 测试Python导入
python -c "import akshare as ak; print('OK')"
```

### 检查容器配置

```bash
# 查看容器详细信息
docker inspect investment_watchdog

# 查看环境变量
docker exec investment_watchdog env

# 查看挂载
docker exec investment_watchdog mount | grep /data
```

## 常见错误代码

| 错误 | 原因 | 解决 |
|------|------|------|
| Exit 0 | 正常退出 | 检查main.py逻辑 |
| Exit 1 | 配置错误 | 检查config.json |
| Exit 137 | 内存不足 | 增加内存限制 |
| Exit 139 | 段错误 | 检查依赖库版本 |

## 参考资料

- [Docker官方文档](https://docs.docker.com/)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [项目README](README.md)
- [测试指南](TESTING_README.md)

---

如遇问题，请查看日志并参考本文档的故障排查部分。
