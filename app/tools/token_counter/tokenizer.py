"""多模型 Token 统计（基于成熟 tokenizer 库）。"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class TokenStats:
    """Token 统计结果。"""

    model_name: str
    token_count: int
    char_count: int


SUPPORTED_MODELS: tuple[str, ...] = ("gpt", "qwen", "llama")

_HF_TOKENIZER_MODELS: dict[str, str] = {
    "qwen": "Qwen/Qwen2.5-7B-Instruct",
    "llama": "meta-llama/Llama-3.1-8B-Instruct",
}


def list_supported_models() -> tuple[str, ...]:
    """返回支持的模型列表。"""
    return SUPPORTED_MODELS


def count_tokens(model_name: str, text: str) -> TokenStats:
    """按模型名称返回 token 与字符统计。"""
    normalized = model_name.strip().lower()
    if normalized not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_name}")

    if normalized == "gpt":
        token_count = _count_with_tiktoken(text)
    else:
        model_id = _HF_TOKENIZER_MODELS[normalized]
        token_count = _count_with_transformers(model_id, text)

    return TokenStats(
        model_name=normalized,
        token_count=token_count,
        char_count=len(text),
    )


def _count_with_tiktoken(text: str) -> int:
    encoding = _get_tiktoken_encoding()
    token_ids = encoding.encode(text, disallowed_special=())
    return len(token_ids)


def _count_with_transformers(model_id: str, text: str) -> int:
    tokenizer = _get_transformers_tokenizer(model_id)
    token_ids = tokenizer.encode(text, add_special_tokens=False)
    return len(token_ids)


@lru_cache(maxsize=1)
def _get_tiktoken_encoding():
    try:
        import tiktoken
    except ImportError as exc:  # pragma: no cover - 依赖缺失属于环境问题
        raise RuntimeError("未安装 tiktoken，请先安装依赖") from exc

    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("加载 GPT tokenizer 失败，请检查网络或本地缓存") from exc


@lru_cache(maxsize=4)
def _get_transformers_tokenizer(model_id: str):
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:  # pragma: no cover - 依赖缺失属于环境问题
        raise RuntimeError("未安装 transformers，请先安装依赖") from exc

    try:
        return AutoTokenizer.from_pretrained(model_id, use_fast=True)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"加载 tokenizer 失败: {model_id}。请检查网络、Hugging Face 权限或本地缓存"
        ) from exc
