"""Diff 引擎测试。"""

from __future__ import annotations

from app.tools.diff_tool.engine import compute_diff


def test_line_diff_should_include_changed_lines() -> None:
    # Given: 两段有行差异的文本
    left = "a\nb\nc"
    right = "a\nx\nc"

    # When: 行级比较
    result = compute_diff(left, right, mode="line", diff_type="text")

    # Then: 输出包含新增与删除行
    assert result.success is True
    assert "-b" in result.plain_text
    assert "+x" in result.plain_text
    assert "行级差异" in result.summary


def test_char_diff_should_mark_insert_and_delete() -> None:
    # Given: 两段有字符替换的文本
    left = "abc"
    right = "axc"

    # When: 字符级比较
    result = compute_diff(left, right, mode="char", diff_type="text")

    # Then: plain 文本包含删除与新增标记
    assert result.success is True
    assert "[-b-]" in result.plain_text
    assert "{+x+}" in result.plain_text
    assert "字符级差异" in result.summary


def test_json_diff_should_compare_after_normalization() -> None:
    # Given: 字段顺序不同但语义一致的 JSON
    left = '{"b":1,"a":2}'
    right = '{"a":2,"b":1}'

    # When: JSON 行级比较
    result = compute_diff(left, right, mode="line", diff_type="json")

    # Then: 无差异
    assert result.success is True
    assert result.plain_text == "无差异"


def test_json_diff_should_fail_for_invalid_json() -> None:
    # Given: 左侧非法 JSON
    left = '{"a":1,}'
    right = '{"a":1}'

    # When: JSON 比较
    result = compute_diff(left, right, mode="line", diff_type="json")

    # Then: 返回错误信息
    assert result.success is False
    assert "左侧 JSON 非法" in result.summary


def test_prompt_diff_should_ignore_extra_blank_lines_and_trailing_spaces() -> None:
    # Given: 提示词仅在空行和尾随空格上不同
    left = "你是助手。  \n\n\n请回答问题。\n"
    right = "你是助手。\n\n请回答问题。"

    # When: Prompt 类型比较
    result = compute_diff(left, right, mode="line", diff_type="prompt")

    # Then: 归一化后无差异
    assert result.success is True
    assert result.plain_text == "无差异"
