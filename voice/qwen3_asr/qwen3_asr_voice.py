# -*- coding: utf-8 -*-
"""
Qwen3-ASR HTTP voice service adapter.
"""

import base64
import json
import mimetypes
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from voice.voice import Voice


class Qwen3AsrVoice(Voice):
    def __init__(self):
        local_config = self._load_local_config()

        self.api_base = (conf().get("qwen3_asr_api_base", local_config.get("qwen3_asr_api_base", "http://127.0.0.1:8001")) or "").rstrip("/")
        self.api_path = conf().get("qwen3_asr_api_path", local_config.get("qwen3_asr_api_path", "/v1/asr/transcribe"))
        self.fallback_path = conf().get("qwen3_asr_fallback_path", local_config.get("qwen3_asr_fallback_path", "/transcribe"))
        self.health_path = conf().get("qwen3_asr_health_path", local_config.get("qwen3_asr_health_path", "/healthz"))

        self.request_timeout = max(1.0, float(conf().get("qwen3_asr_timeout", local_config.get("qwen3_asr_timeout", 120))))
        self.connect_timeout = max(1.0, float(conf().get("qwen3_asr_connect_timeout", local_config.get("qwen3_asr_connect_timeout", 8))))
        self.max_retries = max(0, int(conf().get("qwen3_asr_retries", local_config.get("qwen3_asr_retries", 2))))
        self.retry_backoff = float(conf().get("qwen3_asr_retry_backoff", local_config.get("qwen3_asr_retry_backoff", 0.8)))
        self.verify_ssl = bool(conf().get("qwen3_asr_verify_ssl", local_config.get("qwen3_asr_verify_ssl", True)))

        self.enable_healthcheck = bool(conf().get("qwen3_asr_healthcheck", local_config.get("qwen3_asr_healthcheck", True)))
        self.healthcheck_interval = int(conf().get("qwen3_asr_healthcheck_interval", local_config.get("qwen3_asr_healthcheck_interval", 30)))

        self.language = conf().get("qwen3_asr_language", local_config.get("qwen3_asr_language", None))
        self.context_text = conf().get("qwen3_asr_context", local_config.get("qwen3_asr_context", ""))
        self.return_time_stamps = bool(conf().get("qwen3_asr_return_time_stamps", local_config.get("qwen3_asr_return_time_stamps", False)))
        self.audio_transport = (conf().get("qwen3_asr_audio_transport", local_config.get("qwen3_asr_audio_transport", "base64")) or "base64").lower()
        if self.audio_transport not in ("base64", "path", "data_url"):
            logger.warning("[Qwen3-ASR] Unknown audio transport '%s', fallback to base64", self.audio_transport)
            self.audio_transport = "base64"

        self.api_key = conf().get("qwen3_asr_api_key", local_config.get("qwen3_asr_api_key", ""))
        self.auth_header = conf().get("qwen3_asr_auth_header", local_config.get("qwen3_asr_auth_header", "Authorization"))

        self._last_health_ts = 0.0
        self._last_health_ready = None
        self.session = requests.Session()

        logger.info(
            "[Qwen3-ASR] Initialized: base=%s, path=%s, fallback=%s, retries=%s, audio_transport=%s",
            self.api_base,
            self.api_path,
            self.fallback_path,
            self.max_retries,
            self.audio_transport,
        )

    def _load_local_config(self) -> Dict[str, Any]:
        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, "config.json")
        if not os.path.exists(config_path):
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("[Qwen3-ASR] Failed to load local config: %s", e)
            return {}

    def _normalize_path(self, path: str) -> str:
        path = path or ""
        if not path.startswith("/"):
            path = "/" + path
        return path

    def _build_urls(self) -> List[str]:
        if not self.api_base:
            return []
        urls = []
        primary = self.api_base + self._normalize_path(self.api_path)
        urls.append(primary)
        fallback = self.api_base + self._normalize_path(self.fallback_path)
        if fallback != primary:
            urls.append(fallback)
        return urls

    def _build_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            value = self.api_key
            if self.auth_header.lower() == "authorization" and not value.lower().startswith("bearer "):
                value = "Bearer " + value
            headers[self.auth_header] = value
        return headers

    def _maybe_healthcheck(self):
        if not self.enable_healthcheck or not self.api_base:
            return
        now = time.time()
        if self._last_health_ready is not None and now - self._last_health_ts < self.healthcheck_interval:
            return
        health_url = self.api_base + self._normalize_path(self.health_path)
        try:
            resp = self.session.get(
                health_url,
                headers=self._build_headers(),
                timeout=(self.connect_timeout, min(10.0, self.request_timeout)),
                verify=self.verify_ssl,
            )
            if resp.status_code == 404:
                self._last_health_ready = True
                self._last_health_ts = now
                return
            payload = {}
            try:
                payload = resp.json() if resp.text else {}
            except ValueError:
                payload = {}
            ready = bool(payload.get("ready", resp.status_code < 500))
            self._last_health_ready = ready
            self._last_health_ts = now
            if not ready:
                logger.warning("[Qwen3-ASR] Health check says service is not ready: %s", payload)
        except Exception as e:
            self._last_health_ready = False
            self._last_health_ts = now
            logger.warning("[Qwen3-ASR] Health check failed, will still try transcribe: %s", e)

    def _guess_data_url_prefix(self, voice_file: str) -> str:
        mime_type, _ = mimetypes.guess_type(voice_file)
        if not mime_type:
            mime_type = "application/octet-stream"
        return "data:{},base64,".format(mime_type)

    def _build_audio_payload(self, voice_file: str) -> Optional[str]:
        if self.audio_transport == "path":
            return os.path.abspath(voice_file)
        try:
            with open(voice_file, "rb") as f:
                raw = f.read()
            b64 = base64.b64encode(raw).decode("ascii")
            if self.audio_transport == "data_url":
                return self._guess_data_url_prefix(voice_file) + b64
            return b64
        except Exception as e:
            logger.error("[Qwen3-ASR] Read audio file failed: %s", e)
            return None

    def _build_request_body(self, audio_payload: str) -> Dict[str, Any]:
        body = {
            "audio": audio_payload,
            "context": self.context_text or "",
            "return_time_stamps": self.return_time_stamps,
        }
        if self.language:
            body["language"] = self.language
        return body

    def _is_retryable_status(self, code: int) -> bool:
        return code >= 500 or code in (408, 425, 429)

    def _extract_text(self, payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        if not isinstance(payload, dict):
            return None, "invalid_response_type"

        if "result" in payload and isinstance(payload.get("result"), dict):
            payload = payload["result"]

        results = payload.get("results")
        if isinstance(results, list):
            texts = []
            for item in results:
                if isinstance(item, dict):
                    text = str(item.get("text", "")).strip()
                    if text:
                        texts.append(text)
                elif isinstance(item, str):
                    text = item.strip()
                    if text:
                        texts.append(text)
            if texts:
                return "\n".join(texts), None

        if isinstance(results, dict):
            text = str(results.get("text", "")).strip()
            if text:
                return text, None

        for key in ("text", "transcript", "message"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip(), None

        err = payload.get("error")
        if isinstance(err, str) and err.strip():
            return None, err.strip()
        return None, "empty_transcription"

    def _post_with_retry(self, url: str, body: Dict[str, Any], headers: Dict[str, str]) -> Tuple[Optional[str], str]:
        last_error = "unknown_error"
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.post(
                    url,
                    json=body,
                    headers=headers,
                    timeout=(self.connect_timeout, self.request_timeout),
                    verify=self.verify_ssl,
                )
            except requests.RequestException as e:
                last_error = "request_error: {}".format(e)
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff * (2 ** attempt))
                    continue
                return None, last_error

            if resp.status_code >= 400:
                err_msg = "http_{}".format(resp.status_code)
                try:
                    err_payload = resp.json()
                    if isinstance(err_payload, dict) and err_payload.get("error"):
                        err_msg = "{}: {}".format(err_msg, err_payload.get("error"))
                except ValueError:
                    text = (resp.text or "").strip()
                    if text:
                        err_msg = "{}: {}".format(err_msg, text[:200])
                last_error = err_msg
                if self._is_retryable_status(resp.status_code) and attempt < self.max_retries:
                    time.sleep(self.retry_backoff * (2 ** attempt))
                    continue
                return None, last_error

            try:
                payload = resp.json()
            except ValueError:
                last_error = "invalid_json_response"
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff * (2 ** attempt))
                    continue
                return None, last_error

            text, parse_error = self._extract_text(payload)
            if text:
                return text, ""
            last_error = parse_error or "empty_transcription"
            if attempt < self.max_retries:
                time.sleep(self.retry_backoff * (2 ** attempt))
                continue
            return None, last_error

        return None, last_error

    def voiceToText(self, voice_file):
        logger.debug("[Qwen3-ASR] voice file name=%s", voice_file)
        if not voice_file or not os.path.exists(voice_file):
            return Reply(ReplyType.ERROR, "Voice file not found.")

        urls = self._build_urls()
        if not urls:
            return Reply(ReplyType.ERROR, "Qwen3-ASR API base is not configured.")

        self._maybe_healthcheck()

        audio_payload = self._build_audio_payload(voice_file)
        if not audio_payload:
            return Reply(ReplyType.ERROR, "Voice file read failed.")

        body = self._build_request_body(audio_payload)
        headers = self._build_headers()
        errors = []

        for url in urls:
            text, err = self._post_with_retry(url, body, headers)
            if text:
                logger.info("[Qwen3-ASR] VoiceToText success, endpoint=%s, text=%s", url, text)
                return Reply(ReplyType.TEXT, text)
            errors.append("{} -> {}".format(url, err))
            logger.warning("[Qwen3-ASR] VoiceToText failed at endpoint %s: %s", url, err)

        logger.error("[Qwen3-ASR] VoiceToText failed, all endpoints exhausted: %s", "; ".join(errors))
        return Reply(ReplyType.ERROR, "Voice recognition failed, please retry later.")

    def textToVoice(self, text):
        logger.warning("[Qwen3-ASR] textToVoice is not supported")
        return Reply(ReplyType.ERROR, "Qwen3-ASR does not support text-to-speech.")
