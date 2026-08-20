"""
全局配置（测试端）

所有连接信息都可通过环境变量覆盖，默认指向本机 127.0.0.1，
方便他人 clone 后无需改代码即可本地运行。

如果被测靶场在虚拟机里，设置对应环境变量即可，例如：
    $env:BASE_URL = "http://192.168.80.130:8000"
    $env:DB_HOST  = "192.168.80.130"
"""
import os

# 被测服务地址
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
# 请求超时（秒）
TIMEOUT = int(os.getenv("TIMEOUT", "10"))
# 日志显示等级
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 数据库配置（被测靶场数据库所在机器）
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_NAME = os.getenv("DB_NAME", "ecommerce_db")

if __name__ == "__main__":
    print("OK")