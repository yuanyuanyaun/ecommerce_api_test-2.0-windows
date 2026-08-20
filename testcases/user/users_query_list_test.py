"""用户管理 —— 查询用户列表接口(GET /api/users/)的自动化测试用例。

覆盖场景：默认/分页/limit 边界等成功查询，以及 skip/limit 非法值等失败查询。
"""
import pytest
import requests
import json
import allure

# 加载查询用户列表的测试数据（成功/失败两类用例）
with open('data/user/user_query_list_data.json', 'r', encoding='utf - 8') as f:
    Data = json.load(f)  # 将文件中的数据转化为字符串写入data


@allure.feature("用户管理")
@allure.story("查询用户列表")
class Test_User_query_list:
    """查询用户列表接口测试类：验证 GET /api/users/ 的成功与失败场景"""

    # 成功用例：按参数查询用户列表，校验状态码、返回条数与字段
    @pytest.mark.parametrize(
        "case",
        Data["query_success_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_user_query_list_success(self, client, case):
        """查询用户列表成功：校验状态码、返回条数与字段"""
        # 携带查询参数请求用户列表
        resp = client.get("/api/users/", params=case["params"])
        assert resp.status_code == 200
        data = resp.json()
        # 若用例要求精确条数，则校验返回条数
        if "expected_len" in case:
            assert len(data) == case["expected_len"]
        # 若用例要求最小条数，则校验返回条数不小于该值
        if "expected_min_len" in case:
            assert len(data) >= case["expected_min_len"]
        # 若用例要求校验字段，则逐条校验字段是否存在
        if "expected_fields" in case:
            for u in data:
                for f in case["expected_fields"]:
                    assert f in u

    # 失败用例：非法参数应抛出 HTTPError 异常，并返回预期错误状态码
    @pytest.mark.parametrize(
        "case",
        Data["query_fail_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_user_query_list_fail(self, client, case):
        """查询用户列表失败：非法参数应抛出 HTTPError 并返回预期错误状态码"""
        # 期望请求抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.get("/api/users/", params=case["params"])
        # 校验异常响应中的实际状态码
        assert e.value.response.status_code == case["expected_status"]
