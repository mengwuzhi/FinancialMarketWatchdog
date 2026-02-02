# DB 模块使用文档

## 简介

这是一个轻量级的MySQL数据库操作模块，参考 dbean-mysql 项目设计，提供简洁的API和强大的查询能力。

## 特性

- ✅ **字典驱动查询** - 无需手写复杂 WHERE 子句
- ✅ **连接池管理** - 基于 DBUtils 的高效连接池
- ✅ **事务支持** - 装饰器风格的事务管理
- ✅ **SQL注入防护** - 参数化查询 + 标识符转义
- ✅ **丰富的操作符** - 支持 =、!=、>、<、IN、LIKE、BETWEEN 等
- ✅ **支持原始SQL** - 灵活的 Raw 表达式支持
- ✅ **中文错误提示** - 方便开发调试

## 安装依赖

```bash
pip install pymysql dbutils
```

## 快速开始

### 1. 配置数据库

```python
from db import set_db_config

# 配置数据库连接
set_db_config(
    db_config={
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'your_password',
        'database': 'lof_watchdog',
        'charset': 'utf8mb4',
    },
    pool_config={
        'maxconnections': 10,  # 最大连接数
        'mincached': 2,        # 最小缓存连接数
    }
)
```

### 2. 基础CRUD操作

#### 查询数据

```python
from db import select_rows, select_one

# 查询多行
users = select_rows("user", ["id", "name", "age"], {"age": (">", 18)})
print(users)
# [{'id': 1, 'name': 'Alice', 'age': 20}, {'id': 2, 'name': 'Bob', 'age': 25}]

# 查询单行
user = select_one("user", ["id", "name"], {"id": 1})
print(user)
# {'id': 1, 'name': 'Alice'}

# 复杂查询（带排序和限制）
recent_users = select_rows(
    "user",
    ["id", "name", "created_at"],
    {"status": "active"},
    order_by="created_at DESC",
    limit=10
)
```

#### 插入数据

```python
from db import insert_row, insert_many

# 插入单行
insert_row("user", {"name": "Alice", "age": 20, "email": "alice@example.com"})

# 批量插入
insert_many("user", [
    {"name": "Bob", "age": 25, "email": "bob@example.com"},
    {"name": "Charlie", "age": 30, "email": "charlie@example.com"}
])
```

#### 更新数据

```python
from db import update_rows, Raw

# 普通更新
update_rows("user", {"age": 21}, {"id": 1})

# 使用 SQL 表达式
update_rows("user", {"updated_at": Raw("NOW()")}, {"id": 1})

# 批量更新
update_rows("user", {"status": "inactive"}, {"age": ("<", 18)})
```

#### 删除数据

```python
from db import delete_rows

# 删除记录
delete_rows("user", {"id": 1})

# 批量删除
delete_rows("user", {"status": "deleted"})
```

### 3. 高级查询条件

```python
# IN 查询
users = select_rows("user", ["id", "name"], {
    "type": ("IN", ["admin", "moderator"])
})

# LIKE 模糊查询
users = select_rows("user", ["id", "name"], {
    "name": ("LIKE", "%张%")
})

# BETWEEN 范围查询
orders = select_rows("order", ["id", "amount"], {
    "created_at": ("BETWEEN", "2024-01-01", "2024-12-31")
})

# NULL 判断
users = select_rows("user", ["id", "name"], {
    "deleted_at": ("IS", None)
})

# 组合条件（AND）
users = select_rows("user", ["id", "name"], {
    "age": (">", 18),
    "status": "active",
    "type": ("IN", ["vip", "premium"])
})

# OR 条件
users = select_rows("user", ["id", "name"], {
    "OR": [
        {"name": ("LIKE", "%张%")},
        {"nickname": ("LIKE", "%李%")}
    ]
})

# 复杂嵌套（AND + OR）
users = select_rows("user", ["id", "name"], {
    "age": (">", 18),
    "OR": [
        {"status": "active"},
        {"status": "trial"}
    ]
})
```

### 4. 事务管理

```python
from db import transaction

@transaction
def transfer_money(from_id, to_id, amount, *, conn):
    """转账操作（在事务中执行）"""
    with conn.cursor() as cur:
        # 扣款
        cur.execute(
            "UPDATE wallet SET balance = balance - %s WHERE user_id = %s",
            (amount, from_id)
        )

        # 到账
        cur.execute(
            "UPDATE wallet SET balance = balance + %s WHERE user_id = %s",
            (amount, to_id)
        )

# 调用事务函数（自动提交或回滚）
transfer_money(1, 2, 100)
```

### 5. 底层操作

```python
from db import fetch_all, fetch_one, execute

# 原始SQL查询
rows = fetch_all("SELECT * FROM user WHERE age > %s", (18,))

# 原始SQL执行
execute("UPDATE user SET status = %s WHERE id = %s", ("active", 1))
```

### 6. 便捷方法

```python
from db import count_rows, exists

# 统计行数
total = count_rows("user", {"status": "active"})
print(f"活跃用户数: {total}")

# 检查是否存在
if exists("user", {"email": "alice@example.com"}):
    print("邮箱已存在")
```

## API 参考

### 配置管理

| 函数 | 说明 |
|------|------|
| `set_db_config(db_config, pool_config)` | 设置数据库配置 |
| `get_db_config()` | 获取当前数据库配置 |
| `reset_config()` | 重置为默认配置 |

### DAO 层

| 函数 | 说明 |
|------|------|
| `select_rows(table, columns, filters, ...)` | 查询多行 |
| `select_one(table, columns, filters)` | 查询单行 |
| `insert_row(table, data)` | 插入单行 |
| `insert_many(table, rows)` | 批量插入 |
| `update_rows(table, data, filters)` | 更新记录 |
| `delete_rows(table, filters)` | 删除记录 |
| `count_rows(table, filters)` | 统计行数 |
| `exists(table, filters)` | 检查是否存在 |

### 底层操作

| 函数 | 说明 |
|------|------|
| `fetch_all(sql, params)` | 执行查询（多行） |
| `fetch_one(sql, params)` | 执行查询（单行） |
| `execute(sql, params)` | 执行写操作 |
| `executemany(sql, params_seq)` | 批量执行 |
| `@transaction` | 事务装饰器 |

## 支持的操作符

| 操作符 | 语法 | 示例 |
|--------|------|------|
| 等于 | `{"key": value}` | `{"age": 18}` |
| 不等于 | `{"key": ("!=", value)}` | `{"status": ("!=", "deleted")}` |
| 大于 | `{"key": (">", value)}` | `{"age": (">", 18)}` |
| 小于 | `{"key": ("<", value)}` | `{"score": ("<", 60)}` |
| 大于等于 | `{"key": (">=", value)}` | `{"age": (">=", 18)}` |
| 小于等于 | `{"key": ("<=", value)}` | `{"age": ("<=", 60)}` |
| IN | `{"key": ("IN", [...])}` | `{"type": ("IN", ["A", "B"])}` |
| NOT IN | `{"key": ("NOT IN", [...])}` | `{"type": ("NOT IN", ["C"])}` |
| LIKE | `{"key": ("LIKE", pattern)}` | `{"name": ("LIKE", "%张%")}` |
| NOT LIKE | `{"key": ("NOT LIKE", pattern)}` | `{"name": ("NOT LIKE", "%测试%")}` |
| BETWEEN | `{"key": ("BETWEEN", a, b)}` | `{"date": ("BETWEEN", "2024-01-01", "2024-12-31")}` |
| IS NULL | `{"key": ("IS", None)}` | `{"deleted_at": ("IS", None)}` |
| IS NOT NULL | `{"key": ("IS NOT", None)}` | `{"updated_at": ("IS NOT", None)}` |

## 异常处理

```python
from db import select_rows, DBQueryError, DBConnectionError

try:
    users = select_rows("user", ["id", "name"], {"age": (">", 18)})
except DBQueryError as e:
    print(f"查询失败: {e}")
    print(f"SQL: {e.sql}")
    print(f"参数: {e.params}")
except DBConnectionError as e:
    print(f"数据库连接失败: {e}")
```

## 最佳实践

1. **配置优先** - 在程序启动时调用 `set_db_config()` 配置数据库
2. **使用DAO层** - 优先使用 `select_rows`、`insert_row` 等高级API
3. **防止误操作** - `update_rows` 和 `delete_rows` 必须提供 `filters` 参数
4. **事务管理** - 涉及多表操作使用 `@transaction` 装饰器
5. **异常捕获** - 生产环境应捕获 `DBError` 系列异常
6. **连接池监控** - 使用 `get_pool_status()` 监控连接池状态

## 注意事项

1. 所有表名和列名会自动用反引号包裹，防止关键字冲突
2. `filters` 为 `None` 或 `{}` 时不添加 WHERE 子句
3. `update_rows` 和 `delete_rows` 不允许无条件操作（防止误删全表）
4. 连接池配置修改后需调用 `reset_pool()` 重新初始化

## 许可证

MIT License
