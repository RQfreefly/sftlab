"""LLM API 测试工具插件。"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from app.storage import ConfigRepository
from app.tools.base import ToolMetadata, ToolPlugin
from app.tools.llm_api_tester.client import LlmApiClient
from app.tools.llm_api_tester.widget import LlmApiTesterWidget


class LlmApiTesterTool(ToolPlugin):
    """OpenAI 标准接口测试工具。"""

    def __init__(self, config_repo: ConfigRepository, client: LlmApiClient | None = None) -> None:
        self._config_repo = config_repo
        self._client = client or LlmApiClient()

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="llm_api_tester",
            name="LLM API",
            description="OpenAI 标准接口调试与多 Tab 对比",
        )

    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        return LlmApiTesterWidget(
            config_repo=self._config_repo,
            client=self._client,
            parent=parent,
        )
