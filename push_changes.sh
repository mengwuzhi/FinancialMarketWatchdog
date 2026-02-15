#!/bin/bash

echo "Pushing FinancialMarketWatchdog web service changes..."

# 设置Git配置
git config user.email "mengwuzhi@users.noreply.github.com"
git config user.name "mengwuzhi"

# 添加所有更改
git add .

# 提交更改
git commit -m "Complete Web service transformation from script system to FastAPI

Major changes:
1. Added complete FastAPI web service architecture (financial_watchdog_web/)
2. Created WEB_SERVICE_ARCHITECTURE.md documenting the transformation
3. Removed outdated documentation files

New web service features:
- Complete API layer with 6 modules (auth, market, rss, futures, data, system)
- Service layer with business logic implementation
- Data models for users, monitors, tasks, and system data
- Celery worker for asynchronous task processing
- Docker Compose configuration for deployment
- Comprehensive API documentation
- System monitoring and health checks
- Task scheduling and management"

# 使用gh命令推送
echo "Creating pull request..."
gh pr create --title "Web Service Transformation: Complete FastAPI Architecture" --body "## Complete Transformation from Script System to Full Web Service

### Major Changes:
1. **Added complete FastAPI web service architecture** (\`financial_watchdog_web/\`)
2. **Created comprehensive documentation** including WEB_SERVICE_ARCHITECTURE.md
3. **Removed outdated documentation files** that are no longer relevant

### New Web Service Features:
- **Complete API layer** with 6 modules (auth, market, rss, futures, data, system)
- **Service layer** with business logic implementation
- **Data models** for users, monitors, tasks, and system data
- **Celery worker** for asynchronous task processing
- **Docker Compose configuration** for easy deployment
- **Comprehensive API documentation**
- **System monitoring** and health checks
- **Task scheduling** and management

### Architecture Improvements:
- Modern FastAPI-based architecture
- Support for multi-user access and API integration
- Production-ready deployment configuration
- Complete testing suite
- Modular and extensible design

This transformation turns the FinancialMarketWatchdog from a script-based system into a full-featured web service with modern architecture." --base main --head feature/web-service-transformation

echo "Done!"