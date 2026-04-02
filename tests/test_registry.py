"""ToolRegistry 单元测试。"""

from __future__ import annotations

import pytest

from app.main import build_registry
from app.tools.registry import ToolRegistry
from app.tools.sample_tool import SampleTool


def test_register_and_get_tool() -> None:
    # Given: 一个空注册表和一个示例工具
    registry = ToolRegistry()
    tool = SampleTool()

    # When: 注册后按 id 获取
    registry.register(tool)
    loaded = registry.get("sample_tool")

    # Then: 获取到同一个对象
    assert loaded is tool


def test_register_duplicate_should_raise() -> None:
    # Given: 注册表中已存在同 tool_id 的工具
    registry = ToolRegistry()
    registry.register(SampleTool())

    # When / Then: 再次注册会抛出异常
    with pytest.raises(ValueError):
        registry.register(SampleTool())


def test_build_registry_contains_sample_tool() -> None:
    # Given: 默认注册表
    registry = build_registry()

    # When: 获取所有工具
    tools = list(registry.all())

    # Then: 默认包含一个示例工具
    assert len(tools) == 1
    assert tools[0].metadata.tool_id == "sample_tool"
