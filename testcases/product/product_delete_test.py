"""商品管理 —— 删除商品接口(DELETE /api/products/{id})的自动化测试用例。

覆盖场景：删除无订单商品（含分类级联删除）、删除不存在的商品、删除有关联未完成订单的商品，以及删除仅关联已完成/已发货/已取消订单的商品（预期失败）。
"""
import json
import pytest
import requests
import allure

# 加载删除商品的测试数据（成功/失败/预期失败三类用例）
with open("data/product/product_delete_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)


@allure.feature("商品管理")
@allure.story("删除商品")
class Test_Product_delete:
    """删除商品接口测试类：验证 DELETE /api/products/{id} 的成功、失败与预期失败场景"""

    # 成功用例：删除无订单关联的商品应成功，且删除后再查询返回404
    @pytest.mark.parametrize(
        'case',
        data["success_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_product_delete_success(self, client, db, case):
        """删除商品成功：校验删除提示，并核对商品及分类关联已从数据库删除"""
        # 删除前确认商品存在
        resp = client.get(f"/api/products/{case['product_id']}")
        assert resp.status_code == 200

        # 删除商品，校验状态码与返回提示
        del_resp = client.delete(f"/api/products/{case['product_id']}")
        assert del_resp.status_code == case["expected_status"]
        assert case["expected_message"] in del_resp.json()["message"]

        # 删除后再查询，应404
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.get(f"/api/products/{case['product_id']}")
        assert e.value.response.status_code == 404

        # ========== 数据库校验：商品及其分类关联已从数据库删除 ==========
        db_product = db["one"]("SELECT id FROM products WHERE id = %s", (case['product_id'],))
        assert db_product is None, f"商品 {case['product_id']} 删除后仍存在于数据库"
        db_pc = db["one"]("SELECT id FROM product_category WHERE product_id = %s", (case['product_id'],))
        assert db_pc is None, f"商品 {case['product_id']} 的分类关联未级联删除"

    # 失败用例：删除有关联未完成订单的商品应被拒绝，返回预期错误状态码
    @pytest.mark.parametrize(
        'case',
        data["fail_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_product_delete_fail(self, client, case):
        """删除商品失败：不存在或有关联未完成订单的商品应返回预期错误状态码"""
        # 期望删除请求抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.delete(f"/api/products/{case['product_id']}")
        # 校验异常响应中的实际状态码
        assert e.value.response.status_code == case["expected_status"]

    # 预期失败(xfail)用例：已知 BUG-005/006/007，删除仅关联已完成/已发货/已取消订单的商品后端未正确处理
    @pytest.mark.parametrize(
        'case',
        data["xfail_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    @allure.issue("BUG-005/006/007")
    @pytest.mark.xfail(reason="BUG-005/006/007: 删除仅关联已完成/已发货/已取消订单的商品，后端未正确处理")
    def test_product_delete_xfail(self, client, case):
        """删除仅关联已完成/已发货/已取消订单的商品（预期失败）：已知 BUG-005/006/007"""
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.delete(f"/api/products/{case['product_id']}")
        # BUG-005: 预期200，实际500
        # BUG-006: 预期200，实际500
        # BUG-007: 预期200，实际400
        assert e.value.response.status_code == case["expected_status"]
