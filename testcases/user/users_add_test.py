"""用户管理 —— 新增用户接口(POST /api/users/)的自动化测试用例。

覆盖场景：
- 成功：正常添加、不填电话、密码/用户名/电话边界长度、特殊符号；
- 失败：重复用户名、非法入参（空格/空串/超长/密码位数/电话超长）。
"""
import pytest
import requests
import json
import allure

# 加载新增用户的测试数据（成功/失败两类用例）
with open('data/user/user_add_data.json', 'r', encoding='utf - 8') as f:
    data = json.load(f)  # 将文件中的数据转化为字符串写入data


@allure.feature("用户管理")
@allure.story("添加用户")
class Test_User_add:
    """新增用户接口测试类：验证 POST /api/users/ 的成功与失败场景"""

    # 成功用例：新增用户应返回201，并校验用户名与手机号（密码不应回显）
    @pytest.mark.parametrize(
        "case",
        data["post_success_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_user_add_success(self, client, db, case):
        """新增用户成功：校验响应字段，并核对数据库已真正写入"""
        # 发送新增用户请求
        resp = client.post("/api/users/", json=case["payload"])
        assert resp.status_code == 201
        # 用 add_data 保存响应体，避免与模块级测试数据 data 重名
        add_data = resp.json()
        # 校验用户名，且响应中不应回显密码
        assert add_data["username"] == case["payload"]["username"]
        assert add_data.get("password") is None
        # 若请求带手机号，则校验返回的手机号
        if "phone" in case["payload"]:
            assert add_data["phone"] == case["payload"]["phone"]

        # ========== 数据库校验：确认新用户已真正写入 users 表 ==========
        db_user = db["one"](
            "SELECT id, username, phone FROM users WHERE username = %s",
            (case["payload"]["username"],)
        )
        assert db_user is not None, f"用户 {case['payload']['username']} 未写入数据库"
        assert db_user["username"] == case["payload"]["username"]
        # 若请求带手机号，则校验数据库中的手机号一致
        if "phone" in case["payload"]:
            assert db_user["phone"] == case["payload"]["phone"]

    # 失败用例：非法入参应抛出 HTTPError 异常，并返回预期错误状态码
    @pytest.mark.parametrize(
        "case",
        data["post_fail_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_user_add_fail(self, client, case):
        """新增用户失败：非法入参应抛出 HTTPError 并返回预期错误状态码"""
        # 期望请求抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.post("/api/users/", json=case["payload"])
        # 校验异常响应中的实际状态码
        assert e.value.response.status_code == case["expected_status"]
