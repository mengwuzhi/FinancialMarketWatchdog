"""Database connection helpers"""
import pymysql
import logging

from config.settings import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

logger = logging.getLogger(__name__)


def get_db_connection():
    """Return a new pymysql connection (caller must close)."""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30,
    )


def execute_query(query, params=None, fetch=False):
    """
    Execute single SQL.
      fetch=False -> commit, return affected rows
      fetch=True  -> return fetchall() rows
    """
    conn = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(query, params)
        if fetch:
            return cur.fetchall()
        conn.commit()
        return cur.rowcount
    except Exception as exc:
        if conn:
            conn.rollback()
        logger.error("execute_query: %s", exc)
        raise
    finally:
        if conn:
            conn.close()


def executemany(query, params_list):
    """Batch execute, return affected rows."""
    if not params_list:
        return 0
    conn = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.executemany(query, params_list)
        conn.commit()
        return cur.rowcount
    except Exception as exc:
        if conn:
            conn.rollback()
        logger.error("executemany: %s", exc)
        raise
    finally:
        if conn:
            conn.close()
