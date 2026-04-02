"""JSON 工具服务层测试。"""

from __future__ import annotations

from app.tools.json_tool.service import (
    compact_json,
    escape_json_text,
    format_json,
    parse_json,
    unescape_json_text,
)


def test_parse_json_should_return_error_for_invalid_input() -> None:
    # Given: 非法 JSON
    text = '{"name": "alice", }'

    # When: 解析
    data, error = parse_json(text)

    # Then: 返回结构化错误信息
    assert data is None
    assert error is not None
    assert error.line >= 1
    assert error.column >= 1


def test_format_and_compact_json() -> None:
    # Given: 合法 JSON
    text = '{"a":1,"b":[1,2]}'

    # When: 美化与压缩
    formatted, format_error = format_json(text)
    compacted, compact_error = compact_json(formatted)

    # Then: 两种输出都成功
    assert format_error is None
    assert compact_error is None
    assert "\n" in formatted
    assert compacted == '{"a":1,"b":[1,2]}'


def test_escape_and_unescape_json_text() -> None:
    # Given: 原始文本
    raw = 'line1\nline2 "quoted"'

    # When: 转义并反转义
    escaped = escape_json_text(raw)
    unescaped, error = unescape_json_text(escaped)

    # Then: 内容可逆
    assert error is None
    assert unescaped == raw
