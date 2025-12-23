import logging
import pymysql
import dbutils.pooled_db as dbutils

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456wushikai',
    'database': 'ead',
    'charset': 'utf8mb4'
}

POOL = dbutils.PooledDB(
    creator=pymysql,
    maxconnections=8,
    mincached=2,
    maxcached=5,
    blocking=True,
    **DB_CONFIG
)

def fetch_one(sql, params=None):
    """Execute query and return a single record"""
    conn = POOL.connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(sql, params or ())
        result = cursor.fetchone()
        return result
    except Exception as e:
        logging.error(f"Database query failed: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def fetch_all(sql, params=None):
    """Execute query and return all records"""
    conn = POOL.connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(sql, params or ())
        result = cursor.fetchall()
        return result
    except Exception as e:
        logging.error(f"Database query failed: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def execute_sql(sql, params=None):
    """Execute SQL statement (INSERT, UPDATE, DELETE)"""
    conn = POOL.connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or ())
        conn.commit()
        if sql.strip().upper().startswith('INSERT'):
            return cursor.lastrowid
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        logging.error(f"Database operation failed: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()
