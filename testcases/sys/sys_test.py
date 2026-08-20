"""系统级冒烟测试：服务健康检查与数据库连通性检查。"""
import allure


@allure.feature("系统管理")
@allure.story("系统接口与数据库连接测试")
class Test_System:
    """系统管理测试类：验证根路径健康检查与数据库连接检查接口"""

    @allure.title("健康检查")
    def test_health_check(self, client):
        """健康检查：访问根路径，期望返回 200 且 status=running"""
        # 健康检查：访问根路径 "/"，期望返回 200 且 status=running
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"

    @allure.title("数据库连通性检查")
    def test_db_connection_check(self, client):
        """数据库连通性检查：访问 /api/db-check，期望返回 200 且 status=ok"""
        # 数据库连通性检查：访问 "/api/db-check"，期望返回 200 且 status=ok
        resp = client.get("/api/db-check")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
