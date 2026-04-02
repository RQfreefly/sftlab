"""ToolRegistry 单元测试。"""

from __future__ import annotations

import pytest

from app.main import build_registry
from app.storage import Database, PromptRepository, SftParamTemplateRepository
from app.tools.sample_tool import SampleTool
from app.tools.registry import ToolRegistry


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
    tool_ids = [tool.metadata.tool_id for tool in tools]

    # Then: 默认包含示例、Token、JSON 工具
    assert len(tools) == 3
    assert "sample_tool" in tool_ids
    assert "token_counter" in tool_ids
    assert "json_tool" in tool_ids


def test_build_registry_contains_sft_tool_when_repo_provided(tmp_path) -> None:
    # Given: 可用的参数模板仓储
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = SftParamTemplateRepository(database)

    # When: 使用仓储构建注册表
    registry = build_registry(sft_param_repo=repo)
    tool_ids = [tool.metadata.tool_id for tool in registry.all()]

    # Then: 包含参数管理工具
    assert "sample_tool" in tool_ids
    assert "token_counter" in tool_ids
    assert "json_tool" in tool_ids
    assert "sft_params" in tool_ids


def test_build_registry_contains_prompt_tool_when_repo_provided(tmp_path) -> None:
    # Given: 可用的 Prompt 仓储
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = PromptRepository(database)

    # When: 使用仓储构建注册表
    registry = build_registry(prompt_repo=repo)
    tool_ids = [tool.metadata.tool_id for tool in registry.all()]

    # Then: 包含 Prompt 管理工具
    assert "sample_tool" in tool_ids
    assert "token_counter" in tool_ids
    assert "json_tool" in tool_ids
    assert "prompt_manager" in tool_ids
