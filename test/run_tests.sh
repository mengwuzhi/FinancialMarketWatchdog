#!/bin/bash
# 测试运行脚本 - Linux/Mac版本

echo "=================================="
echo "投资监控系统 - 测试套件"
echo "=================================="
echo ""

# 切换到项目根目录
cd "$(dirname "$0")/.."

echo "开始测试..."
echo ""

echo "[1/3] 快速配置测试..."
python test/quick_test.py
if [ $? -ne 0 ]; then
    echo ""
    echo "快速测试失败，请修复后继续"
    exit 1
fi

echo ""
echo "[2/3] 离线功能测试..."
python test/test_offline.py
if [ $? -ne 0 ]; then
    echo ""
    echo "离线测试失败，请修复后继续"
    exit 1
fi

echo ""
echo "[3/3] 完整测试套件..."
python test/test_suite.py

echo ""
echo "=================================="
echo "测试完成！"
echo "=================================="
