"""分类管理 —— 新增分类接口(POST /api/categories/)的自动化测试用例。

覆盖场景：添加顶级分类、添加子分类；以及父分类不存在、名称超长、空串/空格名称（预期失败）等。
"""
import json
import requests
import pytest
import allure

# 加载新增分类的测试数据（成功/失败/预期失败三类用例）
with open("data/category/category_add_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)


@allure.feature("分类管理")
@allure.story("添加分类")
class Test_Category_add:
    """新增分类接口测试类：验证 POST /api/categories/ 的成功、失败与预期失败场景"""

    # 成功用例：新增分类应返回预期状态码，并正确回显名称与父分类ID
    @pytest.mark.parametrize(
        "case",
        data["success_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_category_add_success(self, client, db, case):
        """新增分类成功：校验响应字段，并核对数据库已真正写入"""
        # 发送新增分类请求
        resp = client.post('/api/categories/', json=case["payload"])
        # 校验返回的状态码与字段内容
        assert resp.status_code == case["expected_status"]
        # 用 add_data 保存响应体，避免与模块级测试数据 data 重名
        add_data = resp.json()
        assert add_data["name"] == case["payload"]["name"]
        assert add_data["parent_id"] == case["payload"]["parent_id"]

        # ========== 数据库校验：新增分类已写入 categories 表 ==========
        db_cat = db["one"](
            "SELECT id, name, parent_id FROM categories WHERE name = %s AND parent_id = %s",
            (case["payload"]["name"], case["payload"]["parent_id"])
        )
        assert db_cat is not None, f"分类 {case['payload']['name']} 未写入数据库"
        assert db_cat["name"] == case["payload"]["name"]
        assert db_cat["parent_id"] == case["payload"]["parent_id"]

    # 失败用例：非法入参应抛出 HTTPError 异常，并返回预期错误状态码
    @pytest.mark.parametrize(
        "case",
        data["fail_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_category_add_fail(self, client, case):
        """新增分类失败：非法入参应抛出 HTTPError 并返回预期错误状态码"""
        # 期望请求抛出 HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.post('/api/categories/', json=case["payload"])

        # 校验异常响应中的实际状态码
        assert e.value.response.status_code == case["expected_status"]

    # 预期失败(xfail)用例：已知 BUG-003/004，空/空格分类名应返回422而非201，故标记为 xfail
    @allure.issue("BUG-003/004")
    @pytest.mark.xfail(reason="BUG-003/004:添加分类名称为空字符串或空格字符串时，应返回422而非201")
    @pytest.mark.parametrize(
        "case",
        data["xfail_cases"],
        ids=lambda case: case["name"]
    )
    @allure.title("{case[name]}")
    def test_category_add_xfail(self, client, case):
        """空/空格分类名（预期失败）：已知 BUG-003/004，应返回422而非201"""
        with pytest.raises(requests.exceptions.HTTPError) as e:
            client.post('/api/categories/', json=case["payload"])
        assert e.value.response.status_code == case["expected_status"]
