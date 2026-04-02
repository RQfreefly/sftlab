"""LLM API 客户端测试。"""

from __future__ import annotations

from typing import Any

import pytest

from app.tools.llm_api_tester.client import LlmApiClient, LlmApiError


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        payload: dict[str, Any] | None = None,
        text: str = "",
        headers: dict[str, str] | None = None,
        lines: list[str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = headers or {"Content-Type": "application/json"}
        self._lines = lines or []

    def json(self) -> dict[str, Any]:
        if self._payload is None:
            raise ValueError("invalid json")
        return self._payload

    def iter_lines(self, decode_unicode: bool = True):  # noqa: ANN001, ANN201
        return iter(self._lines)


def test_client_parses_completion_response(monkeypatch) -> None:
    # Given: 一个成功响应
    payload = {
        "choices": [
            {
                "message": {
                    "content": "你好",
                    "reasoning_content": "这是思考过程",
                }
            }
        ]
    }

    def fake_post(*args, **kwargs):  # noqa: ANN002,ANN003
        return FakeResponse(200, payload=payload)

    monkeypatch.setattr("app.tools.llm_api_tester.client.requests.post", fake_post)

    # When: 发起请求
    client = LlmApiClient(max_retries=0)
    result = client.create_chat_completion(
        base_url="https://api.openai.com",
        api_key="sk-test",
        payload={"model": "deepseek-v3.2", "messages": []},
    )

    # Then: 返回解析后的内容
    assert result.content == "你好"
    assert result.reasoning == "这是思考过程"


def test_client_raises_on_http_error(monkeypatch) -> None:
    # Given: 一个 401 响应
    def fake_post(*args, **kwargs):  # noqa: ANN002,ANN003
        return FakeResponse(401, payload={"error": {"message": "unauthorized"}}, text="unauthorized")

    monkeypatch.setattr("app.tools.llm_api_tester.client.requests.post", fake_post)

    # When / Then: 请求应抛出业务异常
    client = LlmApiClient(max_retries=0)
    with pytest.raises(LlmApiError):
        client.create_chat_completion(
            base_url="https://api.openai.com",
            api_key="sk-test",
            payload={"model": "deepseek-v3.2", "messages": []},
        )


def test_client_parses_stream_response(monkeypatch) -> None:
    # Given: 一个 event-stream 响应
    lines = [
        'data: {"choices":[{"delta":{"content":"你"}}]}',
        'data: {"choices":[{"delta":{"content":"好","reasoning_content":"思"}}]}',
        'data: {"choices":[{"delta":{"reasoning_content":"考"}}]}',
        "data: [DONE]",
    ]

    def fake_post(*args, **kwargs):  # noqa: ANN002,ANN003
        assert kwargs.get("stream") is True
        return FakeResponse(
            200,
            headers={"Content-Type": "text/event-stream"},
            lines=lines,
            text="\n".join(lines),
        )

    monkeypatch.setattr("app.tools.llm_api_tester.client.requests.post", fake_post)

    # When: 发起 stream 请求
    deltas: list[tuple[str, str]] = []
    client = LlmApiClient(max_retries=0)
    result = client.create_chat_completion(
        base_url="https://api.openai.com",
        api_key="sk-test",
        payload={"model": "deepseek-v3.2", "messages": [], "stream": True},
        on_delta=lambda content, reasoning: deltas.append((content, reasoning)),
    )

    # Then: 正确拼接增量内容
    assert result.content == "你好"
    assert result.reasoning == "思考"
    assert deltas == [("你", ""), ("好", "思"), ("", "考")]
