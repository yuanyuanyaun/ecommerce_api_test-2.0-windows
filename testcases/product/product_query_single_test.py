"""商品管理 —— 查询单个商品接口(GET /api/products/{id})的自动化测试用例。

覆盖场景：查询存在的商品（校验字段与分类），以及查询不存在的商品。
"""
import pytest
import requests
import allure


@allure.feature("商品管理")
@allure.story("查询单个商品")
class Test_Product_query_single:
    """查询单个商品接口测试类：验证 GET /api/products/{id} 的成功与失败场景"""

    @allure.title("查询存在的商品")
    def test_product_query_single_success(self, client):
        """查询存在的商品：校验商品字段与分类信息"""
        # 成功查询存在的商品
        # 查询 id=1 的商品
        resp = client.get("/api/products/1")
        assert resp.status_code == 200
        data = resp.json()

        # 初始数据 id=1 是 iPhone 15 Pro
        assert data["id"] == 1
        assert data["name"] == "iPhone 15 Pro"
        assert data["price"] == 8999.0
        assert data["stock"] == 100
        assert data["status"] == "在售"
        assert "create_time" in data

        # categories 必须是列表，且包含手机分类(id=3)
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) == 1
        assert data["categories"][0]["id"] == 3
        assert data["categories"][0]["name"] == "手机"

    @allure.title("查询不存在的商品")
    def test_product_query_single_fail(self, client):
        """查询不存在的商品：期望抛出 HTTPError 且状态码为 404"""
        # TC-PROD-023: 查询不存在的商品
        # 查询不存在的商品，期望抛出 HTTPError 且状态码为 404
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.get("/api/products/999")
        assert e.value.response.status_code == 404
