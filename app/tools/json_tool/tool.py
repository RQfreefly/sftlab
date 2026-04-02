"""JSON 工具插件。"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from app.tools.base import ToolMetadata, ToolPlugin
from app.tools.json_tool.widget import JsonToolWidget


class JsonTool(ToolPlugin):
    """JSON 解析与格式化工具。"""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="json_tool",
            name="JSON",
            description="JSON 解析、格式化、压缩、转义与树形展示",
        )

    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        return JsonToolWidget(parent=parent)
