#!/usr/bin/env python3
"""
无依赖测试套件 - 只使用Python标准库
测试FinancialMarketWatchdog项目的基本功能
"""

import os
import sys
import json
import inspect
import ast
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

class NoDependencyTester:
    """无依赖测试器 - 只使用标准库"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = []
        
    def test_project_structure(self) -> Dict:
        """测试项目结构"""
        result = {
            "name": "项目结构测试",
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        required_dirs = [
            "app",
            "app/api",
            "app/api/v1",
            "app/models",
            "app/schemas",
            "app/services",
            "test"
        ]
        
        required_files = [
            "requirements.txt",
            "README.md",
            "app/main.py",
            "app/config.py",
            "app/__init__.py",
            "app/api/v1/__init__.py",
            "app/api/v1/auth.py",
            "app/api/v1/market.py"
        ]
        
        # 检查目录
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists() and full_path.is_dir():
                result["details"][f"目录: {dir_path}"] = "✅ 存在"
            else:
                result["details"][f"目录: {dir_path}"] = "❌ 缺失"
                result["errors"].append(f"目录缺失: {dir_path}")
        
        # 检查文件
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists() and full_path.is_file():
                result["details"][f"文件: {file_path}"] = "✅ 存在"
            else:
                result["details"][f"文件: {file_path}"] = "❌ 缺失"
                result["errors"].append(f"文件缺失: {file_path}")
        
        if not result["errors"]:
            result["status"] = "success"
        else:
            result["status"] = "failed"
        
        return result
    
    def test_python_syntax(self) -> Dict:
        """测试Python文件语法"""
        result = {
            "name": "Python语法测试",
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        # 查找所有Python文件
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 使用ast检查语法
                ast.parse(content)
                result["details"][str(py_file.relative_to(self.project_root))] = "✅ 语法正确"
                
            except SyntaxError as e:
                error_msg = f"第{e.lineno}行: {e.msg}"
                result["details"][str(py_file.relative_to(self.project_root))] = f"❌ 语法错误: {error_msg}"
                result["errors"].append(f"{py_file}: {error_msg}")
            except Exception as e:
                result["details"][str(py_file.relative_to(self.project_root))] = f"❌ 读取错误: {str(e)}"
                result["errors"].append(f"{py_file}: {str(e)}")
        
        if not result["errors"]:
            result["status"] = "success"
        else:
            result["status"] = "failed"
        
        return result
    
    def test_import_statements(self) -> Dict:
        """测试导入语句"""
        result = {
            "name": "导入语句测试",
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        # 项目允许的导入
        allowed_imports = {
            "fastapi", "uvicorn", "sqlalchemy", "pymysql", "alembic",
            "pydantic", "pydantic_settings", "celery", "redis", "flower",
            "pandas", "numpy", "feedparser", "psutil", "python_jose",
            "passlib", "httpx", "python_dotenv", "loguru", "pytest",
            "pytest_asyncio", "pytest_cov", "black", "isort", "mypy",
            "matplotlib", "seaborn", "email_validator", "websockets"
        }
        
        # 标准库导入总是允许的
        standard_libs = {
            "os", "sys", "json", "datetime", "typing", "pathlib", 
            "re", "inspect", "ast", "collections", "itertools",
            "functools", "math", "random", "statistics", "hashlib",
            "base64", "time", "calendar", "decimal", "fractions",
            "urllib", "urllib.parse", "urllib.request", "socket",
            "ssl", "email", "smtplib", "csv", "xml", "html", "sqlite3",
            "contextlib", "platform", "secrets", "string", "logging",
            "asyncio"
        }
        
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            # 跳过测试目录的文件（测试文件可能有额外的依赖）
            if "test" in str(py_file.relative_to(self.project_root)):
                result["details"][str(py_file.relative_to(self.project_root))] = "⏭️ 测试文件（跳过导入检查）"
                continue
                
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 解析导入语句
                tree = ast.parse(content)
                imports = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                
                # 检查导入
                for imp in imports:
                    # 跳过项目内部的相对导入（以app.开头的）
                    if imp.startswith("app."):
                        result["details"][f"{py_file.name}: {imp}"] = "✅ 项目内部导入"
                        continue
                        
                    # 检查是否在requirements.txt中
                    if imp.split(".")[0] not in allowed_imports and imp.split(".")[0] not in standard_libs:
                        result["errors"].append(f"{py_file}: 未声明的导入: {imp}")
                        result["details"][f"{py_file.name}: {imp}"] = "❌ 未声明的导入"
                    else:
                        result["details"][f"{py_file.name}: {imp}"] = "✅ 允许的导入"
                        
            except Exception as e:
                result["errors"].append(f"{py_file}: 解析错误: {str(e)}")
        
        if not result["errors"]:
            result["status"] = "success"
        else:
            result["status"] = "failed"
        
        return result
    
    def test_api_endpoints(self) -> Dict:
        """测试API端点定义"""
        result = {
            "name": "API端点测试",
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        api_files = [
            self.project_root / "app" / "api" / "v1" / "auth.py",
            self.project_root / "app" / "api" / "v1" / "market.py"
        ]
        
        for api_file in api_files:
            if not api_file.exists():
                result["errors"].append(f"API文件不存在: {api_file}")
                continue
            
            try:
                with open(api_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 查找FastAPI路由装饰器
                routes = re.findall(r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content)
                
                if routes:
                    for method, path in routes:
                        endpoint_info = f"{method.upper()} {path}"
                        result["details"][f"{api_file.name}: {endpoint_info}"] = "✅ 定义正确"
                else:
                    result["details"][api_file.name] = "⚠️ 未找到路由定义"
                    
            except Exception as e:
                result["errors"].append(f"{api_file}: 读取错误: {str(e)}")
        
        if not result["errors"]:
            result["status"] = "success"
        else:
            result["status"] = "failed"
        
        return result
    
    def test_config_files(self) -> Dict:
        """测试配置文件"""
        result = {
            "name": "配置文件测试",
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        config_files = [
            self.project_root / ".env.example",
            self.project_root / "app" / "config.py"
        ]
        
        for config_file in config_files:
            if not config_file.exists():
                result["errors"].append(f"配置文件不存在: {config_file}")
                result["details"][str(config_file.relative_to(self.project_root))] = "❌ 缺失"
                continue
            
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                file_size = len(content)
                result["details"][str(config_file.relative_to(self.project_root))] = f"✅ 存在 ({file_size} 字节)"
                
                # 检查.env.example是否有必要的变量
                if config_file.name == ".env.example":
                    required_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
                    for var in required_vars:
                        if var in content:
                            result["details"][f"变量: {var}"] = "✅ 已定义"
                        else:
                            result["details"][f"变量: {var}"] = "⚠️ 未定义"
                            
            except Exception as e:
                result["errors"].append(f"{config_file}: 读取错误: {str(e)}")
        
        if not result["errors"]:
            result["status"] = "success"
        else:
            result["status"] = "failed"
        
        return result
    
    def test_documentation(self) -> Dict:
        """测试文档文件"""
        result = {
            "name": "文档测试",
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        doc_files = [
            self.project_root / "README.md",
            self.project_root / "API_DOCUMENTATION_V2.md",
            self.project_root / "TEST_CASES.md"
        ]
        
        for doc_file in doc_files:
            if not doc_file.exists():
                result["details"][str(doc_file.relative_to(self.project_root))] = "❌ 缺失"
                if doc_file.name == "README.md":
                    result["errors"].append("README.md文件缺失")
                continue
            
            try:
                with open(doc_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                file_size = len(content)
                line_count = content.count('\n') + 1
                
                # 检查文档内容
                if doc_file.name == "README.md":
                    checks = [
                        ("项目标题", bool(re.search(r'#\s+.+', content))),
                        ("项目描述", bool(re.search(r'##\s+简介|##\s+描述', content, re.IGNORECASE))),
                        ("安装说明", bool(re.search(r'##\s+安装|##\s+快速开始', content, re.IGNORECASE))),
                        ("使用示例", bool(re.search(r'```(bash|python|json)', content)))
                    ]
                    
                    for check_name, check_passed in checks:
                        if check_passed:
                            result["details"][f"README: {check_name}"] = "✅ 完整"
                        else:
                            result["details"][f"README: {check_name}"] = "⚠️ 不完整"
                
                result["details"][str(doc_file.relative_to(self.project_root))] = f"✅ 存在 ({line_count} 行, {file_size} 字节)"
                
            except Exception as e:
                result["errors"].append(f"{doc_file}: 读取错误: {str(e)}")
        
        if not result["errors"]:
            result["status"] = "success"
        else:
            result["status"] = "failed"
        
        return result
    
    def run_all_tests(self) -> List[Dict]:
        """运行所有测试"""
        print("=" * 60)
        print("FinancialMarketWatchdog 无依赖测试套件")
        print("=" * 60)
        print(f"项目路径: {self.project_root}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        tests = [
            self.test_project_structure,
            self.test_python_syntax,
            self.test_import_statements,
            self.test_api_endpoints,
            self.test_config_files,
            self.test_documentation
        ]
        
        all_results = []
        
        for test_func in tests:
            print(f"运行测试: {test_func.__name__.replace('test_', '').replace('_', ' ').title()}...")
            result = test_func()
            all_results.append(result)
            
            # 打印结果
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"  {status_icon} {result['name']}: {result['status']}")
            
            if result.get("errors"):
                for error in result["errors"][:3]:  # 只显示前3个错误
                    print(f"    - {error}")
                if len(result["errors"]) > 3:
                    print(f"    - ... 还有 {len(result['errors']) - 3} 个错误")
        
        return all_results
    
    def generate_report(self, results: List[Dict]) -> Dict:
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("测试报告汇总")
        print("=" * 60)
        
        total_tests = len(results)
        successful = sum(1 for r in results if r["status"] == "success")
        failed = total_tests - successful
        
        print(f"总测试数: {total_tests}")
        print(f"成功: {successful}")
        print(f"失败: {failed}")
        print(f"通过率: {successful/total_tests*100:.1f}%")
        
        # 详细结果
        print("\n详细结果:")
        for result in results:
            print(f"\n{result['name']}:")
            for key, value in result.get("details", {}).items():
                if "✅" in value or "❌" in value or "⚠️" in value:
                    print(f"  {key}: {value}")
        
        # 汇总报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "project": str(self.project_root),
            "total_tests": total_tests,
            "successful": successful,
            "failed": failed,
            "success_rate": successful/total_tests*100,
            "results": results,
            "summary": "所有测试通过" if failed == 0 else f"{failed} 个测试失败"
        }
        
        # 保存报告
        report_file = self.project_root / "test" / "no_dependency_test_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")
        
        # 给出建议
        if failed == 0:
            print("\n✅ 所有无依赖测试通过！")
            print("   项目结构完整，代码语法正确，文档齐全")
        else:
            print("\n⚠️  部分测试失败")
            print("   建议:")
            print("   1. 修复缺失的文件或目录")
            print("   2. 修复Python语法错误")
            print("   3. 完善项目文档")
        
        return report

def main():
    """主函数"""
    project_root = "/home/openclaw/.openclaw/workspace/code_projects/FinancialMarketWatchdog/financial_watchdog_web"
    
    if not os.path.exists(project_root):
        print(f"错误: 项目目录不存在: {project_root}")
        return 1
    
    tester = NoDependencyTester(project_root)
    results = tester.run_all_tests()
    report = tester.generate_report(results)
    
    # 返回退出码
    return 0 if report["failed"] == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)