"""订单管理 —— 创建订单接口(POST /api/orders/)的自动化测试用例。

覆盖场景：正常创建订单（校验订单、明细、库存扣减），以及用户/商品不存在、商品下架、库存不足、数量非法等失败场景。
"""
import pytest
import json
import requests
import allure

# 加载创建订单的测试数据（成功/失败两类用例）
with open('data/order/order_add_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)


@allure.feature("订单管理")
@allure.story("添加订单")
class Test_Order_add:
    """创建订单接口测试类：验证 POST /api/orders/ 的成功与失败场景"""

    # 成功用例：创建订单应返回预期状态码，并校验订单ID/状态/金额/明细条数
    @pytest.mark.parametrize(
        'case',
        data["success_cases"],
        ids=lambda case: case['name']
    )
    @allure.title("{case[name]}")
    def test_order_add_success(self, client, db, case):
        """创建订单成功：校验订单字段，并核对订单/明细写入及库存扣减"""
        # 记录下单前的商品库存，用于后续校验库存扣减
        product_id = case["payload"]["items"][0]["product_id"]
        quantity = case["payload"]["items"][0]["quantity"]
        before_stock = db["one"]("SELECT stock FROM products WHERE id = %s", (product_id,))["stock"]
        # 发送创建订单请求
        resp = client.post('/api/orders/', json=case["payload"])
        # 校验返回的状态码与订单字段内容
        assert resp.status_code == case["expected_status"]
        add_data = resp.json()
        assert add_data["id"] == case["expected_user_id"]
        assert add_data["status"] == case["expected_status_text"]
        assert add_data["total_amount"] == case["expected_total_amount"]
        assert isinstance(add_data["items"], list)
        assert len(add_data["items"]) == case["expected_items_len"]

        # ========== 数据库校验：订单与明细已写入，库存已扣减 ==========
        order_id = add_data["id"]
        db_order = db["one"](
            "SELECT user_id, total_amount, status FROM orders WHERE id = %s",
            (order_id,)
        )
        assert db_order is not None, "新订单未写入数据库"
        assert db_order["user_id"] == case["payload"]["user_id"]
        assert float(db_order["total_amount"]) == case["expected_total_amount"]
        assert db_order["status"] == case["expected_status_text"]
        # 校验订单明细已写入 order_items 表
        db_item = db["one"](
            "SELECT product_id, quantity FROM order_items WHERE order_id = %s",
            (order_id,)
        )
        assert db_item is not None, "订单明细未写入数据库"
        assert db_item["product_id"] == product_id
        assert db_item["quantity"] == quantity
        # 校验库存扣减：下单后库存 = 下单前库存 - 购买数量
        after_stock = db["one"]("SELECT stock FROM products WHERE id = %s", (product_id,))["stock"]
        assert after_stock == before_stock - quantity, f"库存扣减不正确：期望 {before_stock - quantity}，实际 {after_stock}"

    # 失败用例：非法入参应抛出 HTTPError 异常，并返回预期错误状态码
    @pytest.mark.parametrize(
        'case',
        data["fail_cases"],
        ids=lambda case: case['name']
    )
    @allure.title("{case[name]}")
    def test_order_add_fail(self, client, case):
        """创建订单失败：非法入参应抛出 HTTPError 并返回预期错误状态码"""
        # 期望请求抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.post('/api/orders/', json=case["payload"])
        # 校验异常响应中的实际状态码
        assert e.value.response.status_code == case["expected_status"]
