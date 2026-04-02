"""LLM API 客户端（OpenAI 标准接口）。"""

from __future__ import annotations

from collections.abc import Callable
import json
import time
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class LlmApiResult:
    """接口返回的简化结构。"""

    content: str
    reasoning: str
    raw_json: str


class LlmApiError(RuntimeError):
    """LLM API 请求异常。"""


class LlmApiClient:
    """OpenAI Chat Completions 客户端。"""

    def __init__(self, timeout_seconds: int = 90, max_retries: int = 1) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

    def create_chat_completion(
        self,
        base_url: str,
        api_key: str,
        payload: dict[str, Any],
        on_delta: Callable[[str, str], None] | None = None,
    ) -> LlmApiResult:
        """发起 chat/completions 请求。"""
        if not base_url.strip():
            raise LlmApiError("Base URL 不能为空")
        if not api_key.strip():
            raise LlmApiError("API Key 不能为空")

        url = base_url.rstrip("/") + "/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key.strip()}",
        }

        last_error: Exception | None = None
        is_stream = bool(payload.get("stream"))
        for attempt in range(self._max_retries + 1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self._timeout_seconds,
                    stream=is_stream,
                )
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self._max_retries:
                    time.sleep(0.4)
                    continue
                raise LlmApiError(f"网络请求失败：{exc}") from exc

            if response.status_code in (429, 500, 502, 503, 504) and attempt < self._max_retries:
                time.sleep(0.4)
                continue

            if response.status_code >= 400:
                text = response.text.strip()[:600]
                raise LlmApiError(f"HTTP {response.status_code}: {text}")

            content_type = response.headers.get("Content-Type", "")
            if is_stream:
                return self._parse_stream_response(response, content_type, on_delta)

            if "text/event-stream" in content_type.lower():
                raise LlmApiError("服务返回流式 event-stream（stream 模式），当前仅支持非流式 JSON 响应")

            try:
                data = response.json()
            except ValueError as exc:
                body_preview = response.text.strip()[:300]
                raise LlmApiError(
                    f"响应不是合法 JSON，Content-Type={content_type or 'unknown'}，响应片段：{body_preview}"
                ) from exc

            return self._parse_response(data)

        raise LlmApiError(f"请求失败：{last_error}")

    def _parse_stream_response(
        self,
        response: requests.Response,
        content_type: str,
        on_delta: Callable[[str, str], None] | None,
    ) -> LlmApiResult:
        content_type_lower = content_type.lower()
        if "text/event-stream" not in content_type_lower:
            try:
                return self._parse_response(response.json())
            except ValueError as exc:
                body_preview = response.text.strip()[:300]
                raise LlmApiError(
                    f"stream=true 但响应不是 event-stream/JSON，Content-Type={content_type or 'unknown'}，"
                    f"响应片段：{body_preview}"
                ) from exc

        content_parts: list[str] = []
        reasoning_parts: list[str] = []
        chunks: list[dict[str, Any]] = []

        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            line = raw_line.strip()
            if not line or line.startswith(":"):
                continue
            if not line.lower().startswith("data:"):
                continue

            body = line[5:].strip()
            if body == "[DONE]":
                break

            try:
                chunk = json.loads(body)
            except ValueError as exc:
                raise LlmApiError(f"流式分片不是合法 JSON：{body[:200]}") from exc

            chunks.append(chunk)
            content_delta, reasoning_delta = self._extract_stream_delta(chunk)
            if content_delta:
                content_parts.append(content_delta)
            if reasoning_delta:
                reasoning_parts.append(reasoning_delta)
            if on_delta is not None and (content_delta or reasoning_delta):
                on_delta(content_delta, reasoning_delta)

        if not chunks:
            raise LlmApiError("流式响应没有有效数据分片")

        return LlmApiResult(
            content="".join(content_parts),
            reasoning="".join(reasoning_parts),
            raw_json=json.dumps({"stream": True, "chunks": chunks}, ensure_ascii=False),
        )

    def _extract_stream_delta(self, chunk: dict[str, Any]) -> tuple[str, str]:
        choices = chunk.get("choices")
        if not isinstance(choices, list) or not choices:
            return "", ""

        choice = choices[0]
        if not isinstance(choice, dict):
            return "", ""

        source = choice.get("delta")
        if not isinstance(source, dict):
            source = choice.get("message")
        if not isinstance(source, dict):
            return "", ""

        content = _normalize_message_content(source.get("content"))
        reasoning_raw = (
            source.get("reasoning_content")
            or source.get("reasoning")
            or source.get("think")
            or ""
        )
        reasoning = _normalize_message_content(reasoning_raw)
        return content, reasoning

    def _parse_response(self, data: dict[str, Any]) -> LlmApiResult:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LlmApiError("响应中缺少 choices")

        choice = choices[0]
        if not isinstance(choice, dict):
            raise LlmApiError("响应 choices[0] 格式异常")

        message = choice.get("message")
        if not isinstance(message, dict):
            raise LlmApiError("响应 message 格式异常")

        content = _normalize_message_content(message.get("content"))

        reasoning_raw = (
            message.get("reasoning_content")
            or message.get("reasoning")
            or message.get("think")
            or ""
        )
        reasoning = _normalize_message_content(reasoning_raw)

        return LlmApiResult(
            content=content,
            reasoning=reasoning,
            raw_json=json.dumps(data, ensure_ascii=False),
        )


def _normalize_message_content(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    # OpenAI 部分模型可能返回 list[dict{text:...}]
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)

    return str(value)
