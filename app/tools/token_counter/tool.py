"""Token 统计工具插件。"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from app.tools.base import ToolMetadata, ToolPlugin
from app.tools.token_counter.widget import TokenCounterWidget


class TokenCounterTool(ToolPlugin):
    """Token 统计工具。"""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="token_counter",
            name="Token",
            description="统计文本 Token 数与字符数",
        )

    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        return TokenCounterWidget(parent=parent)
