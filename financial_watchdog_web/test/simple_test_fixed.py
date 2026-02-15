#!/usr/bin/env python3
"""
简单测试脚本 - 使用Python标准库测试外部API连接（修复版）
"""

import urllib.request
import urllib.error
import socket
import time
import json
from datetime import datetime
from typing import Dict, List

def test_api_connection(name: str, url: str, method: str = "GET", 
                       params: Dict = None, headers: Dict = None, 
                       timeout: int = 5) -> Dict:
    """测试API连接（使用标准库）"""
    print(f"测试 {name}...")
    
    result = {
        "name": name,
        "url": url,
        "status": "unknown",
        "response_time": 0,
        "status_code": None,
        "error": None
    }
    
    # 在函数开头导入所有需要的模块
    import urllib.parse
    import urllib.request
    import urllib.error
    
    try:
        # 构建请求URL
        full_url = url
        if params and method.upper() == "GET":
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
        
        # 创建请求
        req = urllib.request.Request(full_url, method=method.upper())
        
        # 添加headers
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        
        # 设置超时
        socket.setdefaulttimeout(timeout)
        
        # 发送请求
        start_time = time.time()
        try:
            response = urllib.request.urlopen(req)
            result["response_time"] = time.time() - start_time
            result["status_code"] = response.getcode()
            
            if result["status_code"] == 200:
                result["status"] = "success"
                try:
                    # 尝试读取响应内容
                    content = response.read().decode('utf-8')
                    # 尝试解析JSON
                    data = json.loads(content)
                    result["data"] = data
                except json.JSONDecodeError:
                    result["data"] = {"message": "响应不是JSON格式"}
                except UnicodeDecodeError:
                    result["data"] = {"message": "编码错误"}
            else:
                result["status"] = f"error: HTTP {result['status_code']}"
                
        except urllib.error.HTTPError as e:
            result["response_time"] = time.time() - start_time
            result["status_code"] = e.code
            result["status"] = f"error: HTTP {e.code}"
            result["error"] = str(e)
            
    except urllib.error.URLError as e:
        result["status"] = "connection_error"
        result["error"] = str(e.reason) if hasattr(e, 'reason') else str(e)
    except socket.timeout:
        result["status"] = "timeout"
        result["error"] = "请求超时"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("外部API连接测试 (使用Python标准库)")
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
        }
    ]
    
    # 运行所有测试
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
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        response_time = result.get("response_time", 0)
        print(f"{status_icon} {result['name']}: {result['status']} ({response_time:.3f}s)")
    
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
        if result.get("response_time"):
            print(f"  响应时间: {result['response_time']:.3f}秒")
        if result.get("status_code"):
            print(f"  状态码: {result['status_code']}")
        
        if result.get("error"):
            print(f"  错误: {result['error']}")
    
    # 保存结果
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total,
        "successful": successful,
        "results": results
    }
    
    with open("test/simple_test_fixed_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细结果已保存到: test/simple_test_fixed_results.json")
    
    # 给出建议
    if successful == total:
        print("\n✅ 所有外部API连接测试通过！")
        return 0
    elif successful >= total * 0.5:
        print("\n⚠️  部分外部API连接正常，部分可能需要配置或网络访问")
        print("   建议:")
        print("   1. 检查网络连接")
        print("   2. 某些API可能需要VPN访问")
        print("   3. 某些RSS源可能已失效")
        return 1
    else:
        print("\n❌ 多个外部API连接失败")
        print("   可能原因:")
        print("   1. 网络连接问题")
        print("   2. 防火墙限制")
        print("   3. API服务暂时不可用")
        return 2

def main():
    """主函数"""
    try:
        exit_code = run_tests()
        return exit_code
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 3

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)