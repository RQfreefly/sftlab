"""Token 统计逻辑测试。"""

from __future__ import annotations

import pytest

from app.tools.token_counter import tokenizer


def test_list_supported_models() -> None:
    # Given / When: 读取支持模型
    models = tokenizer.list_supported_models()

    # Then: 包含预期模型
    assert models == ("gpt", "qwen", "llama")


def test_count_tokens_for_gpt_uses_tiktoken(monkeypatch) -> None:
    # Given: 一个 fake 的 tiktoken encoding
    class FakeEncoding:
        def encode(self, _text, disallowed_special=()):  # noqa: ANN001
            assert disallowed_special == ()
            return [1, 2, 3, 4]

    monkeypatch.setattr(tokenizer, "_get_tiktoken_encoding", lambda: FakeEncoding())

    # When: 统计 GPT token
    stats = tokenizer.count_tokens("gpt", "hello")

    # Then: token 数来自 tiktoken 编码长度
    assert stats.model_name == "gpt"
    assert stats.token_count == 4
    assert stats.char_count == 5


def test_count_tokens_for_transformers_models(monkeypatch) -> None:
    # Given: 一个 fake 的 transformers tokenizer 加载器
    calls: list[str] = []

    class FakeTokenizer:
        def __init__(self, model_id: str) -> None:
            self.model_id = model_id

        def encode(self, _text, add_special_tokens=False):  # noqa: ANN001
            assert add_special_tokens is False
            if "Qwen" in self.model_id:
                return [1, 2, 3]
            return [1, 2, 3, 4, 5]

    def fake_get(model_id: str):
        calls.append(model_id)
        return FakeTokenizer(model_id)

    monkeypatch.setattr(tokenizer, "_get_transformers_tokenizer", fake_get)

    # When: 统计 Qwen 和 LLaMA
    qwen_stats = tokenizer.count_tokens("qwen", "hello")
    llama_stats = tokenizer.count_tokens("llama", "hello")

    # Then: token 统计来自对应 tokenizer
    assert qwen_stats.token_count == 3
    assert llama_stats.token_count == 5
    assert any("Qwen" in model_id for model_id in calls)
    assert any("Llama" in model_id for model_id in calls)


def test_count_tokens_should_reject_unsupported_model() -> None:
    # Given / When / Then: 非法模型名称会抛错
    with pytest.raises(ValueError):
        tokenizer.count_tokens("unknown", "abc")
