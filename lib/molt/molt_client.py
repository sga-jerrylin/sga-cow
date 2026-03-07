import uuid

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class MoltClient:
    """SGA-Molt External Agent API client."""

    def __init__(self, api_key: str, base_url: str, agent_id: str, timeout: int = 300):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id
        self.timeout = timeout
        self.session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["DELETE", "GET", "HEAD", "OPTIONS", "POST"]),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _headers(self, idempotency_key=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _agent_url(self, path: str) -> str:
        return f"{self.base_url}/api/v1/agents/{self.agent_id}{path}"

    def chat(
        self,
        message: str,
        user: dict,
        conversation_id: str = "",
        response_mode: str = "blocking",
        attachments: list = None,
        options: dict = None,
        idempotency_key: str = None,
    ):
        body = {
            "message": message,
            "conversation_id": conversation_id,
            "response_mode": response_mode,
            "user": user,
        }
        if attachments:
            body["attachments"] = attachments
        if options:
            body["options"] = options

        headers = self._headers(idempotency_key or str(uuid.uuid4()))
        response = self.session.post(
            self._agent_url("/chat"),
            json=body,
            headers=headers,
            timeout=self.timeout,
            stream=response_mode == "streaming",
        )
        response.raise_for_status()
        if response_mode == "streaming":
            return response
        return response.json()

    def upload_file(self, file_path: str, purpose: str = "chat") -> dict:
        with open(file_path, "rb") as file_obj:
            response = self.session.post(
                f"{self.base_url}/api/v1/files/upload",
                files={"file": file_obj},
                data={"purpose": purpose},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
        response.raise_for_status()
        return response.json()

    def list_conversations(self, user_id: str, limit: int = 20, offset: int = 0) -> dict:
        response = self.session.get(
            self._agent_url("/conversations"),
            headers=self._headers(),
            params={"user_id": user_id, "limit": limit, "offset": offset},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_messages(self, conversation_id: str, user_id: str, limit: int = 50) -> dict:
        response = self.session.get(
            self._agent_url(f"/conversations/{conversation_id}/messages"),
            headers=self._headers(),
            params={"user_id": user_id, "limit": limit},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def delete_conversation(self, conversation_id: str):
        response = self.session.delete(
            self._agent_url(f"/conversations/{conversation_id}"),
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()

    def get_agent_info(self) -> dict:
        response = self.session.get(
            self._agent_url(""),
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def stop(self, message_id: str):
        response = self.session.post(
            self._agent_url(f"/chat/{message_id}/stop"),
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
