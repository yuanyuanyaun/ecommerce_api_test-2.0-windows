"""用户管理 —— 删除用户接口(DELETE /api/users/{id})的自动化测试用例。

覆盖场景：删除无订单用户、删除不存在的用户，以及删除有关联订单的用户（预期失败）。
"""
import pytest
import json
import requests
import allure

# 加载删除用户的测试数据（成功/失败/预期失败三类用例）
with open("data/user/user_delete_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)


@allure.feature("用户管理")
@allure.story("删除用户")
class Test_User_delete:
    """删除用户接口测试类：验证 DELETE /api/users/{id} 的成功、失败与预期失败场景"""

    # 成功用例：删除无订单关联的用户应成功，且删除后再查询返回404
    @pytest.mark.parametrize(
        'case',
        data["delete_success_cases"],
        ids=lambda case: case["name"],
    )
    @allure.title("{case[name]}")
    def test_user_delete_success(self, client, db, case):
        """删除用户成功：校验删除提示，并核对数据库已真正删除"""
        # 发送删除用户请求，校验状态码与返回提示
        resp = client.delete("/api/users/" + str(case['user_id']))
        assert resp.status_code == case["expected_status"]
        assert case["expected_message"] in resp.text
        # 删除后再查询，应抛出 HTTPError 且状态码为404
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.get(f"/api/users/{case['user_id']}")
        assert e.value.response.status_code == 404

        # ========== 数据库校验：确认用户已从 users 表中删除 ==========
        db_user = db["one"]("SELECT id FROM users WHERE id = %s", (case['user_id'],))
        assert db_user is None, f"用户 {case['user_id']} 删除后仍存在于数据库"

    # 失败用例：删除不存在或非法用户应被拒绝，返回预期错误状态码
    @pytest.mark.parametrize(
        'case',
        data["delete_fail_cases"],
        ids=lambda case: case["name"],
    )
    @allure.title("{case[name]}")
    def test_user_delete_fail(self, client, case):
        """删除用户失败：不存在或非法用户应返回预期错误状态码"""
        # 期望删除请求抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.delete("/api/users/" + str(case['user_id']))
        # 校验异常响应中的实际状态码
        assert e.value.response.status_code == case["expected_status"]


    # 预期失败(xfail)用例：已知 BUG-002，删除有订单的用户应返回400而非500
    @pytest.mark.parametrize(
        'case',
        data["delete_xfail_cases"],
        ids=lambda case: case["name"],
    )
    @allure.title("{case[name]}")
    @allure.issue("BUG-002")
    @pytest.mark.xfail(reason="BUG-002: 删除有订单用户时，应返回400而非500")
    def test_user_delete_xfail(self, client, db, case):
        """删除有订单用户（预期失败）：已知 BUG-002，应返回400而非500"""
        # 删除有关联订单的用户，期望抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.delete("/api/users/" + str(case['user_id']))
        assert e.value.response.status_code == case["expected_status"]
        # 用户应仍然存在，查询返回200
        resp = client.get(f"/api/users/{case['user_id']}")
        assert resp.status_code == 200

        # ========== 数据库校验：删除失败的用户应仍然存在于数据库中 ==========
        db_user = db["one"]("SELECT id FROM users WHERE id = %s", (case['user_id'],))
        assert db_user is not None, f"用户 {case['user_id']} 不应被删除"
