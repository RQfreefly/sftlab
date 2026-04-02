"""Prompt 仓储测试。"""

from __future__ import annotations

import pytest

from app.storage import Database, PromptRepository


PROMPT_V1 = "你是一个严谨的代码审查助手。"
PROMPT_V2 = "你是一个严谨的代码审查助手，请给出可执行修改建议。"


def test_create_directories_with_parent(tmp_path) -> None:
    # Given: 初始化仓储
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = PromptRepository(database)

    # When: 创建父子目录
    parent = repo.create_directory("研发")
    child = repo.create_directory("评审", parent_id=parent.id)
    directories = repo.list_directories()

    # Then: 子目录记录了正确父级
    assert len(directories) == 2
    assert child.parent_id == parent.id


def test_create_directory_should_reject_duplicate_name_under_same_parent(tmp_path) -> None:
    # Given: 同一父目录下已有同名目录
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = PromptRepository(database)
    parent = repo.create_directory("研发")
    repo.create_directory("评审", parent_id=parent.id)

    # When / Then: 再创建同名目录应失败
    with pytest.raises(ValueError):
        repo.create_directory("评审", parent_id=parent.id)


def test_create_directory_should_reject_duplicate_name_under_root(tmp_path) -> None:
    # Given: 根目录下已有同名目录
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = PromptRepository(database)
    repo.create_directory("研发")

    # When / Then: 再创建同名根目录应失败
    with pytest.raises(ValueError):
        repo.create_directory("研发")


def test_rename_directory_should_update_name(tmp_path) -> None:
    # Given: 已有目录
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = PromptRepository(database)
    directory = repo.create_directory("研发")

    # When: 执行目录重命名
    renamed = repo.rename_directory(directory.id, "研发-新")

    # Then: 名称被更新
    assert renamed.name == "研发-新"


def test_rename_directory_should_reject_duplicate_name(tmp_path) -> None:
    # Given: 同级已有重名目录
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = PromptRepository(database)
    repo.create_directory("研发")
    directory2 = repo.create_directory("测试")

    # When / Then: 重命名为同级已有名称应失败
    with pytest.raises(ValueError):
        repo.rename_directory(directory2.id, "研发")


def test_create_and_update_prompt_should_append_versions(tmp_path) -> None:
    # Given: 已有目录
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = PromptRepository(database)
    directory = repo.create_directory("研发")

    # When: 创建 Prompt 并更新
    created = repo.create_prompt(directory.id, "代码评审", PROMPT_V1)
    updated = repo.update_prompt(created.id, directory.id, "代码评审", PROMPT_V2)
    versions = repo.list_versions(created.id)

    # Then: 版本递增，最新内容正确
    assert updated.content == PROMPT_V2
    assert len(versions) == 2
    assert versions[0].version_no == 2
    assert versions[1].version_no == 1


def test_move_prompt_should_change_directory_without_new_version(tmp_path) -> None:
    # Given: Prompt 在目录 A 中
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = PromptRepository(database)
    directory_a = repo.create_directory("目录A")
    directory_b = repo.create_directory("目录B")
    prompt = repo.create_prompt(directory_a.id, "代码评审", PROMPT_V1)
    before_versions = repo.list_versions(prompt.id)

    # When: 移动到目录 B
    moved = repo.move_prompt(prompt.id, directory_b.id)
    after_versions = repo.list_versions(prompt.id)

    # Then: 目录变化，但版本数保持不变
    assert moved.directory_id == directory_b.id
    assert len(before_versions) == len(after_versions) == 1
    assert after_versions[0].version_no == 1


def test_delete_directory_should_fail_when_not_empty(tmp_path) -> None:
    # Given: 目录下存在 Prompt
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = PromptRepository(database)
    directory = repo.create_directory("研发")
    repo.create_prompt(directory.id, "代码评审", PROMPT_V1)

    # When / Then: 删除目录应失败
    with pytest.raises(ValueError):
        repo.delete_directory(directory.id)


def test_delete_prompt_should_remove_versions(tmp_path) -> None:
    # Given: Prompt 有多个版本
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = PromptRepository(database)
    directory = repo.create_directory("研发")
    prompt = repo.create_prompt(directory.id, "代码评审", PROMPT_V1)
    repo.update_prompt(prompt.id, directory.id, "代码评审", PROMPT_V2)

    # When: 删除 Prompt
    repo.delete_prompt(prompt.id)

    # Then: Prompt 与版本都被清理
    assert repo.get_prompt(prompt.id) is None
    assert repo.list_versions(prompt.id) == []
