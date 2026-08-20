"""订单管理 —— 查询单个订单接口(GET /api/orders/{id})的自动化测试用例。

覆盖场景：查询存在的订单（校验主单与明细），以及查询不存在的订单。
"""

import pytest
import requests
import allure


@allure.feature("订单管理")
@allure.story("查询单个订单")
class Test_Order_query_single:
    """查询单个订单接口测试类：验证 GET /api/orders/{id} 的成功与失败场景"""

    @allure.title("查询存在的订单")
    def test_query_single_order_success(self, client):
        """查询存在的订单：校验订单主单信息与明细"""
        # 查询存在的订单
        # 查询 id=1 的订单
        resp = client.get("/api/orders/1")
        assert resp.status_code == 200
        data = resp.json()

        # 初始数据订单1是用户1、总金额12999、已支付
        assert data["id"] == 1
        assert data["user_id"] == 1
        assert data["total_amount"] == 12999.0
        assert data["status"] == "已支付"
        assert "create_time" in data

        # items 必须是列表，且至少有一条明细
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["product_id"] == 3
        assert item["quantity"] == 1
        assert item["price"] == 12999.0
        assert item["product_name"] == "联想ThinkPad X1"

    @allure.title("查询不存在的订单")
    def test_query_single_order_fail(self, client):
        """查询不存在的订单：期望抛出 HTTPError 且状态码为 404"""
        # 查询不存在的订单
        # 查询不存在的订单，期望抛出 HTTPError 且状态码为 404
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.get("/api/orders/9999")
        assert e.value.response.status_code == 404
