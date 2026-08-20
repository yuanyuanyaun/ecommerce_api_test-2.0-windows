import requests
from config.setting import BASE_URL,TIMEOUT,LOG_LEVEL
import logging
# 配置日志格式：设置输出的内容为：时间，级别和内容，方便调试
logging.basicConfig(level=LOG_LEVEL,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class APIClient:
    """封装 requests，统一处理日志和异常"""

    def __init__(self, base_url=BASE_URL, timeout=TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()   # 保持会话（以后加登录会用到）

    def _request(self, method, path, **kwargs):
        """内部通用请求方法，所有公开方法都会调它"""
        url = f"{self.base_url}{path}" #拼接url地址
        kwargs.setdefault("timeout", self.timeout)  #补充默认超时设定

        # 打印请求信息
        logger.info(f"{method} {url}")

        try:
            resp = self.session.request(method, url, **kwargs)  #获取响应内容
            resp.raise_for_status()   # 4xx/5xx 自动抛 HTTPError
            logger.info(f"返回码: {resp.status_code}") #自动打印返回码
            return resp
        except requests.ConnectionError:
            logger.error(f"连接失败: {url}")
            raise
        except requests.Timeout:
            logger.error(f"请求超时: {url}")
            raise
        except requests.HTTPError as e:
            logger.error(f"HTTP错误，返回码为: {resp.status_code}, 响应内容: {resp.text}")
            raise

    def get(self, path, params=None, **kwargs):
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path, json=None, **kwargs):
        return self._request("POST", path, json=json, **kwargs)

    def put(self, path, json=None, **kwargs):
        return self._request("PUT", path, json=json, **kwargs)

    def delete(self, path, **kwargs):
        return self._request("DELETE", path, **kwargs)