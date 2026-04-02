"""SFT 参数管理工具插件。"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from app.storage import SftParamTemplateRepository
from app.tools.base import ToolMetadata, ToolPlugin
from app.tools.sft_params.widget import SftParamManagerWidget


class SftParamTool(ToolPlugin):
    """SFT 参数模板管理工具。"""

    def __init__(self, repository: SftParamTemplateRepository) -> None:
        self._repository = repository

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="sft_params",
            name="参数管理",
            description="管理 SFT 训练参数模板",
        )

    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        return SftParamManagerWidget(repository=self._repository, parent=parent)
