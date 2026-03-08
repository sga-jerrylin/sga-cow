import json
import os
import tempfile
import time
import uuid
from urllib.parse import unquote, urlparse

import requests

from bot.molt.molt_session import MoltSessionManager
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common import memory
from common.log import logger
from config import conf
from lib.molt.molt_client import MoltClient
from models.bot import Bot


class MoltBot(Bot):
    """SGA-Molt External Agent API bot."""

    def __init__(self):
        super().__init__()
        self.client = MoltClient(
            api_key=conf().get("molt_api_key", ""),
            base_url=conf().get("molt_api_base", "http://localhost:3000"),
            agent_id=conf().get("molt_agent_id", "main"),
            timeout=conf().get("molt_timeout", 300),
        )
        self.sessions = MoltSessionManager()
        self.response_mode = conf().get("molt_response_mode", "blocking")
        self._pending_map = {}

    def reply(self, query: str, context: Context = None) -> Reply:
        if context is None or context.type not in (ContextType.TEXT, ContextType.IMAGE, ContextType.FILE, ContextType.VOICE):
            return Reply(ReplyType.ERROR, "Unsupported message type")

        if context.type == ContextType.TEXT and query in conf().get("clear_memory_commands", ["#清除记忆"]):
            session_id = context.get("session_id", "default")
            self.sessions.clear(session_id)
            return Reply(ReplyType.INFO, "记忆已清除")

        try:
            session = self.sessions.get_or_create(context)
            message, attachments = self._build_request(query, context, session)
            user = self._build_user(context, session)

            response_mode = self.response_mode if self.response_mode in ("blocking", "streaming") else "blocking"
            if response_mode == "streaming":
                return self._reply_streaming(message, user, session, attachments)
            return self._reply_blocking(message, user, session, attachments)
        except requests.HTTPError as err:
            if err.response is not None and err.response.status_code == 409:
                return Reply(ReplyType.TEXT, "The previous message is still being processed. Please wait a moment.")
            logger.error(f"[Molt] HTTP error: {err}")
            return Reply(ReplyType.ERROR, f"Molt service error: {err}")
        except Exception as err:
            logger.exception(f"[Molt] reply error: {err}")
            return Reply(ReplyType.ERROR, f"Molt service error: {err}")

    def _build_request(self, query: str, context: Context, session) -> tuple[str, list]:
        if context.type == ContextType.TEXT:
            attachments = self._build_cached_attachments(session.session_id)
            return query, attachments

        attachment = self._build_context_attachment(context)
        return "", [attachment] if attachment else []

    def _build_user(self, context: Context, session) -> dict:
        msg = context.get("msg")
        is_group = context.get("isgroup", False)

        user_id = session.user_id or context.get("session_id", "default")
        user_name = ""
        extra = {
            "platform": context.get("channel_type", conf().get("channel_type", "unknown")),
        }

        if msg is not None:
            if is_group:
                user_id = getattr(msg, "actual_user_id", None) or getattr(msg, "from_user_id", None) or user_id
                user_name = getattr(msg, "actual_user_nickname", None) or getattr(msg, "from_user_nickname", None) or ""
                extra["room_id"] = getattr(msg, "other_user_id", None) or ""
                extra["room_name"] = getattr(msg, "other_user_nickname", None) or ""
            else:
                user_id = getattr(msg, "from_user_id", None) or user_id
                user_name = getattr(msg, "from_user_nickname", None) or getattr(msg, "other_user_nickname", None) or ""

        return {
            "id": user_id,
            "name": user_name,
            "extra": extra,
        }

    def _build_cached_attachments(self, session_id: str) -> list:
        img_cache = memory.USER_IMAGE_CACHE.get(session_id)
        if not img_cache:
            return []

        memory.USER_IMAGE_CACHE[session_id] = None
        path = img_cache.get("path")
        msg = img_cache.get("msg")
        local_path = self._ensure_local_path(path, msg)
        if not local_path:
            return []

        attachment = self._upload_attachment(local_path, "image")
        return [attachment] if attachment else []

    def _build_context_attachment(self, context: Context):
        attachment_type = {
            ContextType.IMAGE: "image",
            ContextType.FILE: "file",
            ContextType.VOICE: "audio",
        }.get(context.type)
        if not attachment_type:
            return None

        local_path = self._ensure_local_path(context.content, context.get("msg"))
        if not local_path:
            return None
        return self._upload_attachment(local_path, attachment_type)

    def _ensure_local_path(self, file_path: str, msg=None):
        if not file_path:
            return None

        local_path = file_path[7:] if isinstance(file_path, str) and file_path.startswith("file://") else file_path

        if msg is not None and hasattr(msg, "prepare"):
            try:
                msg.prepare()
            except Exception as err:
                logger.warning(f"[Molt] prepare attachment failed: {err}")

        if os.path.exists(local_path):
            return local_path

        for _ in range(10):
            if os.path.exists(local_path):
                return local_path
            time.sleep(0.2)

        logger.warning(f"[Molt] attachment path not found: {local_path}")
        return None

    def _upload_attachment(self, file_path: str, attachment_type: str):
        local_path = file_path[7:] if file_path.startswith("file://") else file_path
        try:
            result = self.client.upload_file(local_path)
            return {
                "type": attachment_type,
                "transfer_method": "upload_id",
                "upload_id": result["id"],
            }
        except Exception as err:
            logger.warning(f"[Molt] upload {attachment_type} failed: {err}")
            return None

    def _reply_blocking(self, query: str, user: dict, session, attachments: list) -> Reply:
        result = self.client.chat(
            message=query,
            user=user,
            conversation_id=session.conversation_id,
            response_mode="blocking",
            attachments=attachments or None,
        )
        session.conversation_id = result.get("conversation_id", "")

        message_id = result.get("message_id", "")
        reply_attachments = result.get("attachments", [])
        if reply_attachments and message_id:
            self._pending_map[message_id] = reply_attachments

        reply = Reply(ReplyType.TEXT, result.get("answer", ""))
        reply.molt_message_id = message_id
        return reply

    def _reply_streaming(self, query: str, user: dict, session, attachments: list) -> Reply:
        response = self.client.chat(
            message=query,
            user=user,
            conversation_id=session.conversation_id,
            response_mode="streaming",
            attachments=attachments or None,
        )

        full_answer = []
        reply_attachments = []
        message_id = ""
        current_event = ""

        try:
            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue

                if raw_line.startswith("event: "):
                    current_event = raw_line[7:]
                    continue
                if not raw_line.startswith("data: "):
                    continue

                data_str = raw_line[6:]
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    logger.debug(f"[Molt] skip non-json SSE payload: {data_str}")
                    continue

                if current_event == "message":
                    full_answer.append(data.get("content", "") or data.get("answer", ""))
                elif current_event == "attachment":
                    reply_attachments.append(data.get("attachment", data))
                elif current_event == "conversation_created":
                    session.conversation_id = data.get("conversation_id", "")
                    message_id = data.get("message_id", message_id)
                elif current_event == "message_end":
                    message_id = data.get("message_id", message_id)
                    if data.get("conversation_id"):
                        session.conversation_id = data["conversation_id"]
                elif current_event == "error":
                    return Reply(ReplyType.ERROR, data.get("message", "Unknown SSE error"))
        finally:
            response.close()

        if reply_attachments and message_id:
            self._pending_map[message_id] = reply_attachments

        reply = Reply(ReplyType.TEXT, "".join(full_answer))
        reply.molt_message_id = message_id
        return reply

    def send_pending_attachments(self, reply: Reply, context: Context, channel):
        message_id = getattr(reply, "molt_message_id", None)
        if not message_id:
            return

        attachments = self._pending_map.pop(message_id, [])
        for attachment in attachments:
            try:
                attachment_reply = self._build_attachment_reply(attachment)
                if attachment_reply:
                    channel.send(attachment_reply, context)
            except Exception as err:
                logger.warning(f"[Molt] send attachment failed: {err}")

    def _build_attachment_reply(self, attachment: dict):
        payload = attachment.get("attachment", attachment)
        url = payload.get("url") or payload.get("download_url")
        if not url:
            return None
        if not url.startswith("http"):
            url = f"{self.client.base_url}{url}"

        attachment_type = payload.get("type", "file")
        filename = payload.get("filename") or self._guess_filename(url, attachment_type)

        if attachment_type == "image":
            image_storage = self._download_image(url, filename)
            if image_storage is None:
                return None
            return Reply(ReplyType.IMAGE, image_storage)

        local_path = self._download_to_tmp(url, filename)
        if not local_path:
            return None

        reply_type = {
            "audio": ReplyType.VOICE,
            "file": ReplyType.FILE,
            "video": ReplyType.FILE,
        }.get(attachment_type, ReplyType.FILE)
        return Reply(reply_type, local_path)

    def _download_image(self, url: str, filename: str):
        response = None
        try:
            headers = {}
            if url.startswith(self.client.base_url):
                headers["Authorization"] = f"Bearer {self.client.api_key}"
            response = self.client.session.get(
                url,
                headers=headers,
                timeout=30,
                stream=True,
            )
            response.raise_for_status()

            max_size = 50 * 1024 * 1024
            image_storage = io.BytesIO()
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                downloaded += len(chunk)
                if downloaded > max_size:
                    logger.warning(f"[Molt] image too large: {filename}")
                    return None
                image_storage.write(chunk)

            image_storage.seek(0)
            image_storage.name = filename
            return image_storage
        except Exception as err:
            logger.warning(f"[Molt] image download failed: {err}")
            return None
        finally:
            if response is not None:
                response.close()

    def _download_to_tmp(self, url: str, filename: str):
        response = None
        try:
            headers = {}
            if url.startswith(self.client.base_url):
                headers["Authorization"] = f"Bearer {self.client.api_key}"
            response = self.client.session.get(
                url,
                headers=headers,
                timeout=30,
                stream=True,
            )
            response.raise_for_status()

            max_size = 50 * 1024 * 1024
            content_length = int(response.headers.get("content-length", 0))
            if content_length > max_size:
                logger.warning(f"[Molt] file too large: {content_length} bytes")
                return None

            safe_name = os.path.basename(filename) or f"attachment_{uuid.uuid4().hex}"
            tmp_path = os.path.join(tempfile.gettempdir(), f"molt_{uuid.uuid4().hex}_{safe_name}")
            downloaded = 0
            with open(tmp_path, "wb") as file_obj:
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    downloaded += len(chunk)
                    if downloaded > max_size:
                        logger.warning("[Molt] file exceeded max size during download")
                        return None
                    file_obj.write(chunk)
            return tmp_path
        except Exception as err:
            logger.warning(f"[Molt] download failed: {err}")
            return None
        finally:
            if response is not None:
                response.close()

    def _guess_filename(self, url: str, attachment_type: str) -> str:
        path = unquote(urlparse(url).path)
        filename = os.path.basename(path)
        if filename:
            return filename
        return {
            "image": "image.png",
            "audio": "audio.bin",
            "video": "video.bin",
        }.get(attachment_type, "file.bin")
