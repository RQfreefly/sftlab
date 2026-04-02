"""Prompt 管理控件测试。"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.storage import Database, PromptRepository
from app.tools.prompt_manager.widget import PromptManagerWidget


PROMPT_V1 = "你是一个严谨的代码审查助手。"
PROMPT_V2 = "你是一个严谨的代码审查助手，请给出可执行修改建议。"


def test_select_version_should_preview_and_diff(tmp_path) -> None:
    # Given: 一个含两版本的 Prompt
    app = QApplication.instance() or QApplication(sys.argv)
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = PromptRepository(database)
    directory = repo.create_directory("研发")
    prompt = repo.create_prompt(directory.id, "代码评审", PROMPT_V1)
    repo.update_prompt(prompt.id, directory.id, "代码评审", PROMPT_V2)

    widget = PromptManagerWidget(repository=repo)

    # When: 选中目录和 Prompt
    root_item = widget.directory_tree.topLevelItem(0)
    directory_item = root_item.child(0)
    widget.directory_tree.setCurrentItem(directory_item)
    widget.prompt_list.setCurrentRow(0)

    # Then: 当前编辑区默认是最新版本
    assert widget.content_editor.toPlainText() == PROMPT_V2

    # When: 选择 v1 并执行 diff
    widget.version_list.setCurrentRow(1)
    widget.diff_button.click()

    # Then: 预览区显示 v1，Diff 区含有差异标记
    assert widget.version_preview.toPlainText() == PROMPT_V1
    diff_text = widget.diff_preview.toPlainText()
    assert "--- v1" in diff_text
    assert "+++ current" in diff_text

    widget.close()
    app.quit()


def test_rename_directory_and_move_prompt(tmp_path, monkeypatch) -> None:
    # Given: 两个目录和一个 Prompt
    app = QApplication.instance() or QApplication(sys.argv)
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = PromptRepository(database)
    dir_a = repo.create_directory("目录A")
    dir_b = repo.create_directory("目录B")
    prompt = repo.create_prompt(dir_a.id, "代码评审", PROMPT_V1)

    widget = PromptManagerWidget(repository=repo)
    root_item = widget.directory_tree.topLevelItem(0)
    dir_a_item = root_item.child(0)
    widget.directory_tree.setCurrentItem(dir_a_item)
    widget.prompt_list.setCurrentRow(0)

    # When: 重命名目录A
    monkeypatch.setattr(
        "app.tools.prompt_manager.widget.QInputDialog.getText",
        lambda *args, **kwargs: ("目录A-重命名", True),
    )
    widget._rename_directory()

    # Then: 目录名称已更新
    renamed = repo.get_directory(dir_a.id)
    assert renamed is not None
    assert renamed.name == "目录A-重命名"

    # 目录刷新后需要重新选中 Prompt
    widget.prompt_list.setCurrentRow(0)

    # When: 移动 Prompt 到目录B
    monkeypatch.setattr(
        "app.tools.prompt_manager.widget.QInputDialog.getItem",
        lambda *args, **kwargs: ("目录B", True),
    )
    widget._move_prompt()

    # Then: Prompt 目录变更且版本未新增
    moved = repo.get_prompt(prompt.id)
    versions = repo.list_versions(prompt.id)
    assert moved is not None
    assert moved.directory_id == dir_b.id
    assert len(versions) == 1
    assert widget._selected_directory_id() == dir_b.id
    assert widget.prompt_list.count() == 1
    assert widget.prompt_list.currentItem() is not None
    assert widget.prompt_list.currentItem().data(Qt.ItemDataRole.UserRole) == prompt.id

    widget.close()
    app.quit()
