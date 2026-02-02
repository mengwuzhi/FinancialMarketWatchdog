# db/configs.py
"""
数据库配置管理模块
支持运行时动态配置数据库连接参数
"""
import logging

logger = logging.getLogger(__name__)

# 全局默认数据库配置
_DB_CONFIG = {
    'host': '47.95.221.184',
    'port': 18453,
    'user': 'root',
    'password': 'RLCs9.Y3.mSG3@',
    'database': 'watchdog_db',
    'charset': 'utf8mb4',
    'autocommit': False,
}

# 全局默认连接池配置
_DB_POOL_CONFIG = {
    'maxconnections': 10,  # 最大连接数
    'mincached': 2,        # 初始化时，连接池中至少创建的空闲的连接
    'maxcached': 5,        # 连接池中最多闲置的连接
    'blocking': True,      # 连接池中如果没有可用连接，是否阻塞等待
    'maxusage': None,      # 单个连接的最大重复使用次数
    'setsession': [],      # 开始会话前执行的命令列表
    'ping': 1,             # ping MySQL服务端，检查服务是否可用（0=不检查，1=默认检查，2=事务前检查）
}


def set_db_config(db_config=None, pool_config=None):
    """
    设置数据库配置（运行时动态配置）

    Args:
        db_config: 数据库连接配置字典，如 {'host': '127.0.0.1', 'port': 3306, ...}
        pool_config: 连接池配置字典，如 {'maxconnections': 20, ...}

    Example:
        >>> set_db_config(
        ...     db_config={'host': '127.0.0.1', 'database': 'mydb'},
        ...     pool_config={'maxconnections': 20}
        ... )
    """
    global _DB_CONFIG, _DB_POOL_CONFIG

    if db_config:
        logger.info(f"更新数据库配置: {db_config}")
        _DB_CONFIG.update(db_config)

    if pool_config:
        logger.info(f"更新连接池配置: {pool_config}")
        _DB_POOL_CONFIG.update(pool_config)


def get_db_config():
    """
    获取当前数据库配置（返回副本，避免外部修改）

    Returns:
        dict: 数据库配置字典
    """
    return _DB_CONFIG.copy()


def get_pool_config():
    """
    获取当前连接池配置（返回副本，避免外部修改）

    Returns:
        dict: 连接池配置字典
    """
    return _DB_POOL_CONFIG.copy()


def reset_config():
    """
    重置配置为默认值（用于测试或重新初始化）
    """
    global _DB_CONFIG, _DB_POOL_CONFIG

    _DB_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '',
        'database': 'lof_watchdog',
        'charset': 'utf8mb4',
        'autocommit': False,
    }

    _DB_POOL_CONFIG = {
        'maxconnections': 10,
        'mincached': 2,
        'maxcached': 5,
        'blocking': True,
        'maxusage': None,
        'setsession': [],
        'ping': 1,
    }

    logger.info("数据库配置已重置为默认值")
