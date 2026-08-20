"""订单管理 —— 取消订单接口(PUT /api/orders/{id}/cancel)的自动化测试用例。

覆盖场景：待支付订单正常取消（校验状态与库存恢复），以及取消不存在/非待支付状态订单的失败场景。
"""
import json
import pytest
import requests
import allure

# 加载取消订单的测试数据（成功/失败两类用例）
with open("data/order/order_cancel_data.json", "r", encoding="utf-8") as f:
    cancel_data = json.load(f)


@allure.feature("订单管理")
@allure.story("取消订单")
class Test_Order_cancel:
    """取消订单接口测试类：验证 PUT /api/orders/{id}/cancel 的成功与失败场景"""

    # 成功用例：取消订单应返回预期状态码，并校验订单状态/用户/金额
    @pytest.mark.parametrize(
        "case",
        cancel_data["success_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_order_cancel_success(self, client, db, case):
        """取消订单成功：校验订单状态更新与库存恢复"""
        # 记录取消前订单明细与商品库存，用于后续校验库存恢复
        db_item_before = db["one"](
            "SELECT product_id, quantity FROM order_items WHERE order_id = %s",
            (case['order_id'],)
        )
        before_stock = db["one"](
            "SELECT stock FROM products WHERE id = %s",
            (db_item_before["product_id"],)
        )["stock"]
        # 发送取消订单请求
        resp = client.put(f"/api/orders/{case['order_id']}/cancel")
        # 校验返回的状态码与订单字段内容
        assert resp.status_code == case["expected_status"]
        data = resp.json()

        assert data["status"] == case["expected_order_status"]
        assert data["user_id"] == case["expected_user_id"]
        assert data["total_amount"] == case["expected_total_amount"]

        # 使用单个查询接口，再查一次确认状态真的更新了
        get_resp = client.get(f"/api/orders/{case['order_id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == case["expected_order_status"]

        # ========== 数据库校验：订单状态已更新，库存已恢复 ==========
        db_order = db["one"]("SELECT status FROM orders WHERE id = %s", (case['order_id'],))
        assert db_order["status"] == case["expected_order_status"]
        after_stock = db["one"](
            "SELECT stock FROM products WHERE id = %s",
            (db_item_before["product_id"],)
        )["stock"]
        assert after_stock == before_stock + db_item_before["quantity"], \
            f"取消订单后库存未恢复：期望 {before_stock + db_item_before['quantity']}，实际 {after_stock}"

    # 失败用例：非法订单应抛出 HTTPError 异常，并返回预期错误状态码
    @pytest.mark.parametrize(
        "case",
        cancel_data["fail_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_order_cancel_fail(self, client, case):
        """取消订单失败：不存在或非待支付订单应返回预期错误状态码"""
        # 期望请求抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.put(f"/api/orders/{case['order_id']}/cancel")
        # 校验异常响应中的实际状态码
        assert e.value.response.status_code == case["expected_status"]
