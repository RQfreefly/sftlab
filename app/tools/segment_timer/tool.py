"""分段计时器工具插件。"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from app.storage import TimerRepository
from app.tools.base import ToolMetadata, ToolPlugin
from app.tools.segment_timer.widget import SegmentTimerWidget


class SegmentTimerTool(ToolPlugin):
    """分段计时器工具。"""

    def __init__(self, repository: TimerRepository) -> None:
        self._repository = repository

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="segment_timer",
            name="Timer",
            description="多段计时与历史记录",
        )

    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        return SegmentTimerWidget(repository=self._repository, parent=parent)
