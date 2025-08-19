# encoding:utf-8
import json
import time
import requests
from typing import Optional, Dict, Any, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from common.log import logger


class DifyClient:
    """Dify API客户端基类"""

    def __init__(self, api_key: str, api_base: str = "https://api.dify.ai/v1"):
        self.api_key = api_key
        self.api_base = api_base.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # 创建带重试机制的session
        self.session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],  # 新版本使用allowed_methods
            backoff_factor=1
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 设置默认超时
        self.timeout = 30
    
    def _send_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """发送HTTP请求，带重试和错误处理"""
        url = f"{self.api_base}{endpoint}"

        # 设置默认headers
        if 'headers' not in kwargs:
            kwargs['headers'] = self.headers.copy()
        else:
            kwargs['headers'].update(self.headers)

        # 设置超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        start_time = time.time()

        try:
            response = self.session.request(method, url, **kwargs)

            # 记录请求时间
            elapsed_time = time.time() - start_time
            logger.debug(f"[DIFY] {method} {url} - Status: {response.status_code}, Time: {elapsed_time:.2f}s")

            # 检查响应状态
            if response.status_code == 429:
                logger.warning(f"[DIFY] Rate limit exceeded, waiting...")
                time.sleep(2)  # 等待2秒后重试

            return response

        except requests.exceptions.Timeout as e:
            logger.error(f"[DIFY] Request timeout after {self.timeout}s: {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[DIFY] Connection error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"[DIFY] Request failed: {e}")
            raise
    
    def file_upload(self, user: str, files: Dict[str, Any]) -> requests.Response:
        """上传文件到Dify"""
        endpoint = "/files/upload"
        
        # 文件上传不使用JSON Content-Type
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {'user': user}
        
        return self._send_request("POST", endpoint, headers=headers, data=data, files=files)

    def health_check(self) -> bool:
        """检查Dify服务健康状态"""
        try:
            # 简单的健康检查，发送一个轻量级请求
            response = self._send_request("GET", "/", timeout=5)
            return response.status_code < 500
        except Exception as e:
            logger.warning(f"[DIFY] Health check failed: {e}")
            return False

    def close(self):
        """关闭session"""
        if hasattr(self, 'session'):
            self.session.close()


class ChatClient(DifyClient):
    """Dify聊天客户端"""
    
    def __init__(self, api_key: str, api_base: str = "https://api.dify.ai/v1"):
        super().__init__(api_key, api_base)
    
    def create_chat_message(
        self,
        inputs: Dict[str, Any],
        query: str,
        user: str,
        response_mode: str = "blocking",
        conversation_id: str = "",
        files: Optional[List[Dict[str, Any]]] = None
    ) -> requests.Response:
        """创建聊天消息"""
        endpoint = "/chat-messages"
        
        payload = {
            "inputs": inputs,
            "query": query,
            "user": user,
            "response_mode": response_mode
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        if files:
            payload["files"] = files
        
        # 对于streaming模式，需要特殊处理
        if response_mode == "streaming":
            kwargs = {
                "json": payload,
                "stream": True,
                "headers": self.headers.copy()
            }
            return self._send_request("POST", endpoint, **kwargs)
        else:
            return self._send_request("POST", endpoint, json=payload)
    
    def get_conversation_messages(
        self,
        conversation_id: str,
        user: str,
        first_id: Optional[str] = None,
        limit: int = 20
    ) -> requests.Response:
        """获取会话消息历史"""
        endpoint = f"/messages"
        
        params = {
            "conversation_id": conversation_id,
            "user": user,
            "limit": limit
        }
        
        if first_id:
            params["first_id"] = first_id
        
        return self._send_request("GET", endpoint, params=params)
    
    def get_conversations(
        self,
        user: str,
        last_id: Optional[str] = None,
        limit: int = 20,
        pinned: Optional[bool] = None
    ) -> requests.Response:
        """获取会话列表"""
        endpoint = "/conversations"
        
        params = {
            "user": user,
            "limit": limit
        }
        
        if last_id:
            params["last_id"] = last_id
        
        if pinned is not None:
            params["pinned"] = pinned
        
        return self._send_request("GET", endpoint, params=params)
    
    def rename_conversation(
        self,
        conversation_id: str,
        name: str,
        user: str
    ) -> requests.Response:
        """重命名会话"""
        endpoint = f"/conversations/{conversation_id}/name"
        
        payload = {
            "name": name,
            "user": user
        }
        
        return self._send_request("POST", endpoint, json=payload)
    
    def delete_conversation(
        self,
        conversation_id: str,
        user: str
    ) -> requests.Response:
        """删除会话"""
        endpoint = f"/conversations/{conversation_id}"
        
        data = {"user": user}
        
        return self._send_request("DELETE", endpoint, json=data)


class WorkflowClient(DifyClient):
    """Dify工作流客户端"""
    
    def __init__(self, api_key: str, api_base: str = "https://api.dify.ai/v1"):
        super().__init__(api_key, api_base)
    
    def run_workflow(
        self,
        inputs: Dict[str, Any],
        user: str,
        response_mode: str = "blocking",
        files: Optional[List[Dict[str, Any]]] = None
    ) -> requests.Response:
        """运行工作流"""
        endpoint = "/workflows/run"
        
        payload = {
            "inputs": inputs,
            "user": user,
            "response_mode": response_mode
        }
        
        if files:
            payload["files"] = files
        
        # 对于streaming模式，需要特殊处理
        if response_mode == "streaming":
            kwargs = {
                "json": payload,
                "stream": True,
                "headers": self.headers.copy()
            }
            return self._send_request("POST", endpoint, **kwargs)
        else:
            return self._send_request("POST", endpoint, json=payload)
    
    def get_workflow_runs(
        self,
        user: str,
        last_id: Optional[str] = None,
        limit: int = 20
    ) -> requests.Response:
        """获取工作流运行历史"""
        endpoint = "/workflows/runs"
        
        params = {
            "user": user,
            "limit": limit
        }
        
        if last_id:
            params["last_id"] = last_id
        
        return self._send_request("GET", endpoint, params=params)


class CompletionClient(DifyClient):
    """Dify文本补全客户端"""
    
    def __init__(self, api_key: str, api_base: str = "https://api.dify.ai/v1"):
        super().__init__(api_key, api_base)
    
    def create_completion_message(
        self,
        inputs: Dict[str, Any],
        user: str,
        response_mode: str = "blocking",
        files: Optional[List[Dict[str, Any]]] = None
    ) -> requests.Response:
        """创建文本补全消息"""
        endpoint = "/completion-messages"
        
        payload = {
            "inputs": inputs,
            "user": user,
            "response_mode": response_mode
        }
        
        if files:
            payload["files"] = files
        
        # 对于streaming模式，需要特殊处理
        if response_mode == "streaming":
            kwargs = {
                "json": payload,
                "stream": True,
                "headers": self.headers.copy()
            }
            return self._send_request("POST", endpoint, **kwargs)
        else:
            return self._send_request("POST", endpoint, json=payload)
