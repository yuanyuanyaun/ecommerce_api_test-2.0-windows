"""分类管理 —— 查询分类列表接口(GET /api/categories/)的自动化测试用例。"""
import allure


@allure.feature("分类管理")
@allure.story("查询分类")
class Test_Category_query():
    """查询分类列表接口测试类：验证 GET /api/categories/ 返回全部分类"""

    @allure.title("查询全部分类")

    def test_category_query(self, client):
        """查询全部分类：校验返回列表、初始分类名称与字段"""
        # 查询全部分类
        resp = client.get("/api/categories/")
        # 校验状态码，返回体必须是列表且至少包含6条初始分类
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 6
        # 校验初始分类名称都存在于返回结果中
        names = [i["name"] for i in data]
        for name in ["电子产品", "服装", "手机", "电脑", "男装", "女装"]:
            assert name in names
        # 校验每条分类都包含 id/name/parent_id 字段
        for item in data:
            assert "id" in item
            assert "name" in item
            assert "parent_id" in item
