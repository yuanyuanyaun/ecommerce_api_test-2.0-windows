from utils.db_helper import reset_database
import pytest


@pytest.fixture(scope="module", autouse=True)
def reset_db_before_test():
    """整个测试会话开始前自动重置数据库"""
    reset_database()
    yield
