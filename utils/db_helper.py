import os
import pymysql
from config.setting import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# 项目根目录（utils/ 的上一级），用于定位 scripts/reset_db.sql，避免依赖当前工作目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def reset_database():
    """创建数据库连接，用于重置数据库（不指定库，以便 reset_db.sql 里的 CREATE DATABASE 能执行）"""
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        charset="utf8mb4",
        autocommit=True
    )
    try:
        with conn.cursor() as cursor:
            with open(os.path.join(BASE_DIR, "scripts", "reset_db.sql"), encoding="utf-8") as f:
                sql_content = f.read()
            statements = [s.strip() for s in sql_content.split(";") if s.strip()]
            for stmt in statements:
                cursor.execute(stmt)
        print("\n数据库重置完成")
    finally:
        conn.close()


def _get_conn():
    """创建数据库连接（内部使用，不直接给测试用例调用）"""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",  #避免中文乱码
        autocommit=True,    #自动提交
        cursorclass=pymysql.cursors.DictCursor  # 关键：返回字典，不是元组
    )


def query_one(sql, params=None):
    """查询一条记录，返回字典；查不到返回 None"""
    conn = _get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()
    finally:
        conn.close()


def query_all(sql, params=None):
    """查询所有记录，返回字典列表；查不到返回空列表 []"""
    conn = _get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def execute_sql(sql, params=None):
    """执行非查询 SQL（INSERT/UPDATE/DELETE）"""
    conn = _get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
    finally:
        conn.close()
