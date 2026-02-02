# db/core.py
"""
数据库核心操作模块
提供底层的数据库查询和执行接口
"""
import pymysql
import logging
from contextlib import contextmanager
from typing import Generator, Any, List, Tuple, Union, Callable

from .pool import get_connection
from .exceptions import DBQueryError

logger = logging.getLogger(__name__)


@contextmanager
def _cursor(dict_: bool = True) -> Generator[pymysql.cursors.Cursor, None, None]:
    """
    获取数据库游标的上下文管理器（私有方法）

    Args:
        dict_: 是否返回字典格式结果（True=DictCursor, False=普通Cursor）

    Yields:
        pymysql.cursors.Cursor: 数据库游标对象

    Raises:
        DBQueryError: 数据库操作失败时抛出
    """
    try:
        with get_connection() as conn:
            cursor_cls = pymysql.cursors.DictCursor if dict_ else None
            with conn.cursor(cursor_cls) as cur:
                yield cur
                # 自动提交（读操作无影响，写操作需要提交）
                conn.commit()
    except Exception as e:
        logger.exception("数据库游标上下文错误")
        raise DBQueryError(original_exception=e) from e


def fetch_all(
    sql: str,
    params: Union[Tuple, List, None] = None,
    *,
    dict_: bool = True
) -> List[Any]:
    """
    查询多行记录

    Args:
        sql: SQL 查询语句（支持参数占位符 %s）
        params: SQL 参数元组或列表
        dict_: 是否返回字典格式（True=字典列表，False=元组列表）

    Returns:
        查询结果列表

    Example:
        >>> rows = fetch_all("SELECT * FROM user WHERE age > %s", (18,))
        >>> print(rows)
        [{'id': 1, 'name': 'Alice', 'age': 20}, ...]
    """
    try:
        with _cursor(dict_) as cur:
            cur.execute(sql, params)
            result = cur.fetchall()
            logger.debug(f"查询成功 - SQL: {sql} | params: {params} | 结果数: {len(result)}")
            return result
    except Exception as e:
        logger.error(f"查询失败 - SQL: {sql} | params: {params}")
        raise DBQueryError(sql=sql, params=params, original_exception=e) from e


def fetch_one(
    sql: str,
    params: Union[Tuple, List, None] = None,
    *,
    dict_: bool = True
) -> Union[Any, None]:
    """
    查询单行记录

    Args:
        sql: SQL 查询语句
        params: SQL 参数
        dict_: 是否返回字典格式

    Returns:
        单行结果（字典或元组），无结果返回 None

    Example:
        >>> row = fetch_one("SELECT * FROM user WHERE id = %s", (1,))
        >>> print(row)
        {'id': 1, 'name': 'Alice', 'age': 20}
    """
    try:
        with _cursor(dict_) as cur:
            cur.execute(sql, params)
            result = cur.fetchone()
            logger.debug(f"查询单行成功 - SQL: {sql} | params: {params}")
            return result
    except Exception as e:
        logger.error(f"查询单行失败 - SQL: {sql} | params: {params}")
        raise DBQueryError(sql=sql, params=params, original_exception=e) from e


def execute(
    sql: str,
    params: Union[Tuple, List, None] = None
) -> int:
    """
    执行单条写操作（INSERT / UPDATE / DELETE）

    Args:
        sql: SQL 语句
        params: SQL 参数

    Returns:
        受影响的行数

    Example:
        >>> rows = execute("UPDATE user SET age = %s WHERE id = %s", (25, 1))
        >>> print(f"更新了 {rows} 行")
    """
    try:
        with _cursor(False) as cur:
            rows = cur.execute(sql, params)
            logger.info(f"执行成功 - SQL: {sql} | params: {params} | 影响行数: {rows}")
            return rows
    except Exception as e:
        logger.error(f"执行失败 - SQL: {sql} | params: {params}")
        raise DBQueryError(sql=sql, params=params, original_exception=e) from e


def executemany(
    sql: str,
    params_seq: List[Union[Tuple, List]]
) -> int:
    """
    批量执行写操作

    Args:
        sql: SQL 语句
        params_seq: 参数列表（每个元素是一组参数）

    Returns:
        受影响的总行数

    Example:
        >>> rows = executemany(
        ...     "INSERT INTO user (name, age) VALUES (%s, %s)",
        ...     [("Alice", 20), ("Bob", 25), ("Charlie", 30)]
        ... )
        >>> print(f"插入了 {rows} 行")
    """
    try:
        with _cursor(False) as cur:
            rows = cur.executemany(sql, params_seq)
            logger.info(f"批量执行成功 - SQL: {sql} | 批次数: {len(params_seq)} | 影响行数: {rows}")
            return rows
    except Exception as e:
        logger.error(f"批量执行失败 - SQL: {sql} | 批次数: {len(params_seq)}")
        raise DBQueryError(sql=sql, params=params_seq, original_exception=e) from e


def transaction(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    事务装饰器：将函数包装为一个事务

    Args:
        func: 需要在事务中执行的函数，函数必须接受 conn 参数

    Returns:
        包装后的函数

    Example:
        >>> @transaction
        ... def transfer_money(from_id, to_id, amount, *, conn):
        ...     with conn.cursor() as cur:
        ...         cur.execute("UPDATE wallet SET balance = balance - %s WHERE user_id = %s",
        ...                     (amount, from_id))
        ...         cur.execute("UPDATE wallet SET balance = balance + %s WHERE user_id = %s",
        ...                     (amount, to_id))
        ...
        >>> transfer_money(1, 2, 100)  # 自动在事务中执行
    """
    def wrapper(*args, **kwargs):
        with get_connection() as conn:
            try:
                # 调用原函数，传入 conn 参数
                result = func(*args, **kwargs, conn=conn)
                conn.commit()
                logger.info(f"事务提交成功 - 函数: {func.__name__}")
                return result
            except Exception as e:
                conn.rollback()
                logger.error(f"事务回滚 - 函数: {func.__name__}")
                raise DBQueryError(original_exception=e) from e

    return wrapper
