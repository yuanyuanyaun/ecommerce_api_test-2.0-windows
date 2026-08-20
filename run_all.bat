@echo off
chcp 65001 >nul
setlocal

REM ============================================================
REM  电商后台管理系统 —— 一键运行脚本
REM  1) 启动被测系统 (uvicorn)
REM  2) 运行 pytest 测试脚本
REM  3) 生成并打开 Allure 测试报告
REM ============================================================

REM 切换到脚本所在目录（保证双击运行时路径正确）
cd /d "%~dp0"

REM ---------- 连接配置（按需修改） ----------
REM 通过环境变量统一传给被测系统(app/main.py)和测试端(config/setting.py)
set "SERVER_HOST=127.0.0.1"
set "SERVER_PORT=8000"
set "BASE_URL=http://%SERVER_HOST%:%SERVER_PORT%"

set "DB_HOST=127.0.0.1"
set "DB_PORT=3306"
set "DB_USER=root"
REM 默认密码 123456（与 README 一致）；若数据库密码不同，请先执行 set DB_PASSWORD=你的密码 再运行本脚本
if not defined DB_PASSWORD set "DB_PASSWORD=123456"
set "DB_NAME=ecommerce_db"

REM ---------- 工具路径 ----------
set "PYTHON=%CD%\.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"

set "PYTEST_EXIT=1"

echo.
echo ============================================================
echo  [1/3] 启动被测系统 uvicorn (http://%SERVER_HOST%:%SERVER_PORT%)
echo ============================================================

REM 先清理可能占用端口的残留进程，避免端口冲突
call :kill_port %SERVER_PORT%

start "ecommerce-api-server" /min "%PYTHON%" -m uvicorn app.main:app --host 0.0.0.0 --port %SERVER_PORT%

echo 等待被测系统就绪...
set /a RETRY=0
:WAIT_LOOP
set /a RETRY+=1
curl -s -o nul "%BASE_URL%/" 2>nul
if not errorlevel 1 goto SERVER_READY
if %RETRY% GEQ 30 goto SERVER_TIMEOUT
ping -n 3 127.0.0.1 >nul
goto WAIT_LOOP

:SERVER_READY
echo 被测系统已就绪: %BASE_URL%
echo.

echo ============================================================
echo  [2/3] 运行测试脚本 pytest
echo ============================================================
"%PYTHON%" -m pytest
set "PYTEST_EXIT=%errorlevel%"
echo.

if not exist "reports\allure-results" (
    echo [警告] 未生成 allure 结果，跳过报告生成。
    goto SERVER_STOP
)

echo ============================================================
echo  [3/3] 生成并打开 Allure 测试报告
echo ============================================================
call allure generate reports\allure-results -o reports\allure-report --clean
if errorlevel 1 (
    echo [错误] Allure 报告生成失败，请确认已安装 allure 命令行工具。
    goto SERVER_STOP
)

start "Allure Report" cmd /k "allure open reports\allure-report"
echo 报告已生成并启动，浏览器即将自动打开。
echo （Allure 窗口关闭后报告服务随之停止）
goto SERVER_STOP

:SERVER_TIMEOUT
echo [错误] 被测系统启动超时，请检查端口 %SERVER_PORT% 是否被占用或依赖是否安装。
goto SERVER_STOP

:SERVER_STOP
echo.
echo 停止被测系统...
call :kill_port %SERVER_PORT%
echo 全部完成。
pause
exit /b %PYTEST_EXIT%

REM ---------- 根据端口号结束监听该端口的进程 ----------
:kill_port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%1" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
exit /b 0
