# db/dao.py
"""
数据访问对象层（DAO）
提供高级的数据库操作接口，支持字典驱动的查询条件
"""
from typing import Any, Dict, List, Tuple, Optional, Union
import re
import logging

from .core import fetch_all, fetch_one, execute, executemany
from .exceptions import DBQueryError

logger = logging.getLogger(__name__)

# 类型别名
RowDict = Dict[str, Any]
RowTuple = Tuple[Any, ...]

# 标识符校验正则
_id_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class Raw:
    """
    原始SQL表达式包装类
    用于在 UPDATE 等操作中插入原始SQL表达式

    Example:
        >>> update_rows("user", {"updated_at": Raw("NOW()")}, {"id": 1})
    """
    def __init__(self, expr: str):
        self.expr = expr


def _id(name: str) -> str:
    """
    SQL标识符转义（防止SQL注入）

    Args:
        name: 列名或表名（支持 a.b.c 样式）

    Returns:
        转义后的标识符（用反引号包裹）

    Raises:
        ValueError: 非法标识符时抛出
    """
    if "." in name:
        parts = name.split(".")
        if not all(_id_re.match(part) for part in parts):
            raise ValueError(f"非法 SQL 标识符: {name}")
        return ".".join(f"`{part}`" for part in parts)

    if not _id_re.match(name):
        raise ValueError(f"非法 SQL 标识符: {name}")

    return f"`{name}`"


def _build_where(filters: Union[Dict[str, Any], None]) -> Tuple[str, List[Any]]:
    """
    构建 WHERE 子句（支持复杂条件）

    支持的操作符：
        - 等于：        {"age": 18}
        - 不等于：      {"status": ("!=", "inactive")}
        - 大小比较：    {"score": (">", 60)}
        - BETWEEN：     {"date": ("BETWEEN", "2024-01-01", "2024-12-31")}
        - LIKE：        {"name": ("LIKE", "%张%")}
        - NOT LIKE：    {"name": ("NOT LIKE", "%测试%")}
        - IS NULL：     {"deleted_at": ("IS", None)}
        - IS NOT NULL： {"updated_at": ("IS NOT", None)}
        - IN：          {"type": ("IN", ["A", "B"])}
        - NOT IN：      {"type": ("NOT IN", ["C", "D"])}
        - OR 组合：     {"OR": [{"name": "Alice"}, {"name": "Bob"}]}

    Args:
        filters: 过滤条件字典

    Returns:
        (where_sql, params): WHERE 子句和参数列表

    Example:
        >>> where_sql, params = _build_where({"age": (">", 18), "status": "active"})
        >>> print(where_sql)
        WHERE `age` > %s AND `status` = %s
        >>> print(params)
        [18, 'active']
    """
    if not filters:
        return "", []

    def parse(filters, logic="AND"):
        if isinstance(filters, list):
            clauses = []
            params = []
            for sub_filter in filters:
                clause, sub_params = parse(sub_filter)
                clauses.append(f"({clause})")
                params.extend(sub_params)
            return f" {logic} ".join(clauses), params

        if isinstance(filters, dict):
            clauses = []
            params = []

            for key, value in filters.items():
                if key.upper() in ("AND", "OR"):
                    clause, sub_params = parse(value, logic=key.upper())
                    clauses.append(f"({clause})")
                    params.extend(sub_params)

                elif isinstance(value, tuple):
                    op = value[0].upper()
                    col_sql = _id(key)

                    if op == "IN":
                        vals = value[1]
                        if not vals:
                            raise ValueError("IN 的值不能为空")
                        placeholders = ", ".join(["%s"] * len(vals))
                        clauses.append(f"{col_sql} IN ({placeholders})")
                        params.extend(vals)

                    elif op == "NOT IN":
                        vals = value[1]
                        if not vals:
                            raise ValueError("NOT IN 的值不能为空")
                        placeholders = ", ".join(["%s"] * len(vals))
                        clauses.append(f"{col_sql} NOT IN ({placeholders})")
                        params.extend(vals)

                    elif op == "LIKE":
                        clauses.append(f"{col_sql} LIKE %s")
                        params.append(value[1])

                    elif op == "NOT LIKE":
                        clauses.append(f"{col_sql} NOT LIKE %s")
                        params.append(value[1])

                    elif op == "BETWEEN":
                        clauses.append(f"{col_sql} BETWEEN %s AND %s")
                        params.extend([value[1], value[2]])

                    elif op == "IS" and value[1] is None:
                        clauses.append(f"{col_sql} IS NULL")

                    elif op == "IS NOT" and value[1] is None:
                        clauses.append(f"{col_sql} IS NOT NULL")

                    elif op in ("=", "!=", "<", ">", "<=", ">=", "<>"):
                        clauses.append(f"{col_sql} {op} %s")
                        params.append(value[1])

                    else:
                        raise ValueError(f"不支持的操作符: {op}")

                else:
                    col_sql = _id(key)
                    clauses.append(f"{col_sql} = %s")
                    params.append(value)

            return f" {logic} ".join(clauses), params

        raise TypeError("filters 必须是 dict 或 list")

    clause_str, param_list = parse(filters)
    where_sql = f"WHERE {clause_str}" if clause_str else ""
    return where_sql, param_list


# ---------------------------------------------------------------------------
# 单表 CRUD 操作
# ---------------------------------------------------------------------------

def select_rows(
    table: str,
    columns: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
    order_by: Optional[str] = None,
    dict_: bool = True,
) -> Union[List[RowDict], List[RowTuple]]:
    """
    查询多行记录

    Args:
        table: 表名
        columns: 要返回的列名列表，None 表示所有列
        filters: 过滤条件字典
        limit: 返回记录数限制
        offset: 偏移量
        order_by: 排序规则（如 "id DESC"）
        dict_: 是否返回字典格式

    Returns:
        查询结果列表

    Example:
        >>> rows = select_rows("user", ["id", "name"], {"age": (">", 18)}, order_by="age DESC")
        >>> print(rows)
        [{'id': 3, 'name': 'Charlie'}, {'id': 2, 'name': 'Bob'}]
    """
    col_sql = ", ".join(_id(c) for c in columns) if columns else "*"
    where_sql, params = _build_where(filters)
    order_sql = f"ORDER BY {order_by}" if order_by else ""
    limit_sql = f"LIMIT {limit} OFFSET {offset}" if limit is not None else ""

    sql = f"SELECT {col_sql} FROM {_id(table)} {where_sql} {order_sql} {limit_sql}"
    logger.debug(f"select_rows - SQL: {sql} | params: {params}")

    return fetch_all(sql, params, dict_=dict_)


def select_one(
    table: str,
    columns: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    *,
    dict_: bool = True,
) -> Union[RowDict, RowTuple, None]:
    """
    查询单行记录

    Args:
        table: 表名
        columns: 要返回的列名列表
        filters: 过滤条件
        dict_: 是否返回字典格式

    Returns:
        单行记录或 None

    Example:
        >>> user = select_one("user", ["id", "name"], {"id": 1})
        >>> print(user)
        {'id': 1, 'name': 'Alice'}
    """
    result = select_rows(table, columns, filters, limit=1, dict_=dict_)
    return result[0] if result else None


def insert_row(table: str, data: RowDict) -> int:
    """
    插入单行记录

    Args:
        table: 表名
        data: 数据字典

    Returns:
        受影响的行数（通常为1）

    Example:
        >>> insert_row("user", {"name": "Alice", "age": 20})
        1
    """
    cols_sql = ", ".join(_id(k) for k in data)
    placeholders = ", ".join(["%s"] * len(data))
    sql = f"INSERT INTO {_id(table)} ({cols_sql}) VALUES ({placeholders})"

    logger.debug(f"insert_row - SQL: {sql} | data: {data}")
    return execute(sql, list(data.values()))


def insert_many(table: str, rows: List[RowDict]) -> int:
    """
    批量插入记录

    Args:
        table: 表名
        rows: 数据字典列表（所有字典的键必须一致）

    Returns:
        受影响的总行数

    Example:
        >>> insert_many("user", [
        ...     {"name": "Alice", "age": 20},
        ...     {"name": "Bob", "age": 25}
        ... ])
        2
    """
    if not rows:
        return 0

    keys = rows[0].keys()
    cols_sql = ", ".join(_id(k) for k in keys)
    placeholders = ", ".join(["%s"] * len(keys))
    sql = f"INSERT INTO {_id(table)} ({cols_sql}) VALUES ({placeholders})"

    values = [list(row.values()) for row in rows]
    logger.debug(f"insert_many - SQL: {sql} | 批次数: {len(rows)}")

    return executemany(sql, values)


def update_rows(
    table: str,
    data: Dict[str, Any],
    filters: Dict[str, Any]
) -> int:
    """
    更新记录

    Args:
        table: 表名
        data: 要更新的数据字典（支持 Raw 表达式）
        filters: 过滤条件（必须提供，防止误更新全表）

    Returns:
        受影响的行数

    Example:
        >>> update_rows("user", {"age": 21}, {"id": 1})
        1
        >>> update_rows("user", {"updated_at": Raw("NOW()")}, {"id": 1})
        1
    """
    if not filters:
        raise ValueError("拒绝执行无 WHERE 条件的 UPDATE")

    set_parts = []
    set_params = []

    for k, v in data.items():
        if isinstance(v, Raw):
            set_parts.append(f"{_id(k)} = {v.expr}")
        else:
            set_parts.append(f"{_id(k)} = %s")
            set_params.append(v)

    where_sql, where_params = _build_where(filters)
    sql = f"UPDATE {_id(table)} SET {', '.join(set_parts)} {where_sql}"

    logger.debug(f"update_rows - SQL: {sql} | params: {set_params + where_params}")
    return execute(sql, set_params + where_params)


def delete_rows(table: str, filters: Dict[str, Any]) -> int:
    """
    删除记录

    Args:
        table: 表名
        filters: 过滤条件（必须提供，防止误删全表）

    Returns:
        受影响的行数

    Example:
        >>> delete_rows("user", {"id": 1})
        1
    """
    if not filters:
        raise ValueError("拒绝执行无 WHERE 条件的 DELETE")

    where_sql, params = _build_where(filters)
    sql = f"DELETE FROM {_id(table)} {where_sql}"

    logger.debug(f"delete_rows - SQL: {sql} | params: {params}")
    return execute(sql, params)


# ---------------------------------------------------------------------------
# 便捷方法
# ---------------------------------------------------------------------------

def count_rows(table: str, filters: Optional[Dict[str, Any]] = None) -> int:
    """
    统计行数

    Args:
        table: 表名
        filters: 过滤条件

    Returns:
        符合条件的行数

    Example:
        >>> count = count_rows("user", {"age": (">", 18)})
        >>> print(count)
        42
    """
    where_sql, params = _build_where(filters)
    sql = f"SELECT COUNT(*) as count FROM {_id(table)} {where_sql}"

    result = fetch_one(sql, params, dict_=True)
    return result['count'] if result else 0


def exists(table: str, filters: Dict[str, Any]) -> bool:
    """
    检查记录是否存在

    Args:
        table: 表名
        filters: 过滤条件

    Returns:
        是否存在

    Example:
        >>> if exists("user", {"email": "alice@example.com"}):
        ...     print("邮箱已存在")
    """
    return count_rows(table, filters) > 0
