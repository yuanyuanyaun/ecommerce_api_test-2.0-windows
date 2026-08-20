"""订单管理 —— 查询订单列表接口(GET /api/orders/)的自动化测试用例。

覆盖场景：默认查询、按状态/用户筛选、组合筛选以及无结果组合筛选。
"""
import pytest
import json
import allure

# 加载查询订单列表的测试数据
with open('data/order/order_query_list_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)


@allure.feature("订单管理")
@allure.story("查询订单列表")
class Test_Order_query_list:
    """查询订单列表接口测试类：验证 GET /api/orders/ 的成功场景"""

    # 成功用例：按参数查询订单列表，校验状态码、返回条数与字段
    @pytest.mark.parametrize(
        "case",
        data["success_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_order_query_list_success(self, client, case):
        """查询订单列表成功：校验状态码、返回条数、字段与用户ID"""
        # 携带查询参数请求订单列表
        resp = client.get('/api/orders/', params=case["params"])
        # 校验状态码、返回体类型与条数
        assert resp.status_code == case['expected_status']
        query_data = resp.json()
        assert isinstance(query_data, list)
        assert len(query_data) == case["expected_len"]
        # 若用例要求校验字段，则逐条校验字段是否存在
        if "expected_fields" in case:
            for order in query_data:
                for field in case["expected_fields"]:
                    assert field in order
        # 若用例要求校验用户ID，则比对返回订单的用户ID序列
        if "expected_user_ids" in case:
            ids = [id["user_id"] for id in query_data]
            assert ids == case["expected_user_ids"]
