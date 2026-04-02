"""CLI 计算器工具插件。"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from app.tools.base import ToolMetadata, ToolPlugin
from app.tools.cli_calculator.widget import CliCalculatorWidget


class CliCalculatorTool(ToolPlugin):
    """命令行计算器工具。"""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="cli_calculator",
            name="Calculator",
            description="支持表达式、变量与函数的命令行计算器",
        )

    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        return CliCalculatorWidget(parent=parent)
