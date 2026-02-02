# db/example_usage.py
"""
DB 模块使用示例
演示如何在 lof_watchdog 项目中使用数据库模块
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import (
    set_db_config,
    select_rows,
    select_one,
    insert_row,
    insert_many,
    update_rows,
    delete_rows,
    count_rows,
    exists,
    transaction,
    Raw,
    DBQueryError
)


def example_1_config():
    """示例1：配置数据库"""
    print("=" * 60)
    print("示例1：配置数据库")
    print("=" * 60)

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
            'maxconnections': 10,
            'mincached': 2,
        }
    )

    print("✓ 数据库配置完成")
    print()


def example_2_basic_crud():
    """示例2：基础 CRUD 操作"""
    print("=" * 60)
    print("示例2：基础 CRUD 操作")
    print("=" * 60)

    # 插入单行
    print("\n[插入单行]")
    try:
        insert_row("lof_price_history", {
            "code": "161226",
            "name": "新华MSCI中国A股国际ETF",
            "price": 1.234,
            "change_pct": 2.5,
            "date": "2024-01-22"
        })
        print("✓ 插入成功")
    except DBQueryError as e:
        print(f"✗ 插入失败: {e}")

    # 批量插入
    print("\n[批量插入]")
    try:
        insert_many("lof_price_history", [
            {"code": "161225", "name": "LOF基金1", "price": 1.5, "change_pct": 1.2, "date": "2024-01-22"},
            {"code": "163407", "name": "LOF基金2", "price": 2.3, "change_pct": -0.8, "date": "2024-01-22"}
        ])
        print("✓ 批量插入成功")
    except DBQueryError as e:
        print(f"✗ 批量插入失败: {e}")

    # 查询数据
    print("\n[查询数据]")
    try:
        rows = select_rows(
            "lof_price_history",
            ["code", "name", "price", "change_pct"],
            {"date": "2024-01-22"},
            order_by="change_pct DESC",
            limit=5
        )
        print(f"✓ 查询成功，共 {len(rows)} 条记录")
        for row in rows:
            print(f"  - {row['code']} {row['name']}: {row['price']} ({row['change_pct']}%)")
    except DBQueryError as e:
        print(f"✗ 查询失败: {e}")

    # 更新数据
    print("\n[更新数据]")
    try:
        affected = update_rows(
            "lof_price_history",
            {"price": 1.5, "updated_at": Raw("NOW()")},
            {"code": "161226", "date": "2024-01-22"}
        )
        print(f"✓ 更新成功，影响 {affected} 行")
    except DBQueryError as e:
        print(f"✗ 更新失败: {e}")

    # 删除数据
    print("\n[删除数据]")
    try:
        affected = delete_rows("lof_price_history", {"date": "2024-01-22"})
        print(f"✓ 删除成功，影响 {affected} 行")
    except DBQueryError as e:
        print(f"✗ 删除失败: {e}")

    print()


def example_3_advanced_query():
    """示例3：高级查询"""
    print("=" * 60)
    print("示例3：高级查询")
    print("=" * 60)

    # IN 查询
    print("\n[IN 查询]")
    try:
        rows = select_rows(
            "lof_price_history",
            ["code", "name", "price"],
            {"code": ("IN", ["161226", "161225", "163407"])}
        )
        print(f"✓ 查询成功，共 {len(rows)} 条记录")
    except DBQueryError as e:
        print(f"✗ 查询失败: {e}")

    # LIKE 模糊查询
    print("\n[LIKE 模糊查询]")
    try:
        rows = select_rows(
            "lof_price_history",
            ["code", "name"],
            {"name": ("LIKE", "%ETF%")}
        )
        print(f"✓ 查询成功，共 {len(rows)} 条记录")
    except DBQueryError as e:
        print(f"✗ 查询失败: {e}")

    # 范围查询
    print("\n[范围查询 - 涨幅 > 5%]")
    try:
        rows = select_rows(
            "lof_price_history",
            ["code", "name", "change_pct"],
            {"change_pct": (">", 5)},
            order_by="change_pct DESC"
        )
        print(f"✓ 查询成功，共 {len(rows)} 条记录")
    except DBQueryError as e:
        print(f"✗ 查询失败: {e}")

    # 复杂组合查询（AND + OR）
    print("\n[复杂组合查询]")
    try:
        rows = select_rows(
            "lof_price_history",
            ["code", "name", "price", "change_pct"],
            {
                "date": "2024-01-22",
                "OR": [
                    {"change_pct": (">", 5)},
                    {"change_pct": ("<", -5)}
                ]
            }
        )
        print(f"✓ 查询成功，共 {len(rows)} 条记录")
    except DBQueryError as e:
        print(f"✗ 查询失败: {e}")

    print()


def example_4_transaction():
    """示例4：事务操作"""
    print("=" * 60)
    print("示例4：事务操作")
    print("=" * 60)

    @transaction
    def update_lof_status(code, new_status, *, conn):
        """更新LOF状态（事务中执行）"""
        with conn.cursor() as cur:
            # 更新状态
            cur.execute(
                "UPDATE lof_monitor SET status = %s WHERE code = %s",
                (new_status, code)
            )

            # 记录日志
            cur.execute(
                "INSERT INTO lof_status_log (code, old_status, new_status, changed_at) "
                "VALUES (%s, 'active', %s, NOW())",
                (code, new_status)
            )

    try:
        update_lof_status("161226", "suspended")
        print("✓ 事务执行成功")
    except DBQueryError as e:
        print(f"✗ 事务执行失败（已回滚）: {e}")

    print()


def example_5_utility_functions():
    """示例5：便捷方法"""
    print("=" * 60)
    print("示例5：便捷方法")
    print("=" * 60)

    # 统计行数
    print("\n[统计行数]")
    try:
        total = count_rows("lof_price_history", {"date": "2024-01-22"})
        print(f"✓ 2024-01-22 共有 {total} 条记录")
    except DBQueryError as e:
        print(f"✗ 统计失败: {e}")

    # 检查是否存在
    print("\n[检查记录是否存在]")
    try:
        if exists("lof_price_history", {"code": "161226", "date": "2024-01-22"}):
            print("✓ 记录存在")
        else:
            print("✗ 记录不存在")
    except DBQueryError as e:
        print(f"✗ 检查失败: {e}")

    print()


def example_6_lof_watchdog_scenario():
    """示例6：lof_watchdog 实际场景"""
    print("=" * 60)
    print("示例6：lof_watchdog 实际使用场景")
    print("=" * 60)

    # 场景1：保存每日LOF价格数据
    print("\n[场景1：保存每日LOF价格数据]")
    lof_data = [
        {"code": "161226", "name": "新华MSCI中国A股", "price": 1.234, "premium": 2.5, "date": "2024-01-22"},
        {"code": "161225", "name": "新华鑫动力", "price": 0.987, "premium": -1.2, "date": "2024-01-22"},
    ]

    try:
        insert_many("lof_daily_price", lof_data)
        print(f"✓ 保存了 {len(lof_data)} 条LOF价格数据")
    except DBQueryError as e:
        print(f"✗ 保存失败: {e}")

    # 场景2：查询高溢价LOF
    print("\n[场景2：查询溢价率 > 10% 的LOF]")
    try:
        high_premium = select_rows(
            "lof_daily_price",
            ["code", "name", "premium"],
            {
                "date": "2024-01-22",
                "premium": (">", 10)
            },
            order_by="premium DESC"
        )
        print(f"✓ 找到 {len(high_premium)} 个高溢价LOF")
        for lof in high_premium:
            print(f"  - {lof['code']} {lof['name']}: 溢价 {lof['premium']}%")
    except DBQueryError as e:
        print(f"✗ 查询失败: {e}")

    # 场景3：查询最近5天的涨停记录
    print("\n[场景3：查询最近5天的涨停记录]")
    try:
        limit_up_records = select_rows(
            "lof_limit_alerts",
            ["code", "name", "alert_type", "created_at"],
            {
                "alert_type": "LIMIT_UP",
                "created_at": (">", "2024-01-17")
            },
            order_by="created_at DESC",
            limit=10
        )
        print(f"✓ 找到 {len(limit_up_records)} 条涨停记录")
    except DBQueryError as e:
        print(f"✗ 查询失败: {e}")

    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DB 模块使用示例")
    print("=" * 60 + "\n")

    print("注意：运行此示例前，请先创建数据库和相应的表结构")
    print()

    # 运行示例（注释掉需要实际数据库的部分）
    # example_1_config()
    # example_2_basic_crud()
    # example_3_advanced_query()
    # example_4_transaction()
    # example_5_utility_functions()
    # example_6_lof_watchdog_scenario()

    print("=" * 60)
    print("示例演示完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
