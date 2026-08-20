"""用户管理 —— 查询单个用户接口(GET /api/users/{id})的自动化测试用例。

覆盖场景：查询存在的用户、查询不存在的用户以及各种非法 id 入参。
"""
import pytest
import json
import requests
import allure

# 加载查询单个用户的测试数据（成功/失败两类用例）
with open("data/user/user_query_single_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)


@allure.feature("用户管理")
@allure.story("查询单个用户")
class Test_User_query_single:
    """查询单个用户接口测试类：验证 GET /api/users/{id} 的成功与失败场景"""

    # 成功用例：查询存在的用户，校验用户名与手机号
    @pytest.mark.parametrize(
        'case',
        data["query_single_success_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_user_query_single_success(self, client, case):
        """查询单个用户成功：校验返回的用户名与手机号"""
        # 发送查询单个用户请求
        resp = client.get("/api/users/" + str(case["user_id"]))
        # 用 query_data 保存响应体，避免与模块级测试数据 data 重名
        query_data = resp.json()
        assert resp.status_code == 200
        assert case["expected_username"] == query_data["username"]
        assert case["expected_phone"] == query_data["phone"]

    # 失败用例：查询不存在的用户应抛出 HTTPError 异常，并返回预期错误状态码
    @pytest.mark.parametrize(
        'case',
        data["query_single_fail_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_user_query_single_fail(self, client, case):
        """查询单个用户失败：不存在的用户或非法 id 应返回预期错误状态码"""
        # 期望请求抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.get("/api/users/" + str(case["user_id"]))
        # 校验异常响应中的实际状态码
        assert e.value.response.status_code == case["expected_status"]
