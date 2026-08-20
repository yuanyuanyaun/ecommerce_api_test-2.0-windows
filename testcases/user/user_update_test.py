"""用户管理 —— 修改用户接口(PUT /api/users/{id})的自动化测试用例。

覆盖场景：只改 phone、改全部字段、改回当前用户名；以及用户不存在、用户名重复、密码非法、用户名改为空格等异常。
"""
import pytest
import requests
import json
import allure

# 加载修改用户的测试数据（成功/失败/预期失败三类用例）
with open('data/user/user_update_data.json', 'r', encoding='utf_8') as f:
    data = json.load(f)


@allure.feature("用户管理")
@allure.story("修改用户")
class Test_User_update:
    """修改用户接口测试类：验证 PUT /api/users/{id} 的成功、失败与预期失败场景"""

    # 成功用例：修改用户应返回200，并校验用户名/手机号，密码不应回显
    @pytest.mark.parametrize(
        'case',
        data["success_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_user_updata_success(self, client, db, case):
        """修改用户成功：校验响应字段，并核对数据库已真正落库"""
        # 发送修改用户请求
        resp = client.put("/api/users/" + str(case["user_id"]), json=case["update_payload"])
        assert resp.status_code == 200
        # 用 update_data 保存响应体，避免与模块级测试数据 data 重名
        update_data = resp.json()
        assert update_data["username"] == case["expected_username"]
        assert update_data["phone"] == case["expected_phone"]
        assert "password" not in update_data
        assert update_data["id"] == case["user_id"]

        # ========== 数据库校验：用户修改结果已真正落库 ==========
        db_user = db["one"](
            "SELECT id, username, phone FROM users WHERE id = %s",
            (case["user_id"],)
        )
        assert db_user is not None, f"用户 {case['user_id']} 在数据库中不存在"
        assert db_user["username"] == case["expected_username"]
        assert db_user["phone"] == case["expected_phone"]

    # 失败用例：非法入参应抛出 HTTPError 异常，并返回预期错误状态码
    @pytest.mark.parametrize(
        'case',
        data["fail_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_user_updata_fail(self, client, case):
        """修改用户失败：非法入参应抛出 HTTPError 并返回预期错误状态码"""
        # 期望请求抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.put("/api/users/" + str(case["user_id"]), json=case["update_payload"])
        # 校验异常响应中的实际状态码
        assert e.value.response.status_code == case["expected_status"]

    # 预期失败(xfail)用例：已知 BUG-001，用户名为空格时应返回422而非200
    @allure.issue("BUG-001")
    @pytest.mark.xfail(reason="BUG-001: 用户名为空格时，应返回422而非200")
    @pytest.mark.parametrize(
        'case',
        data["xfail_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_user_updata_xfail(self, client, case):
        """修改用户名为空格（预期失败）：已知 BUG-001，应返回422而非200"""
        # 修改用户名称为空格，期望抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.put("/api/users/" + str(case["user_id"]), json=case["update_payload"])
        assert e.value.response.status_code == case["expected_status"]
