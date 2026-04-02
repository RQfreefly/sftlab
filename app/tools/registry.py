"""工具注册与查询。"""

from __future__ import annotations

from collections.abc import Iterable

from app.tools.base import ToolPlugin


class ToolRegistry:
    """维护工具插件的注册与查询。"""

    def __init__(self) -> None:
        self._tools: dict[str, ToolPlugin] = {}

    def register(self, plugin: ToolPlugin) -> None:
        """注册工具插件，tool_id 不可重复。"""
        tool_id = plugin.metadata.tool_id
        if tool_id in self._tools:
            raise ValueError(f"Tool already registered: {tool_id}")

        self._tools[tool_id] = plugin

    def get(self, tool_id: str) -> ToolPlugin:
        """按 tool_id 获取插件。"""
        if tool_id not in self._tools:
            raise KeyError(f"Tool not found: {tool_id}")
        return self._tools[tool_id]

    def all(self) -> Iterable[ToolPlugin]:
        """按注册顺序返回所有插件。"""
        return self._tools.values()
