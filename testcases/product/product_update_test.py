"""商品管理 —— 修改商品接口(PUT /api/products/{id})的自动化测试用例。

覆盖场景：只改 name、改全部字段（含价格/库存/状态/分类）；以及商品不存在、名称超长、价格/库存为负、非法状态、关联不存在分类等异常。
"""
import pytest
import json
import requests
import allure

# 加载修改商品的测试数据（成功/失败两类用例）
with open('data/product/product_update_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)


@allure.feature("商品管理")
@allure.story("修改商品")
class Test_Product_update:
    """修改商品接口测试类：验证 PUT /api/products/{id} 的成功与失败场景"""

    # 成功用例：修改商品应返回预期状态码，并校验各字段与分类ID的更新结果
    @pytest.mark.parametrize(
        'case',
        data["success_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_product_update_success(self, client, db, case):
        """修改商品成功：校验响应字段，并核对数据库已真正落库"""
        # 发送修改商品请求
        resp = client.put(f"/api/products/{case["product_id"]}", json=case["update_payload"])
        # 校验返回的状态码与商品字段内容
        assert resp.status_code == case["expected_status_code"]
        # 用 update_data 保存响应体，避免与模块级测试数据 data 重名
        update_data = resp.json()
        assert update_data["id"] == case["product_id"]
        assert update_data["name"] == case["expected_name"]
        assert update_data["price"] == case["expected_price"]
        assert update_data["stock"] == case["expected_stock"]
        assert update_data["status"] == case["expected_status"]
        # 校验返回的分类ID集合与预期一致（排序后比较）
        assert isinstance(update_data["categories"], list)
        actual_cat_ids = sorted(cat["id"] for cat in update_data["categories"])
        assert actual_cat_ids == sorted(case["expected_category_ids"])
        # 再用查询接口确认修改已落库
        get_resp = client.get(f"/api/products/{case['product_id']}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["name"] == case["expected_name"]
        assert get_data["price"] == case["expected_price"]
        assert get_data["stock"] == case["expected_stock"]
        assert get_data["status"] == case["expected_status"]
        assert isinstance(get_data["categories"], list)
        actual_cat_ids_get = sorted(cat["id"] for cat in get_data["categories"])
        assert actual_cat_ids_get == sorted(case["expected_category_ids"])

        # ========== 数据库校验：商品修改结果已真正落库 ==========
        db_product = db["one"](
            "SELECT id, name, price, stock, status FROM products WHERE id = %s",
            (case["product_id"],)
        )
        assert db_product is not None, f"商品 {case['product_id']} 在数据库中不存在"
        assert db_product["name"] == case["expected_name"]
        assert float(db_product["price"]) == case["expected_price"]
        assert db_product["stock"] == case["expected_stock"]
        assert db_product["status"] == case["expected_status"]

    # 失败用例：非法入参应抛出 HTTPError 异常，并返回预期错误状态码
    @pytest.mark.parametrize(
        'case',
        data["fail_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_product_update_fail(self, client, case):
        """修改商品失败：非法入参应抛出 HTTPError 并返回预期错误状态码"""
        # 期望请求抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.put(f"/api/products/{case['product_id']}", json=case["update_payload"])
        # 校验异常响应中的实际状态码
        assert e.value.response.status_code == case["expected_status_code"]
