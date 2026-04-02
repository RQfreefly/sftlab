"""Diff 核心逻辑。"""

from __future__ import annotations

import difflib
import html
import json
from dataclasses import dataclass


DIFF_MODES: tuple[str, ...] = ("line", "char")
DIFF_TYPES: tuple[str, ...] = ("text", "json", "prompt")


@dataclass(frozen=True)
class DiffChunk:
    """字符级差异块。"""

    op: str
    text: str


@dataclass(frozen=True)
class DiffResult:
    """Diff 输出结果。"""

    success: bool
    mode: str
    diff_type: str
    summary: str
    plain_text: str
    html_text: str


def compute_diff(left_text: str, right_text: str, mode: str, diff_type: str) -> DiffResult:
    """统一 diff 入口。"""
    normalized_mode = mode.strip().lower()
    normalized_type = diff_type.strip().lower()

    if normalized_mode not in DIFF_MODES:
        raise ValueError(f"Unsupported diff mode: {mode}")
    if normalized_type not in DIFF_TYPES:
        raise ValueError(f"Unsupported diff type: {diff_type}")

    left_normalized, right_normalized, error = _normalize_by_type(
        left_text=left_text,
        right_text=right_text,
        diff_type=normalized_type,
    )
    if error is not None:
        return DiffResult(
            success=False,
            mode=normalized_mode,
            diff_type=normalized_type,
            summary=error,
            plain_text="",
            html_text=_to_pre_html(error),
        )

    if normalized_mode == "line":
        return _compute_line_diff(
            left_text=left_normalized,
            right_text=right_normalized,
            diff_type=normalized_type,
        )
    return _compute_char_diff(
        left_text=left_normalized,
        right_text=right_normalized,
        diff_type=normalized_type,
    )


def _compute_line_diff(left_text: str, right_text: str, diff_type: str) -> DiffResult:
    lines = list(
        difflib.unified_diff(
            left_text.splitlines(),
            right_text.splitlines(),
            fromfile="left",
            tofile="right",
            lineterm="",
        )
    )

    if not lines:
        plain = "无差异"
        summary = "行级差异：0 行变更"
    else:
        plain = "\n".join(lines)
        changed = sum(1 for line in lines if line.startswith("+") or line.startswith("-"))
        summary = f"行级差异：{changed} 行变更"

    return DiffResult(
        success=True,
        mode="line",
        diff_type=diff_type,
        summary=summary,
        plain_text=plain,
        html_text=_to_pre_html(plain),
    )


def _compute_char_diff(left_text: str, right_text: str, diff_type: str) -> DiffResult:
    matcher = difflib.SequenceMatcher(a=left_text, b=right_text)
    chunks: list[DiffChunk] = []

    insert_count = 0
    delete_count = 0

    for tag, a_start, a_end, b_start, b_end in matcher.get_opcodes():
        if tag == "equal":
            chunks.append(DiffChunk(op="equal", text=left_text[a_start:a_end]))
            continue

        if tag == "delete":
            text = left_text[a_start:a_end]
            delete_count += len(text)
            chunks.append(DiffChunk(op="delete", text=text))
            continue

        if tag == "insert":
            text = right_text[b_start:b_end]
            insert_count += len(text)
            chunks.append(DiffChunk(op="insert", text=text))
            continue

        deleted = left_text[a_start:a_end]
        inserted = right_text[b_start:b_end]
        delete_count += len(deleted)
        insert_count += len(inserted)
        if deleted:
            chunks.append(DiffChunk(op="delete", text=deleted))
        if inserted:
            chunks.append(DiffChunk(op="insert", text=inserted))

    plain = _char_chunks_to_plain(chunks)
    html_text = _char_chunks_to_html(chunks)
    if insert_count == 0 and delete_count == 0:
        summary = "字符级差异：0 字符变更"
    else:
        summary = f"字符级差异：+{insert_count} / -{delete_count}"

    return DiffResult(
        success=True,
        mode="char",
        diff_type=diff_type,
        summary=summary,
        plain_text=plain,
        html_text=html_text,
    )


def _char_chunks_to_plain(chunks: list[DiffChunk]) -> str:
    parts: list[str] = []
    for chunk in chunks:
        if chunk.op == "equal":
            parts.append(chunk.text)
        elif chunk.op == "insert":
            parts.append("{+" + chunk.text + "+}")
        elif chunk.op == "delete":
            parts.append("[-" + chunk.text + "-]")
    return "".join(parts)


def _char_chunks_to_html(chunks: list[DiffChunk]) -> str:
    html_parts = ["<div style='font-family: Menlo, Consolas, monospace; white-space: pre-wrap;'>"]
    for chunk in chunks:
        escaped = html.escape(chunk.text)
        if chunk.op == "equal":
            html_parts.append(escaped)
        elif chunk.op == "insert":
            html_parts.append(f"<span style='background:#daf5d7;color:#145214;'>{escaped}</span>")
        elif chunk.op == "delete":
            html_parts.append(f"<span style='background:#ffd9d9;color:#8a1f1f;'>{escaped}</span>")
    html_parts.append("</div>")
    return "".join(html_parts)


def _to_pre_html(text: str) -> str:
    escaped = html.escape(text)
    return (
        "<pre style='font-family: Menlo, Consolas, monospace; white-space: pre-wrap; "
        "margin: 0;'>"
        + escaped
        + "</pre>"
    )


def _normalize_by_type(left_text: str, right_text: str, diff_type: str) -> tuple[str, str, str | None]:
    if diff_type == "text":
        return left_text, right_text, None

    if diff_type == "prompt":
        return _normalize_prompt_text(left_text), _normalize_prompt_text(right_text), None

    return _normalize_json_text(left_text, right_text)


def _normalize_prompt_text(text: str) -> str:
    raw_lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [line.rstrip() for line in raw_lines]

    collapsed: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue
        collapsed.append(line)
        previous_blank = is_blank

    return "\n".join(collapsed).strip()


def _normalize_json_text(left_text: str, right_text: str) -> tuple[str, str, str | None]:
    try:
        left_data = json.loads(left_text)
    except json.JSONDecodeError as exc:
        return "", "", f"左侧 JSON 非法：{exc.msg}（{exc.lineno}:{exc.colno}）"

    try:
        right_data = json.loads(right_text)
    except json.JSONDecodeError as exc:
        return "", "", f"右侧 JSON 非法：{exc.msg}（{exc.lineno}:{exc.colno}）"

    left_normalized = json.dumps(left_data, ensure_ascii=False, indent=2, sort_keys=True)
    right_normalized = json.dumps(right_data, ensure_ascii=False, indent=2, sort_keys=True)
    return left_normalized, right_normalized, None
