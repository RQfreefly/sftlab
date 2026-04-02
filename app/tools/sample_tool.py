"""M0 示例工具。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from app.tools.base import ToolMetadata, ToolPlugin


class SampleTool(ToolPlugin):
    """用于验证框架可运行的示例工具。"""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="sample_tool",
            name="示例工具",
            description="M0 阶段占位页",
        )

    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        label = QLabel("M0：工具框架已就绪", parent)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label
