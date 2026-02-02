# db/pool.py
"""
数据库连接池管理
使用 DBUtils 的 PooledDB 实现线程安全的连接池
"""
import pymysql
import logging
from dbutils.pooled_db import PooledDB
from typing import Optional

from .configs import get_db_config, get_pool_config
from .exceptions import DBConnectionError

logger = logging.getLogger(__name__)

# 全局连接池实例（延迟初始化）
_pool: Optional[PooledDB] = None


def _init_pool():
    """
    初始化数据库连接池（延迟初始化，仅在第一次获取连接时调用）

    Raises:
        DBConnectionError: 连接池初始化失败时抛出
    """
    global _pool

    if _pool is not None:
        return

    try:
        db_config = get_db_config()
        pool_config = get_pool_config()

        logger.info(
            f"初始化数据库连接池 - "
            f"host={db_config.get('host')}:{db_config.get('port')}, "
            f"database={db_config.get('database')}, "
            f"maxconnections={pool_config.get('maxconnections')}"
        )

        _pool = PooledDB(
            creator=pymysql,
            **db_config,
            **pool_config
        )

        logger.info("数据库连接池初始化成功")

    except Exception as e:
        logger.exception("数据库连接池初始化失败")
        raise DBConnectionError(f"连接池初始化失败: {e}") from e


def get_connection():
    """
    从连接池获取一个数据库连接

    Returns:
        pymysql.Connection: 数据库连接对象

    Raises:
        DBConnectionError: 获取连接失败时抛出

    Example:
        >>> with get_connection() as conn:
        ...     with conn.cursor() as cursor:
        ...         cursor.execute("SELECT 1")
        ...         print(cursor.fetchone())
    """
    try:
        # 延迟初始化连接池
        if _pool is None:
            _init_pool()

        return _pool.connection()

    except Exception as e:
        logger.exception("获取数据库连接失败")
        raise DBConnectionError(f"获取连接失败: {e}") from e


def reset_pool():
    """
    重置连接池（用于配置更新后重新初始化）
    注意：调用此方法后，之前获取的连接将失效
    """
    global _pool

    if _pool is not None:
        logger.info("重置数据库连接池")
        # PooledDB 没有显式的 close 方法，直接置为 None 让 GC 回收
        _pool = None


def get_pool_status():
    """
    获取连接池状态信息（用于监控和调试）

    Returns:
        dict: 连接池状态字典，包含当前连接数等信息
    """
    if _pool is None:
        return {
            "initialized": False,
            "message": "连接池未初始化"
        }

    return {
        "initialized": True,
        "message": "连接池已初始化",
        # DBUtils 的 PooledDB 不直接暴露连接数统计
        # 可以通过 _pool._idle_cache 等内部属性查看（不推荐）
    }
