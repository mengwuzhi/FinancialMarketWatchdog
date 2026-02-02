@echo off
REM Docker快速启动脚本 - Windows版本（已修复路径）

echo ==================================
echo 投资监控系统 - Docker启动
echo ==================================
echo 注意：已修复Docker挂载路径问题
echo.

REM 检查data目录
if not exist "data" (
    echo. 创建data目录...
    mkdir data
)

REM 检查配置文件
if not exist "data\config.json" (
    echo 警告: 配置文件不存在

    if exist "data\config.json.example" (
        echo 从示例创建配置文件...
        copy data\config.json.example data\config.json
        echo.
        echo 请编辑 data\config.json 填写以下信息:
        echo   1. 钉钉webhook和secret
        echo   2. AI API Key
        echo   3. RSS Feed URL
        echo.
        echo 编辑完成后重新运行此脚本
        pause
        exit /b 1
    ) else (
        echo 错误: 找不到 data\config.json.example
        echo 请确保您在项目根目录运行此脚本
        pause
        exit /b 1
    )
)

REM 检查LOF代码文件
if not exist "data\lof_limit_codes.txt" (
    echo 创建LOF涨跌停监控代码文件...
    echo # 在此添加需要监控涨跌停的LOF代码，一行一个 > data\lof_limit_codes.txt
    echo # 示例: >> data\lof_limit_codes.txt
    echo # 161226 >> data\lof_limit_codes.txt
)

if not exist "data\lof_speed_codes.txt" (
    echo 创建LOF急涨急跌监控代码文件...
    echo # 在此添加需要监控急涨急跌的LOF代码，一行一个 > data\lof_speed_codes.txt
    echo # 示例: >> data\lof_speed_codes.txt
    echo # 161725 >> data\lof_speed_codes.txt
)

echo.
echo 所有文件准备就绪
echo.
echo 启动Docker容器...
echo.

REM 停止并删除旧容器
docker-compose down

REM 构建并启动
docker-compose up -d --build

echo.
echo ==================================
echo 容器已启动
echo.
echo 查看日志:
echo   docker-compose logs -f
echo.
echo 停止容器:
echo   docker-compose down
echo.
echo 重启容器:
echo   docker-compose restart
echo ==================================
pause
