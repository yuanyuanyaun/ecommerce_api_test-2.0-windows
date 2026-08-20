"""pytest 全局夹具(fixture)定义文件，供所有测试用例共享。"""
from utils.api_client import APIClient
from utils.db_helper import query_one, query_all, execute_sql
import pytest


# 定义 session 级别的 client 夹具：整个测试会话只创建一次，供所有用例复用同一个客户端
@pytest.fixture(scope="session")
def client():
    """设置一次，全测试通用，调用api设置"""
    # 返回统一的 API 客户端实例
    return APIClient()


@pytest.fixture
def db():
    """数据库校验工具"""
    return {
        "one": query_one,
        "all": query_all,
        "exec": execute_sql
    }
