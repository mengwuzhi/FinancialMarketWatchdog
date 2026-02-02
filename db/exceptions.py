# db/exceptions.py
"""
数据库操作异常类定义
"""


class DBError(Exception):
    """
    数据库操作基础异常，所有自定义异常的父类
    """
    def __init__(self, message="发生未知数据库操作异常"):
        super().__init__(message)


class DBQueryError(DBError):
    """
    执行 SQL 失败相关异常，例如语法错误、参数错误
    """
    def __init__(self, sql=None, params=None, original_exception=None):
        message = "SQL 执行失败"
        if sql:
            message += f" | SQL: {sql}"
        if params:
            message += f" | 参数: {params}"
        if original_exception:
            message += f" | 原始错误: {original_exception}"
        super().__init__(message)
        self.sql = sql
        self.params = params
        self.original_exception = original_exception


class DBConnectionError(DBError):
    """
    数据库连接池相关异常，例如连接超时、连接池配置错误
    """
    def __init__(self, message="数据库连接失败"):
        super().__init__(message)
