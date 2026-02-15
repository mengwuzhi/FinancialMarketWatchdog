#!/usr/bin/env python3
"""
基础连接测试 - 不使用外部依赖
使用urllib测试网络连接
"""

import urllib.request
import urllib.error
import socket
import time
import json
from datetime import datetime
from typing import Dict, List

def test_url_connection(name: str, url: str, timeout: int = 5) -> Dict:
    """测试URL连接"""
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
        # 设置请求头，模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        req = urllib.request.Request(url, headers=headers)
        start_time = time.time()
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result["response_time"] = time.time() - start_time
            result["status_code"] = response.getcode()
            
            if response.getcode() == 200:
                result["status"] = "success"
                # 读取部分内容确认连接正常
                content = response.read(100)  # 只读前100字节
                result["data"] = {
                    "content_length": len(content),
                    "content_type": response.headers.get('Content-Type', 'unknown')
                }
            else:
                result["status"] = f"error: HTTP {response.getcode()}"
                
    except urllib.error.HTTPError as e:
        result["status"] = f"error: HTTP {e.code}"
        result["status_code"] = e.code
        result["error"] = str(e.reason)
    except urllib.error.URLError as e:
        result["status"] = "url_error"
        result["error"] = str(e.reason)
    except socket.timeout:
        result["status"] = "timeout"
        result["error"] = "连接超时"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def test_dns_resolution(hostname: str) -> Dict:
    """测试DNS解析"""
    print(f"测试DNS解析 {hostname}...")
    
    result = {
        "name": f"DNS解析: {hostname}",
        "hostname": hostname,
        "status": "unknown",
        "ip_addresses": [],
        "error": None
    }
    
    try:
        start_time = time.time()
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
        result["response_time"] = time.time() - start_time
        result["ip_addresses"] = ip_addresses
        result["status"] = "success"
    except socket.gaierror as e:
        result["status"] = "dns_error"
        result["error"] = str(e)
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def test_port_connection(hostname: str, port: int) -> Dict:
    """测试端口连接"""
    print(f"测试端口连接 {hostname}:{port}...")
    
    result = {
        "name": f"端口连接: {hostname}:{port}",
        "hostname": hostname,
        "port": port,
        "status": "unknown",
        "response_time": 0,
        "error": None
    }
    
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((hostname, port))
        result["response_time"] = time.time() - start_time
        result["status"] = "success"
        sock.close()
    except socket.timeout:
        result["status"] = "timeout"
        result["error"] = "连接超时"
    except ConnectionRefusedError:
        result["status"] = "connection_refused"
        result["error"] = "连接被拒绝"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def main():
    """主测试函数"""
    print("=" * 60)
    print("基础网络连接测试")
    print("=" * 60)
    
    all_results = []
    
    # 测试DNS解析
    dns_hosts = [
        "www.alphavantage.co",
        "query1.finance.yahoo.com",
        "rss.sina.com.cn",
        "www.stcn.com",
        "github.com"
    ]
    
    for host in dns_hosts:
        result = test_dns_resolution(host)
        all_results.append(result)
    
    # 测试URL连接
    url_tests = [
        {"name": "Alpha Vantage API", "url": "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey=demo"},
        {"name": "Yahoo Finance", "url": "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1m"},
        {"name": "GitHub API", "url": "https://api.github.com"},
        {"name": "公共API测试", "url": "https://httpbin.org/get"}
    ]
    
    for test in url_tests:
        result = test_url_connection(test["name"], test["url"])
        all_results.append(result)
    
    # 测试常用端口
    port_tests = [
        {"hostname": "www.baidu.com", "port": 80},
        {"hostname": "www.google.com", "port": 443},
        {"hostname": "8.8.8.8", "port": 53}  # Google DNS
    ]
    
    for test in port_tests:
        result = test_port_connection(test["hostname"], test["port"])
        all_results.append(result)
    
    # 打印结果汇总
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    successful = sum(1 for r in all_results if r["status"] == "success")
    total = len(all_results)
    
    print(f"总测试数: {total}")
    print(f"成功: {successful}")
    print(f"失败: {total - successful}")
    
    # 按类别统计
    dns_tests = [r for r in all_results if "DNS解析" in r["name"]]
    url_tests = [r for r in all_results if "API" in r["name"] or "Finance" in r["name"] or "GitHub" in r["name"] or "公共API" in r["name"]]
    port_tests = [r for r in all_results if "端口连接" in r["name"]]
    
    print(f"\n分类统计:")
    print(f"  DNS解析测试: {len([r for r in dns_tests if r['status'] == 'success'])}/{len(dns_tests)} 成功")
    print(f"  URL连接测试: {len([r for r in url_tests if r['status'] == 'success'])}/{len(url_tests)} 成功")
    print(f"  端口连接测试: {len([r for r in port_tests if r['status'] == 'success'])}/{len(port_tests)} 成功")
    
    # 详细结果
    print("\n详细结果:")
    for result in all_results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"\n{status_icon} {result['name']}: {result['status']}")
        
        if "response_time" in result and result["response_time"]:
            print(f"  响应时间: {result['response_time']:.3f}秒")
        
        if "ip_addresses" in result and result["ip_addresses"]:
            print(f"  IP地址: {', '.join(result['ip_addresses'][:3])}")
        
        if "status_code" in result and result["status_code"]:
            print(f"  HTTP状态码: {result['status_code']}")
        
        if result["error"]:
            print(f"  错误: {result['error']}")
    
    # 保存结果
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total,
        "successful": successful,
        "network_status": "good" if successful >= total * 0.8 else "fair" if successful >= total * 0.5 else "poor",
        "results": all_results
    }
    
    with open("test/basic_connection_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细结果已保存到: test/basic_connection_results.json")
    
    # 网络状态评估
    print("\n" + "=" * 60)
    print("网络状态评估:")
    print("=" * 60)
    
    if output["network_status"] == "good":
        print("✅ 网络连接状态良好")
        print("   所有外部API应该可以正常访问")
        print("   建议: 可以正常进行开发和测试")
    elif output["network_status"] == "fair":
        print("⚠️  网络连接状态一般")
        print("   部分外部API可能无法访问")
        print("   建议:")
        print("   1. 检查防火墙设置")
        print("   2. 某些API可能需要VPN访问")
        print("   3. 可以使用本地模拟数据进行开发")
    else:
        print("❌ 网络连接状态较差")
        print("   大部分外部API无法访问")
        print("   建议:")
        print("   1. 检查网络连接")
        print("   2. 配置代理服务器")
        print("   3. 使用离线模式或本地数据")
    
    # 项目特定建议
    print("\n" + "=" * 60)
    print("项目特定建议:")
    print("=" * 60)
    
    # 检查关键API
    critical_apis = [
        {"name": "Alpha Vantage", "url": "www.alphavantage.co"},
        {"name": "Yahoo Finance", "url": "query1.finance.yahoo.com"},
        {"name": "RSS源", "url": "rss.sina.com.cn"}
    ]
    
    print("关键外部服务状态:")
    for api in critical_apis:
        # 查找对应的测试结果
        api_results = [r for r in all_results if api["url"] in str(r.get("url", "")) or api["url"] in str(r.get("hostname", ""))]
        if api_results:
            status = "✅ 正常" if any(r["status"] == "success" for r in api_results) else "❌ 异常"
            print(f"  {api['name']}: {status}")
        else:
            print(f"  {api['name']}: ⚠️  未测试")
    
    print("\n开发建议:")
    if output["network_status"] == "good":
        print("  1. 可以直接使用真实外部API进行开发")
        print("  2. 建议配置API密钥以获得完整功能")
        print("  3. 可以启用所有数据采集任务")
    else:
        print("  1. 建议使用模拟数据进行开发")
        print("  2. 可以配置本地数据源")
        print("  3. 部分功能可能需要网络恢复后才能测试")
    
    return 0 if output["network_status"] in ["good", "fair"] else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)