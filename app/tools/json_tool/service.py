"""JSON 工具核心逻辑。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JsonError:
    """JSON 解析错误信息。"""

    message: str
    line: int
    column: int
    pos: int


def parse_json(text: str) -> tuple[Any | None, JsonError | None]:
    """解析 JSON，失败时返回结构化错误。"""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, JsonError(
            message=exc.msg,
            line=exc.lineno,
            column=exc.colno,
            pos=exc.pos,
        )
    return data, None


def format_json(text: str) -> tuple[str, JsonError | None]:
    """JSON 美化。"""
    data, error = parse_json(text)
    if error is not None:
        return "", error
    return json.dumps(data, ensure_ascii=False, indent=2), None


def compact_json(text: str) -> tuple[str, JsonError | None]:
    """JSON 压缩为单行。"""
    data, error = parse_json(text)
    if error is not None:
        return "", error
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")), None


def escape_json_text(text: str) -> str:
    """将任意文本转为 JSON 字符串内容（带转义）。"""
    escaped = json.dumps(text, ensure_ascii=False)
    return escaped[1:-1]


def unescape_json_text(text: str) -> tuple[str, JsonError | None]:
    """将 JSON 转义文本还原。

    输入 text 不含外层双引号，函数内部补齐再解析。
    """
    wrapped = f'"{text}"'
    data, error = parse_json(wrapped)
    if error is not None:
        return "", error
    if not isinstance(data, str):
        return "", JsonError(
            message="Unescaped result is not string",
            line=1,
            column=1,
            pos=0,
        )
    return data, None
