"""商品管理 —— 查询商品列表接口(GET /api/products/)的自动化测试用例。

覆盖场景：默认/分页/分类筛选/limit 边界等成功查询，以及 skip/limit/category_id 非法值等失败查询。
"""
import json
import pytest
import requests
import allure

# 加载查询商品列表的测试数据
with open("data/product/product_query_list_data.json", 'r', encoding="utf-8") as f:
    query_data = json.load(f)


@allure.feature("商品管理")
@allure.story("查询商品列表")
class Test_Product_query_list:
    """查询商品列表接口测试类：验证 GET /api/products/ 的成功与失败场景"""

    # 成功用例：按参数查询商品列表，校验状态码、返回条数、字段与分类
    @pytest.mark.parametrize(
        "case",
        query_data["success_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_product_query_list_success(self, client, case):
        """查询商品列表成功：校验状态码、返回条数、字段与分类"""
        # 携带查询参数请求商品列表
        resp = client.get("/api/products/", params=case["params"])
        # 校验状态码、返回体类型与条数
        assert resp.status_code == case["expected_status"]
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == case["expected_len"]
        # 若用例要求校验字段，则逐条校验字段是否存在
        if "expected_fields" in case:
            for product in data:
                for field in case["expected_fields"]:
                    assert field in product
        # 若用例要求校验分类，则校验每个商品的首个分类ID
        if "expected_category_id" in case:
            for product in data:
                assert product["categories"][0]["id"] == case["expected_category_id"]

    # 失败用例：非法参数应抛出 HTTPError 异常，并返回预期错误状态码
    @pytest.mark.parametrize(
        "case",
        query_data["fail_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_product_query_list_fail(self, client, case):
        """查询商品列表失败：非法参数应抛出 HTTPError 并返回预期错误状态码"""
        # 期望请求抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.get("/api/products/", params=case["params"])
        # 校验异常响应中的实际状态码
        assert e.value.response.status_code == case["expected_status"]
