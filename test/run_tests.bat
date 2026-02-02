@echo off
REM 测试运行脚本 - Windows版本
REM 解决Unicode编码问题

echo ==================================
echo 投资监控系统 - 测试套件
echo ==================================
echo.

REM 设置UTF-8编码
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8

echo 开始测试...
echo.

REM 切换到项目根目录
cd /d "%~dp0\.."

echo [1/3] 快速配置测试...
python test/quick_test.py
if errorlevel 1 (
    echo.
    echo 快速测试失败，请修复后继续
    pause
    exit /b 1
)

echo.
echo [2/3] 离线功能测试...
python test/test_offline.py
if errorlevel 1 (
    echo.
    echo 离线测试失败，请修复后继续
    pause
    exit /b 1
)

echo.
echo [3/3] 完整测试套件...
python test/test_suite.py

echo.
echo ==================================
echo 测试完成！
echo ==================================
pause
