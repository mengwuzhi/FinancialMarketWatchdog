#!/usr/bin/env python
"""查看新闻爬虫采集结果"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_crawler.db.connection import execute_query


def view_news_stats():
    """查看新闻统计"""
    print("=" * 100)
    print("新闻爬虫采集结果统计")
    print("=" * 100)

    # 总数
    total = execute_query("SELECT COUNT(*) FROM news", fetch=True)[0][0]
    print(f"\n[统计] 数据库中共有 {total} 条新闻")

    # 各来源统计
    sources = execute_query("""
        SELECT source, COUNT(*) as count
        FROM news
        GROUP BY source
        ORDER BY count DESC
    """, fetch=True)

    print("\n[来源] 各来源统计：")
    for source, count in sources:
        print(f"  - {source}: {count}条")

    # 各分类统计
    categories = execute_query("""
        SELECT category, COUNT(*) as count
        FROM news
        GROUP BY category
        ORDER BY count DESC
    """, fetch=True)

    print("\n[分类] 各分类统计：")
    for category, count in categories:
        print(f"  - {category}: {count}条")


def view_latest_news(limit=20):
    """查看最新新闻"""
    print("\n" + "=" * 100)
    print(f"最新采集的 {limit} 条新闻")
    print("=" * 100)

    news = execute_query(f"""
        SELECT title, source, category, url, created_at
        FROM news
        ORDER BY created_at DESC
        LIMIT {limit}
    """, fetch=True)

    for i, (title, source, category, url, created_at) in enumerate(news, 1):
        print(f"\n{i}. {title}")
        print(f"   来源: {source} | 分类: {category} | 时间: {created_at}")
        print(f"   链接: {url}")


def search_news(keyword, limit=10):
    """搜索新闻"""
    print("\n" + "=" * 100)
    print(f"搜索关键词: '{keyword}' (最多显示{limit}条)")
    print("=" * 100)

    news = execute_query(f"""
        SELECT title, source, category, url, created_at
        FROM news
        WHERE title LIKE %s OR summary LIKE %s
        ORDER BY created_at DESC
        LIMIT {limit}
    """, (f'%{keyword}%', f'%{keyword}%'), fetch=True)

    if not news:
        print(f"\n未找到包含 '{keyword}' 的新闻")
        return

    print(f"\n找到 {len(news)} 条相关新闻：\n")
    for i, (title, source, category, url, created_at) in enumerate(news, 1):
        print(f"{i}. {title}")
        print(f"   来源: {source} | 分类: {category} | 时间: {created_at}")
        print(f"   链接: {url}\n")


def export_to_file(filename="news_export.txt", limit=100):
    """导出新闻到文件"""
    news = execute_query(f"""
        SELECT title, source, category, url, publish_time, created_at
        FROM news
        ORDER BY created_at DESC
        LIMIT {limit}
    """, fetch=True)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write(f"新闻爬虫采集结果导出 (最新{limit}条)\n")
        f.write("=" * 100 + "\n\n")

        for i, (title, source, category, url, pub_time, created_at) in enumerate(news, 1):
            f.write(f"{i}. {title}\n")
            f.write(f"   来源: {source}\n")
            f.write(f"   分类: {category}\n")
            f.write(f"   发布时间: {pub_time}\n")
            f.write(f"   采集时间: {created_at}\n")
            f.write(f"   链接: {url}\n")
            f.write("\n" + "-" * 100 + "\n\n")

    print(f"[成功] 已导出 {len(news)} 条新闻到文件: {filename}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='查看新闻爬虫采集结果')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--latest', type=int, metavar='N', help='显示最新N条新闻')
    parser.add_argument('--search', type=str, metavar='KEYWORD', help='搜索关键词')
    parser.add_argument('--export', type=str, metavar='FILE', help='导出到文件')
    parser.add_argument('--limit', type=int, default=20, help='限制显示数量')

    args = parser.parse_args()

    # 默认显示统计
    if not any([args.stats, args.latest, args.search, args.export]):
        view_news_stats()
        view_latest_news(10)
    else:
        if args.stats:
            view_news_stats()

        if args.latest:
            view_latest_news(args.latest)

        if args.search:
            search_news(args.search, args.limit)

        if args.export:
            export_to_file(args.export, args.limit)
