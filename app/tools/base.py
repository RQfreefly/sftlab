"""工具插件基础接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class ToolMetadata:
    """工具元数据。"""

    tool_id: str
    name: str
    description: str


class ToolPlugin(ABC):
    """工具插件抽象基类。"""

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """返回工具元数据。"""

    @abstractmethod
    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        """创建工具 UI 组件。"""
