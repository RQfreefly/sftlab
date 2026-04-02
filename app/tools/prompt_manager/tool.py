"""Prompt 管理工具插件。"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from app.storage import PromptRepository
from app.tools.base import ToolMetadata, ToolPlugin
from app.tools.prompt_manager.widget import PromptManagerWidget


class PromptManagerTool(ToolPlugin):
    """Prompt 目录化管理工具。"""

    def __init__(self, repository: PromptRepository) -> None:
        self._repository = repository

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="prompt_manager",
            name="Prompt",
            description="目录化管理 Prompt 模板与历史版本",
        )

    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        return PromptManagerWidget(repository=self._repository, parent=parent)
