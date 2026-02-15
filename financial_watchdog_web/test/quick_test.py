#!/usr/bin/env python3
"""
快速测试脚本 - 测试外部API连接
"""

import requests
import time
import json
from datetime import datetime

def test_api_connection(name, url, method="GET", params=None, headers=None, timeout=5):
    """测试API连接"""
    print(f"测试 {name}...")
    
    result = {
        "name": name,
        "url": url,
        "status": "unknown",
        "response_time": 0,
        "status_code": None,
        "error": None
    }
    
    try:
        start_time = time.time()
        
        if method.upper() == "GET":
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=params, headers=headers, timeout=timeout)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        result["response_time"] = time.time() - start_time
        result["status_code"] = response.status_code
        
        if response.status_code == 200:
            result["status"] = "success"
            try:
                # 尝试解析JSON响应
                data = response.json()
                result["data"] = data
            except:
                result["data"] = {"message": "响应不是JSON格式"}
        else:
            result["status"] = f"error: HTTP {response.status_code}"
            result["error"] = response.text[:100]  # 只取前100个字符
            
    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["error"] = "请求超时"
    except requests.exceptions.ConnectionError:
        result["status"] = "connection_error"
        result["error"] = "连接错误"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def main():
    """主测试函数"""
    print("=" * 60)
    print("快速外部API连接测试")
    print("=" * 60)
    
    # 定义要测试的API
    tests = [
        {
            "name": "Alpha Vantage (股票数据)",
            "url": "https://www.alphavantage.co/query",
            "params": {
                "function": "TIME_SERIES_DAILY",
                "symbol": "IBM",
                "apikey": "demo",
                "outputsize": "compact"
            }
        },
        {
            "name": "Yahoo Finance (市场数据)",
            "url": "https://query1.finance.yahoo.com/v8/finance/chart/AAPL",
            "params": {
                "range": "1d",
                "interval": "1m"
            }
        },
        {
            "name": "新浪财经RSS",
            "url": "https://rss.sina.com.cn/finance/news/global.xml"
        },
        {
            "name": "证券时报RSS",
            "url": "http://www.stcn.com/rss/finance.xml"
        },
        {
            "name": "CoinMarketCap (加密货币)",
            "url": "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
            "headers": {
                "X-CMC_PRO_API_KEY": "demo"  # 演示用
            }
        }
    ]
    
    results = []
    
    for test in tests:
        result = test_api_connection(
            name=test["name"],
            url=test["url"],
            params=test.get("params"),
            headers=test.get("headers")
        )
        results.append(result)
        
        # 打印结果
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {result['name']}: {result['status']} ({result['response_time']:.3f}s)")
    
    # 汇总统计
    print("\n" + "=" * 60)
    print("测试汇总:")
    print("=" * 60)
    
    successful = sum(1 for r in results if r["status"] == "success")
    total = len(results)
    
    print(f"总测试数: {total}")
    print(f"成功: {successful}")
    print(f"失败: {total - successful}")
    
    # 详细结果
    print("\n详细结果:")
    for result in results:
        print(f"\n{result['name']}:")
        print(f"  URL: {result['url']}")
        print(f"  状态: {result['status']}")
        print(f"  响应时间: {result['response_time']:.3f}秒")
        print(f"  状态码: {result['status_code']}")
        
        if result["error"]:
            print(f"  错误: {result['error']}")
    
    # 保存结果
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total,
        "successful": successful,
        "results": results
    }
    
    with open("test/quick_test_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细结果已保存到: test/quick_test_results.json")
    
    # 给出建议
    if successful == total:
        print("\n✅ 所有外部API连接测试通过！")
    elif successful >= total * 0.7:
        print("\n⚠️  大部分外部API连接正常，部分可能需要配置API密钥")
    else:
        print("\n❌ 多个外部API连接失败，请检查网络连接和API配置")
    
    return 0 if successful >= total * 0.7 else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)