"""商品管理 —— 新增商品接口(POST /api/products/)的自动化测试用例。

覆盖场景：正常添加；以及名称超长/空串/空格、价格为负、库存为负、非法状态、关联不存在的分类等失败场景。
"""
import requests
import pytest
import json
import allure
# 加载新增商品的测试数据（成功/失败两类用例）
with open('data/product/product_add_data.json', 'r', encoding='utf - 8') as f:
    data = json.load(f)
@allure.feature("商品管理")
@allure.story("添加商品")

class Test_Product_add:
    """新增商品接口测试类：验证 POST /api/products/ 的成功与失败场景"""

    # 成功用例：新增商品应返回预期状态码，并校验名称/价格/库存/状态及关键字段
    @pytest.mark.parametrize(
        'case',
        data["success_cases"],
        ids=lambda case: case['name']
    )
    @allure.title("{case[name]}")
    def test_product_add_success(self, client, db, case):
        """新增商品成功：校验响应字段，并核对商品及分类关联已写入数据库"""
        # 发送新增商品请求
        resp = client.post('/api/products/', json=case["payload"])
        # 校验返回的状态码与商品字段内容
        assert resp.status_code == case["expected_status"]
        # 用 add_data 保存响应体，避免与模块级测试数据 data 重名
        add_data = resp.json()
        assert add_data["name"] == case["payload"]["name"]
        assert add_data["price"] == case["payload"]["price"]
        assert add_data["stock"] == case["payload"]["stock"]
        assert add_data["status"] == case["payload"]["status"]
        assert "id" in add_data
        assert "create_time" in add_data
        assert isinstance(add_data, dict)

        # ========== 数据库校验：商品及其分类关联已真正写入 ==========
        db_product = db["one"](
            "SELECT id, name, price, stock, status FROM products WHERE name = %s",
            (case["payload"]["name"],)
        )
        assert db_product is not None, f"商品 {case['payload']['name']} 未写入数据库"
        assert db_product["name"] == case["payload"]["name"]
        assert float(db_product["price"]) == float(case["payload"]["price"])
        assert db_product["stock"] == case["payload"]["stock"]
        assert db_product["status"] == case["payload"]["status"]
        # 校验商品与分类的关联关系已写入 product_category 表
        if case["payload"].get("category_ids"):
            db_pc = db["all"](
                "SELECT category_id FROM product_category WHERE product_id = %s",
                (db_product["id"],)
            )
            actual_cat_ids = sorted(row["category_id"] for row in db_pc)
            assert actual_cat_ids == sorted(case["payload"]["category_ids"]), \
                f"商品分类关联不正确：期望 {sorted(case['payload']['category_ids'])}，实际 {actual_cat_ids}"

    # 失败用例：非法入参应抛出 HTTPError 异常，并返回预期错误状态码
    @pytest.mark.parametrize(
        'case',
        data["fail_cases"],
        ids=lambda case: case['name']
    )
    @allure.title("{case[name]}")
    def test_product_add_fail(self, client, case):
        """新增商品失败：非法入参应抛出 HTTPError 并返回预期错误状态码"""
        # 期望请求抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.post("/api/products/", json=case["payload"])
        # 校验异常响应中的实际状态码
        assert e.value.response.status_code == case["expected_status"]
