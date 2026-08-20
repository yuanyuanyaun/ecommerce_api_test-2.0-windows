# 电商后台管理系统 —— 接口自动化测试靶场

一套完整的「被测系统 + 自动化测试」学习/练习项目：

- `app/`：被测系统（FastAPI 电商后台，测试靶场）
- `testcases/`：接口自动化测试（pytest + allure）
- `data/`：测试数据（JSON）
- `utils/`：API 客户端与数据库工具
- `scripts/reset_db.sql`：建库建表 + 种子数据
- `run_all.bat`：Windows 一键运行脚本

## 技术栈

| 端 | 技术 |
| --- | --- |
| 被测系统 | FastAPI + SQLAlchemy + MySQL / MariaDB |
| 测试端 | pytest + allure-pytest + requests + pymysql |
| 测试报告 | Allure（需要 Java 环境） |

## 目录结构

```
ecommerce_api_test_dfy/
├── app/
│   └── main.py           # 被测系统（靶场）
├── config/
│   └── setting.py        # 测试端配置（可用环境变量覆盖）
├── data/                 # 测试数据 JSON
├── scripts/
│   └── reset_db.sql      # 建库建表 + 种子数据
├── testcases/            # 测试脚本
│   ├── user/  product/  order/  category/
│   └── sys_test.py
├── utils/
│   ├── api_client.py     # requests 封装
│   └── db_helper.py      # pymysql 数据库操作
├── pytest.ini
├── run_all.bat           # 一键运行脚本（Windows）
├── requirements.txt
└── README.md
```

## 环境准备

1. **Python 3.10+**（本项目开发用 3.14）
2. **MySQL / MariaDB**（默认连接本机 `127.0.0.1:3306`，账号 `root`，密码 `123456`）
3. **Java 8+**（Allure 报告依赖）
4. **Allure 命令行工具**（安装后执行 `allure --version` 应能输出版本号）

项目本地使用了虚拟环境 `.venv/`（已被 `.gitignore` 忽略，不会提交到 GitHub）。clone 后可按下面方式自己创建：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

> 以下命令默认已激活虚拟环境；未激活时请使用 `.venv\Scripts\python.exe -m pytest` 这类完整路径。

## 快速开始

### 方式一：Windows 一键运行（推荐）

直接双击 `run_all.bat`，脚本会自动完成：

1. 启动被测系统（uvicorn，端口 8000）
2. 运行 pytest 测试脚本
3. 生成并打开 Allure 测试报告
4. 测试结束后自动停止被测系统

> 如果数据库密码不是默认的 `123456`，先打开一个 cmd 设置环境变量，再运行脚本：

```cmd
set DB_PASSWORD=你的密码
run_all.bat
```

### 方式二：手动四步

```bash
# 1.（可选）建库 + 导入种子数据
mysql -uroot -p123456 < scripts/reset_db.sql

# 2. 启动被测系统（另开一个终端）
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. 运行测试（在项目根目录）
pytest

# 4. 生成并查看 Allure 报告
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

> 第 1 步可以跳过：运行 `pytest` 时会自动执行 `scripts/reset_db.sql` 重置数据库（见 `conftest.py`）。

## 数据库配置

被测系统与测试端均默认连接 `root/123456@127.0.0.1:3306/ecommerce_db`，全部支持**环境变量覆盖**：

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `BASE_URL` | `http://127.0.0.1:8000` | 被测服务地址 |
| `TIMEOUT` | `10` | 请求超时（秒） |
| `LOG_LEVEL` | `INFO` | 日志等级 |
| `DB_HOST` | `127.0.0.1` | 数据库地址 |
| `DB_PORT` | `3306` | 数据库端口 |
| `DB_USER` | `root` | 数据库用户 |
| `DB_PASSWORD` | `123456` | 数据库密码 |
| `DB_NAME` | `ecommerce_db` | 数据库名 |

如果被测系统/数据库跑在**虚拟机**上，例如 IP 为 `192.168.80.130`：

```cmd
REM cmd
set BASE_URL=http://192.168.80.130:8000
set DB_HOST=192.168.80.130
set DB_PASSWORD=123456
```

```powershell
# PowerShell
$env:BASE_URL = "http://192.168.80.130:8000"
$env:DB_HOST  = "192.168.80.130"
$env:DB_PASSWORD = "123456"
```

设置后再运行 `pytest`（或 `run_all.bat`）即可。

> 注意：测试会先通过 `utils/db_helper.py` 执行 `scripts/reset_db.sql` 重置数据库，因此数据库需允许远程连接（若跑在虚拟机上）。

## 常见问题（FAQ）

**Q1：双击 `run_all.bat` 提示「被测系统启动超时」？**

- 检查 8000 端口是否被占用：`netstat -ano | findstr :8000`
- 检查依赖是否安装：`pip install -r requirements.txt`
- 检查 MySQL 是否已启动。

**Q2：报错 `Access denied for user 'root'@'localhost'`？**

数据库密码不是默认的 `123456`。设置环境变量 `DB_PASSWORD`（见上文），或直接修改 `config/setting.py` 与 `app/main.py` 中的默认值。

**Q3：提示 `'allure' 不是内部或外部命令`？**

未安装 Allure 或未加入 PATH。请先安装 Java，再下载 Allure 并配置 PATH，执行 `allure --version` 验证。

**Q4：测试大量失败，日志提示数据库连接错误？**

确认 MySQL 已启动、账号密码正确、数据库 `ecommerce_db` 可创建（`reset_db.sql` 会自动建库建表，需要 root 权限）。

**Q5：测试用例里的中文乱码？**

终端编码问题，设置代码页：`chcp 65001`（`run_all.bat` 已内置）。

## 已知问题（测试靶场的「BUG」）

- BUG-001：用户名为空格时应返回 422，实际返回 200
- BUG-002：删除有订单的用户应返回 400，实际返回 500
- BUG-003/004：空/空格分类名应返回 422，实际返回 201
- BUG-005/006/007：删除仅关联已完成/已发货/已取消订单的商品，后端未正确处理

> 对应用例在测试代码中已用 `@pytest.mark.xfail` 标记为「预期失败」，正常跑测试会显示 `xfailed`，不影响整体结果（实测 109 passed / 7 xfailed）。
