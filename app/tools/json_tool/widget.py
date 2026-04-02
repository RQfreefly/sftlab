"""JSON 工具页面。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
)

from app.tools.json_tool.service import (
    compact_json,
    escape_json_text,
    format_json,
    parse_json,
    unescape_json_text,
)


class JsonToolWidget(QWidget):
    """JSON 工具主界面。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._bind_events()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        action_row = QHBoxLayout()
        self.format_button = QPushButton("美化", self)
        self.compact_button = QPushButton("压缩", self)
        self.escape_button = QPushButton("转义", self)
        self.unescape_button = QPushButton("反转义", self)
        self.expand_button = QPushButton("展开树", self)
        self.collapse_button = QPushButton("折叠树", self)

        action_row.addWidget(self.format_button)
        action_row.addWidget(self.compact_button)
        action_row.addWidget(self.escape_button)
        action_row.addWidget(self.unescape_button)
        action_row.addWidget(self.expand_button)
        action_row.addWidget(self.collapse_button)
        root_layout.addLayout(action_row)

        splitter = QSplitter(self)
        root_layout.addWidget(splitter, stretch=1)

        self.text_editor = QPlainTextEdit(splitter)
        self.text_editor.setPlaceholderText("输入 JSON 文本")

        right_panel = QWidget(splitter)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self.tree = QTreeWidget(right_panel)
        self.tree.setHeaderLabels(["Key", "Value"])
        right_layout.addWidget(self.tree, stretch=2)

        right_layout.addWidget(QLabel("节点值全量预览", right_panel))
        self.value_preview = QPlainTextEdit(right_panel)
        self.value_preview.setReadOnly(True)
        self.value_preview.setPlaceholderText("选择树节点后显示完整 Value 内容")
        right_layout.addWidget(self.value_preview, stretch=1)

        splitter.setSizes([760, 520])

        self.status_label = QLabel("就绪", self)
        root_layout.addWidget(self.status_label)

    def _bind_events(self) -> None:
        self.format_button.clicked.connect(self._format_json)
        self.compact_button.clicked.connect(self._compact_json)
        self.escape_button.clicked.connect(self._escape_text)
        self.unescape_button.clicked.connect(self._unescape_text)
        self.expand_button.clicked.connect(self.tree.expandAll)
        self.collapse_button.clicked.connect(self.tree.collapseAll)
        self.text_editor.textChanged.connect(self._refresh_tree_realtime)
        self.tree.currentItemChanged.connect(self._on_tree_item_selected)

    def _format_json(self) -> None:
        text = self.text_editor.toPlainText()
        formatted, error = format_json(text)
        if error is not None:
            self._set_error(f"美化失败：{error.message}（{error.line}:{error.column}）", error.pos)
            return

        self.text_editor.setPlainText(formatted)
        self._clear_error_highlight()
        self._refresh_tree_realtime()
        self.status_label.setText("JSON 美化成功")

    def _compact_json(self) -> None:
        text = self.text_editor.toPlainText()
        compacted, error = compact_json(text)
        if error is not None:
            self._set_error(f"压缩失败：{error.message}（{error.line}:{error.column}）", error.pos)
            return

        self.text_editor.setPlainText(compacted)
        self._clear_error_highlight()
        self._refresh_tree_realtime()
        self.status_label.setText("JSON 压缩成功")

    def _escape_text(self) -> None:
        text = self.text_editor.toPlainText()
        self.text_editor.setPlainText(escape_json_text(text))
        self.status_label.setText("文本已转义")

    def _unescape_text(self) -> None:
        text = self.text_editor.toPlainText()
        unescaped, error = unescape_json_text(text)
        if error is not None:
            self._set_error(f"反转义失败：{error.message}（{error.line}:{error.column}）", error.pos)
            return

        self.text_editor.setPlainText(unescaped)
        self._clear_error_highlight()
        self.status_label.setText("文本已反转义")

    def _refresh_tree_realtime(self) -> None:
        self.tree.clear()
        self.value_preview.clear()
        text = self.text_editor.toPlainText()
        if not text.strip():
            self._clear_error_highlight()
            self.status_label.setText("就绪")
            return

        data, error = parse_json(text)
        if error is not None:
            self._set_error(f"JSON 非法：{error.message}（{error.line}:{error.column}）", error.pos)
            return

        root = QTreeWidgetItem(["$", self._value_type_name(data)])
        root.setData(0, Qt.ItemDataRole.UserRole, self._full_value_text(data))
        self.tree.addTopLevelItem(root)
        self._fill_tree(root, data)
        self.tree.expandToDepth(1)
        self.tree.setCurrentItem(root)
        self._on_tree_item_selected(root, None)
        self._clear_error_highlight()
        self.status_label.setText("JSON 解析成功")

    def _fill_tree(self, parent: QTreeWidgetItem, data: Any) -> None:
        if isinstance(data, Mapping):
            for key, value in data.items():
                item = QTreeWidgetItem([str(key), self._preview_value(value)])
                item.setData(0, Qt.ItemDataRole.UserRole, self._full_value_text(value))
                parent.addChild(item)
                self._fill_tree(item, value)
            return

        if isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
            for index, value in enumerate(data):
                item = QTreeWidgetItem([f"[{index}]", self._preview_value(value)])
                item.setData(0, Qt.ItemDataRole.UserRole, self._full_value_text(value))
                parent.addChild(item)
                self._fill_tree(item, value)

    def _preview_value(self, value: Any) -> str:
        if isinstance(value, Mapping):
            return f"object({len(value)})"
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return f"array({len(value)})"
        return repr(value)

    def _value_type_name(self, value: Any) -> str:
        if isinstance(value, Mapping):
            return "object"
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return "array"
        return type(value).__name__

    def _full_value_text(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, Mapping) or (
            isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
        ):
            import json

            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    def _on_tree_item_selected(
        self,
        current: QTreeWidgetItem | None,
        _previous: QTreeWidgetItem | None,
    ) -> None:
        if current is None:
            self.value_preview.clear()
            return

        full_text = current.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(full_text, str):
            self.value_preview.setPlainText(full_text)
            return
        self.value_preview.clear()

    def _set_error(self, message: str, pos: int) -> None:
        self.status_label.setText(message)
        self._highlight_error_position(pos)

    def _highlight_error_position(self, pos: int) -> None:
        cursor = self.text_editor.textCursor()
        max_pos = len(self.text_editor.toPlainText())
        target = max(0, min(pos, max_pos))
        cursor.setPosition(target)
        self.text_editor.setTextCursor(cursor)

        extra = QTextEdit.ExtraSelection()
        extra.cursor = self.text_editor.textCursor()
        extra.format.setBackground(QColor("#ffcccc"))
        extra.format.setForeground(QColor("#aa0000"))
        self.text_editor.setExtraSelections([extra])

    def _clear_error_highlight(self) -> None:
        self.text_editor.setExtraSelections([])
