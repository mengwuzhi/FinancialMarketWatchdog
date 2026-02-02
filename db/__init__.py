# db/__init__.py
"""
数据库操作模块
提供简洁的数据库访问接口

使用示例:
    >>> from db import set_db_config, select_rows, insert_row
    >>>
    >>> # 配置数据库
    >>> set_db_config(db_config={'host': '127.0.0.1', 'database': 'mydb'})
    >>>
    >>> # 查询数据
    >>> users = select_rows("user", ["id", "name"], {"age": (">", 18)})
    >>>
    >>> # 插入数据
    >>> insert_row("user", {"name": "Alice", "age": 20})
"""

# 配置管理
from .configs import (
    set_db_config,
    get_db_config,
    get_pool_config,
    reset_config,
)

# 连接池管理
from .pool import (
    get_connection,
    reset_pool,
    get_pool_status,
)

# 底层数据库操作
from .core import (
    fetch_all,
    fetch_one,
    execute,
    executemany,
    transaction,
)

# DAO 层数据访问
from .dao import (
    Raw,
    select_rows,
    select_one,
    insert_row,
    insert_many,
    update_rows,
    delete_rows,
    count_rows,
    exists,
)

# 异常类
from .exceptions import (
    DBError,
    DBQueryError,
    DBConnectionError,
)

__all__ = [
    # 配置管理
    "set_db_config",
    "get_db_config",
    "get_pool_config",
    "reset_config",
    # 连接池
    "get_connection",
    "reset_pool",
    "get_pool_status",
    # 底层操作
    "fetch_all",
    "fetch_one",
    "execute",
    "executemany",
    "transaction",
    # DAO层
    "Raw",
    "select_rows",
    "select_one",
    "insert_row",
    "insert_many",
    "update_rows",
    "delete_rows",
    "count_rows",
    "exists",
    # 异常
    "DBError",
    "DBQueryError",
    "DBConnectionError",
]
