"""Diff 工具插件。"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from app.tools.base import ToolMetadata, ToolPlugin
from app.tools.diff_tool.widget import DiffToolWidget


class DiffTool(ToolPlugin):
    """文本差异工具。"""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="diff_tool",
            name="Diff",
            description="行级与字符级文本差异比较",
        )

    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        return DiffToolWidget(parent=parent)
