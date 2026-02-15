#!/usr/bin/env python3
"""
外部数据接口测试脚本
测试项目依赖的外部API是否可用
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ExternalAPITester:
    """外部API测试器"""
    
    def __init__(self):
        self.results = {}
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_alpha_vantage(self) -> Dict:
        """测试Alpha Vantage API（股票数据）"""
        result = {
            "name": "Alpha Vantage",
            "status": "unknown",
            "response_time": 0,
            "data": None,
            "error": None
        }
        
        # 测试用的API密钥（公开的演示密钥）
        api_key = "demo"  # 实际使用时应从环境变量获取
        symbol = "IBM"
        
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": api_key,
            "outputsize": "compact"
        }
        
        try:
            start_time = time.time()
            async with self.session.get(url, params=params, timeout=10) as response:
                result["response_time"] = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    if "Time Series (Daily)" in data:
                        result["status"] = "success"
                        result["data"] = {
                            "symbol": symbol,
                            "latest_date": list(data["Time Series (Daily)"].keys())[0],
                            "data_points": len(data["Time Series (Daily)"])
                        }
                    else:
                        result["status"] = "error"
                        result["error"] = data.get("Note", "API返回数据格式异常")
                else:
                    result["status"] = "error"
                    result["error"] = f"HTTP {response.status}: {await response.text()}"
                    
        except asyncio.TimeoutError:
            result["status"] = "timeout"
            result["error"] = "请求超时"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            
        return result
    
    async def test_coinmarketcap(self) -> Dict:
        """测试CoinMarketCap API（加密货币数据）"""
        result = {
            "name": "CoinMarketCap",
            "status": "unknown",
            "response_time": 0,
            "data": None,
            "error": None
        }
        
        # 注意：CoinMarketCap需要API密钥，这里只测试连接
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        
        try:
            start_time = time.time()
            async with self.session.get(url, timeout=10) as response:
                result["response_time"] = time.time() - start_time
                
                if response.status == 200:
                    result["status"] = "success"
                    result["data"] = {"message": "API端点可访问"}
                elif response.status == 401:
                    result["status"] = "unauthorized"
                    result["error"] = "需要有效的API密钥"
                else:
                    result["status"] = "error"
                    result["error"] = f"HTTP {response.status}"
                    
        except asyncio.TimeoutError:
            result["status"] = "timeout"
            result["error"] = "请求超时"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            
        return result
    
    async def test_yahoo_finance(self) -> Dict:
        """测试Yahoo Finance API（市场数据）"""
        result = {
            "name": "Yahoo Finance",
            "status": "unknown",
            "response_time": 0,
            "data": None,
            "error": None
        }
        
        symbol = "AAPL"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "range": "1d",
            "interval": "1m"
        }
        
        try:
            start_time = time.time()
            async with self.session.get(url, params=params, timeout=10) as response:
                result["response_time"] = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    if "chart" in data and "result" in data["chart"]:
                        result["status"] = "success"
                        result["data"] = {
                            "symbol": symbol,
                            "has_data": len(data["chart"]["result"]) > 0
                        }
                    else:
                        result["status"] = "success"
                        result["data"] = {"message": "API响应正常"}
                else:
                    result["status"] = "error"
                    result["error"] = f"HTTP {response.status}"
                    
        except asyncio.TimeoutError:
            result["status"] = "timeout"
            result["error"] = "请求超时"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            
        return result
    
    async def test_rss_feeds(self) -> Dict:
        """测试RSS源"""
        result = {
            "name": "RSS Feeds",
            "status": "unknown",
            "response_time": 0,
            "feeds": [],
            "error": None
        }
        
        feeds = [
            {"name": "新浪财经", "url": "https://rss.sina.com.cn/finance/news/global.xml"},
            {"name": "证券时报", "url": "http://www.stcn.com/rss/finance.xml"},
            {"name": "Reuters Business", "url": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"},
        ]
        
        successful_feeds = []
        
        for feed in feeds:
            try:
                start_time = time.time()
                async with self.session.get(feed["url"], timeout=10) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        successful_feeds.append({
                            "name": feed["name"],
                            "url": feed["url"],
                            "status": "success",
                            "response_time": response_time
                        })
                    else:
                        successful_feeds.append({
                            "name": feed["name"],
                            "url": feed["url"],
                            "status": f"error: HTTP {response.status}",
                            "response_time": response_time
                        })
                        
            except Exception as e:
                successful_feeds.append({
                    "name": feed["name"],
                    "url": feed["url"],
                    "status": f"error: {str(e)}",
                    "response_time": 0
                })
        
        if any(f["status"] == "success" for f in successful_feeds):
            result["status"] = "partial_success"
        elif any("error" in f["status"] for f in successful_feeds):
            result["status"] = "partial_failure"
        else:
            result["status"] = "unknown"
            
        result["feeds"] = successful_feeds
        result["response_time"] = sum(f["response_time"] for f in successful_feeds) / max(len(successful_feeds), 1)
        
        return result
    
    async def test_futures_data(self) -> Dict:
        """测试期货数据API"""
        result = {
            "name": "Futures Data",
            "status": "unknown",
            "response_time": 0,
            "data": None,
            "error": None
        }
        
        # 测试中金所数据（示例）
        url = "https://www.cffex.com.cn/sj/hqsj/rtj/20240215/index.xml"
        
        try:
            start_time = time.time()
            async with self.session.get(url, timeout=10) as response:
                result["response_time"] = time.time() - start_time
                
                if response.status == 200:
                    result["status"] = "success"
                    result["data"] = {"message": "期货数据源可访问"}
                else:
                    result["status"] = "error"
                    result["error"] = f"HTTP {response.status}"
                    
        except asyncio.TimeoutError:
            result["status"] = "timeout"
            result["error"] = "请求超时"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            
        return result
    
    async def test_all_apis(self) -> Dict:
        """测试所有外部API"""
        print("开始测试外部数据接口...")
        print("=" * 60)
        
        tests = [
            self.test_alpha_vantage(),
            self.test_coinmarketcap(),
            self.test_yahoo_finance(),
            self.test_rss_feeds(),
            self.test_futures_data()
        ]
        
        results = await asyncio.gather(*tests)
        
        # 汇总结果
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful": 0,
            "failed": 0,
            "partial": 0,
            "details": {}
        }
        
        for result in results:
            name = result["name"]
            summary["details"][name] = result
            
            if result["status"] == "success":
                summary["successful"] += 1
            elif result["status"] in ["partial_success", "partial_failure"]:
                summary["partial"] += 1
            else:
                summary["failed"] += 1
        
        return summary
    
    def print_results(self, summary: Dict):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("外部数据接口测试结果")
        print("=" * 60)
        print(f"测试时间: {summary['timestamp']}")
        print(f"测试总数: {summary['total_tests']}")
        print(f"成功: {summary['successful']}")
        print(f"部分成功: {summary['partial']}")
        print(f"失败: {summary['failed']}")
        print("-" * 60)
        
        for name, result in summary["details"].items():
            print(f"\n{name}:")
            print(f"  状态: {result['status']}")
            print(f"  响应时间: {result['response_time']:.3f}秒")
            
            if result["error"]:
                print(f"  错误: {result['error']}")
            
            if result["data"]:
                print(f"  数据: {json.dumps(result['data'], ensure_ascii=False, indent=2)}")
        
        print("\n" + "=" * 60)
        
        # 保存结果到文件
        output_file = "test/external_api_test_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"详细结果已保存到: {output_file}")
        
        # 给出建议
        if summary["failed"] == 0 and summary["partial"] == 0:
            print("✅ 所有外部API测试通过！")
        elif summary["failed"] > 0:
            print("⚠️  部分外部API测试失败，可能需要配置API密钥或检查网络连接")
        else:
            print("⚠️  部分外部API测试部分成功，建议检查配置")

async def main():
    """主函数"""
    async with ExternalAPITester() as tester:
        summary = await tester.test_all_apis()
        tester.print_results(summary)
        
        # 返回退出码
        if summary["failed"] > 0:
            return 1
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)