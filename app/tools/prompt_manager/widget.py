"""Prompt 管理页面。"""

from __future__ import annotations

import difflib

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
)

from app.storage import PromptDirectory, PromptRepository, PromptTemplate, PromptVersion


class PromptManagerWidget(QWidget):
    """Prompt 管理工具 UI。"""

    def __init__(self, repository: PromptRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._repository = repository
        self._current_prompt_id: int | None = None
        self._current_prompt_directory_id: int | None = None
        self._directory_item_map: dict[int, QTreeWidgetItem] = {}

        self._build_ui()
        self._bind_events()

        self.refresh_directories(preserve_current=False)
        self.refresh_prompts()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        root_layout.addWidget(splitter, stretch=1)

        left_panel = QWidget(splitter)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        left_layout.addWidget(QLabel("目录分类", left_panel))
        self.directory_tree = QTreeWidget(left_panel)
        self.directory_tree.setHeaderHidden(True)
        self.directory_tree.setMinimumWidth(260)
        left_layout.addWidget(self.directory_tree, stretch=2)

        dir_buttons = QHBoxLayout()
        self.new_dir_button = QPushButton("新建目录", left_panel)
        self.rename_dir_button = QPushButton("重命名", left_panel)
        self.delete_dir_button = QPushButton("删除目录", left_panel)
        self.refresh_dir_button = QPushButton("刷新", left_panel)
        dir_buttons.addWidget(self.new_dir_button)
        dir_buttons.addWidget(self.rename_dir_button)
        dir_buttons.addWidget(self.delete_dir_button)
        dir_buttons.addWidget(self.refresh_dir_button)
        left_layout.addLayout(dir_buttons)

        left_layout.addWidget(QLabel("Prompt 列表", left_panel))
        self.prompt_list = QListWidget(left_panel)
        left_layout.addWidget(self.prompt_list, stretch=3)

        prompt_buttons = QHBoxLayout()
        self.new_prompt_button = QPushButton("新建Prompt", left_panel)
        self.move_prompt_button = QPushButton("移动目录", left_panel)
        self.delete_prompt_button = QPushButton("删除Prompt", left_panel)
        self.refresh_prompt_button = QPushButton("刷新", left_panel)
        prompt_buttons.addWidget(self.new_prompt_button)
        prompt_buttons.addWidget(self.move_prompt_button)
        prompt_buttons.addWidget(self.delete_prompt_button)
        prompt_buttons.addWidget(self.refresh_prompt_button)
        left_layout.addLayout(prompt_buttons)

        right_panel = QWidget(splitter)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        right_layout.addWidget(QLabel("标题", right_panel))
        self.title_input = QLineEdit(right_panel)
        self.title_input.setPlaceholderText("例如：代码评审系统提示词")
        right_layout.addWidget(self.title_input)

        right_layout.addWidget(QLabel("内容", right_panel))
        self.content_editor = QPlainTextEdit(right_panel)
        self.content_editor.setPlaceholderText("在此编辑 Prompt 内容")
        right_layout.addWidget(self.content_editor, stretch=1)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("保存", right_panel)
        self.copy_button = QPushButton("复制", right_panel)
        self.diff_button = QPushButton("对比所选版本", right_panel)
        action_row.addWidget(self.save_button)
        action_row.addWidget(self.copy_button)
        action_row.addWidget(self.diff_button)
        right_layout.addLayout(action_row)

        version_panel = QWidget(right_panel)
        version_layout = QHBoxLayout(version_panel)
        version_layout.setContentsMargins(0, 0, 0, 0)
        version_layout.setSpacing(8)

        version_left = QWidget(version_panel)
        version_left_layout = QVBoxLayout(version_left)
        version_left_layout.setContentsMargins(0, 0, 0, 0)
        version_left_layout.setSpacing(4)
        version_left_layout.addWidget(QLabel("版本历史", version_left))
        self.version_list = QListWidget(version_left)
        self.version_list.setMinimumWidth(260)
        version_left_layout.addWidget(self.version_list, stretch=1)

        version_right = QWidget(version_panel)
        version_right_layout = QVBoxLayout(version_right)
        version_right_layout.setContentsMargins(0, 0, 0, 0)
        version_right_layout.setSpacing(4)

        self.preview_tabs = QTabWidget(version_right)
        self.version_preview = QPlainTextEdit(version_right)
        self.version_preview.setReadOnly(True)
        self.version_preview.setPlaceholderText("选择历史版本后，在这里预览")
        self.diff_preview = QPlainTextEdit(version_right)
        self.diff_preview.setReadOnly(True)
        self.diff_preview.setPlaceholderText("点击“对比所选版本”后展示差异")
        self.preview_tabs.addTab(self.version_preview, "版本预览")
        self.preview_tabs.addTab(self.diff_preview, "Diff")
        version_right_layout.addWidget(self.preview_tabs, stretch=1)

        version_layout.addWidget(version_left, stretch=1)
        version_layout.addWidget(version_right, stretch=2)
        right_layout.addWidget(version_panel, stretch=1)

        restore_row = QHBoxLayout()
        self.restore_button = QPushButton("恢复所选版本", right_panel)
        restore_row.addWidget(self.restore_button)
        right_layout.addLayout(restore_row)

        self.status_label = QLabel("就绪", self)
        root_layout.addWidget(self.status_label)

        splitter.setSizes([350, 900])

    def _bind_events(self) -> None:
        self.directory_tree.currentItemChanged.connect(self._on_directory_selected)
        self.prompt_list.currentItemChanged.connect(self._on_prompt_selected)
        self.version_list.currentItemChanged.connect(self._on_version_selected)

        self.new_dir_button.clicked.connect(self._create_directory)
        self.rename_dir_button.clicked.connect(self._rename_directory)
        self.delete_dir_button.clicked.connect(self._delete_directory)
        self.refresh_dir_button.clicked.connect(self.refresh_directories)

        self.new_prompt_button.clicked.connect(self._reset_prompt_editor)
        self.move_prompt_button.clicked.connect(self._move_prompt)
        self.delete_prompt_button.clicked.connect(self._delete_prompt)
        self.refresh_prompt_button.clicked.connect(self.refresh_prompts)

        self.save_button.clicked.connect(self._save_prompt)
        self.copy_button.clicked.connect(self._copy_prompt)
        self.diff_button.clicked.connect(self._diff_with_selected_version)
        self.restore_button.clicked.connect(self._restore_selected_version)

    def refresh_directories(
        self,
        selected_directory_id: int | None = None,
        preserve_current: bool = True,
    ) -> None:
        """刷新目录树。"""
        previous_directory_id = self._selected_directory_id() if preserve_current else None
        directories = self._repository.list_directories()

        self.directory_tree.clear()
        self._directory_item_map.clear()

        root_item = QTreeWidgetItem(["全部目录"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, None)
        self.directory_tree.addTopLevelItem(root_item)

        for directory in directories:
            item = QTreeWidgetItem([directory.name])
            item.setData(0, Qt.ItemDataRole.UserRole, directory.id)
            self._directory_item_map[directory.id] = item

        for directory in directories:
            item = self._directory_item_map[directory.id]
            if directory.parent_id is None:
                root_item.addChild(item)
                continue

            parent_item = self._directory_item_map.get(directory.parent_id)
            if parent_item is None:
                root_item.addChild(item)
            else:
                parent_item.addChild(item)

        self.directory_tree.expandAll()
        target_directory_id = selected_directory_id if selected_directory_id is not None else previous_directory_id
        if target_directory_id is None:
            self.directory_tree.setCurrentItem(root_item)
        else:
            self._select_directory_by_id(target_directory_id)
            if self.directory_tree.currentItem() is None:
                self.directory_tree.setCurrentItem(root_item)
        self._set_status(f"目录加载完成：{len(directories)} 个")

    def refresh_prompts(self) -> None:
        """按当前目录刷新 Prompt 列表。"""
        directory_id = self._selected_directory_id()
        prompts = self._repository.list_prompts(directory_id=directory_id)

        self.prompt_list.clear()
        for prompt in prompts:
            item = QListWidgetItem(prompt.title)
            item.setData(Qt.ItemDataRole.UserRole, prompt.id)
            self.prompt_list.addItem(item)

        self._set_status(f"Prompt 加载完成：{len(prompts)} 条")
        if self._current_prompt_id is not None:
            self._select_prompt_by_id(self._current_prompt_id)

    def _on_directory_selected(
        self,
        current: QTreeWidgetItem | None,
        _previous: QTreeWidgetItem | None,
    ) -> None:
        if current is None:
            return
        self._current_prompt_id = None
        self._reset_prompt_editor(keep_status=True)
        self.refresh_prompts()

    def _create_directory(self) -> None:
        parent_id = self._selected_directory_id()
        parent_label = "根目录" if parent_id is None else f"目录 ID={parent_id}"

        name, ok = QInputDialog.getText(self, "新建目录", f"请输入目录名称（父级：{parent_label}）")
        if not ok:
            return

        try:
            created = self._repository.create_directory(name=name, parent_id=parent_id)
        except (ValueError, KeyError) as exc:
            self._set_status(f"创建目录失败：{exc}")
            return

        self.refresh_directories(selected_directory_id=created.id)
        self._select_directory_by_id(created.id)
        self._set_status(f"目录已创建：{created.name}")

    def _rename_directory(self) -> None:
        directory_id = self._selected_directory_id()
        if directory_id is None:
            self._set_status("根节点不可重命名")
            return

        directory = self._repository.get_directory(directory_id)
        if directory is None:
            self._set_status("目录不存在")
            return

        new_name, ok = QInputDialog.getText(
            self,
            "重命名目录",
            "请输入新目录名称",
            text=directory.name,
        )
        if not ok:
            return

        try:
            renamed = self._repository.rename_directory(directory_id, new_name)
        except (ValueError, KeyError) as exc:
            self._set_status(f"重命名失败：{exc}")
            return

        self.refresh_directories(selected_directory_id=renamed.id)
        self._set_status(f"目录已重命名：{renamed.name}")

    def _delete_directory(self) -> None:
        directory_id = self._selected_directory_id()
        if directory_id is None:
            self._set_status("根节点不可删除")
            return

        answer = QMessageBox.question(
            self,
            "确认删除目录",
            "仅空目录可删除，确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self._repository.delete_directory(directory_id)
        except (ValueError, KeyError) as exc:
            self._set_status(f"删除目录失败：{exc}")
            return

        self.refresh_directories(preserve_current=False)
        self.refresh_prompts()
        self._set_status("目录已删除")

    def _on_prompt_selected(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return

        prompt_id = current.data(Qt.ItemDataRole.UserRole)
        if not isinstance(prompt_id, int):
            return

        prompt = self._repository.get_prompt(prompt_id)
        if prompt is None:
            self._set_status("Prompt 不存在，可能已被删除")
            return

        self._load_prompt(prompt)

    def _load_prompt(self, prompt: PromptTemplate) -> None:
        self._current_prompt_id = prompt.id
        self._current_prompt_directory_id = prompt.directory_id
        self.title_input.setText(prompt.title)
        self.content_editor.setPlainText(prompt.content)

        self._load_versions(prompt.id)
        self._set_status(f"已加载 Prompt：{prompt.title}")

    def _load_versions(self, prompt_id: int) -> None:
        versions = self._repository.list_versions(prompt_id)
        self.version_list.clear()

        for version in versions:
            item = QListWidgetItem(f"v{version.version_no}  {version.created_at}")
            item.setData(Qt.ItemDataRole.UserRole, version.id)
            self.version_list.addItem(item)

        if self.version_list.count() > 0:
            self.version_list.setCurrentRow(0)
        else:
            self.version_preview.clear()
            self.diff_preview.clear()

    def _on_version_selected(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            self.version_preview.clear()
            return

        version_id = current.data(Qt.ItemDataRole.UserRole)
        if not isinstance(version_id, int):
            self._set_status("版本数据异常")
            return

        version = self._repository.get_version(version_id)
        if version is None:
            self._set_status("版本不存在")
            return

        self.version_preview.setPlainText(version.content)
        self.preview_tabs.setCurrentWidget(self.version_preview)
        self._set_status(f"已预览 v{version.version_no}")

    def _reset_prompt_editor(self, keep_status: bool = False) -> None:
        self._current_prompt_id = None
        self._current_prompt_directory_id = None
        self.title_input.clear()
        self.content_editor.clear()
        self.version_list.clear()
        self.version_preview.clear()
        self.diff_preview.clear()
        self.prompt_list.clearSelection()
        if not keep_status:
            self._set_status("新建 Prompt 模式")

    def _save_prompt(self) -> None:
        directory_id = self._selected_directory_id()
        title = self.title_input.text()
        content = self.content_editor.toPlainText()

        try:
            if self._current_prompt_id is None:
                prompt = self._repository.create_prompt(directory_id, title, content)
            else:
                prompt = self._repository.update_prompt(
                    prompt_id=self._current_prompt_id,
                    directory_id=self._current_prompt_directory_id,
                    title=title,
                    content=content,
                )
        except (ValueError, KeyError) as exc:
            self._set_status(f"保存失败：{exc}")
            return

        self._current_prompt_id = prompt.id
        self._current_prompt_directory_id = prompt.directory_id
        self.refresh_prompts()
        self._select_prompt_by_id(prompt.id)
        self._set_status(f"保存成功：{prompt.title}")

    def _move_prompt(self) -> None:
        if self._current_prompt_id is None:
            self._set_status("请先选择 Prompt")
            return

        prompt = self._repository.get_prompt(self._current_prompt_id)
        if prompt is None:
            self._set_status("Prompt 不存在，可能已被删除")
            return

        directory_choices = self._build_directory_choices()
        labels = [label for label, _directory_id in directory_choices]
        if not labels:
            self._set_status("暂无可用目录")
            return

        current_index = 0
        for index, (_label, directory_id) in enumerate(directory_choices):
            if directory_id == prompt.directory_id:
                current_index = index
                break

        selected_label, ok = QInputDialog.getItem(
            self,
            "移动 Prompt",
            "请选择目标目录",
            labels,
            current=current_index,
            editable=False,
        )
        if not ok:
            return

        target_directory_id = None
        for label, directory_id in directory_choices:
            if label == selected_label:
                target_directory_id = directory_id
                break

        if prompt.directory_id == target_directory_id:
            self._set_status("目标目录未变化")
            return

        try:
            moved = self._repository.move_prompt(prompt.id, target_directory_id)
        except (ValueError, KeyError) as exc:
            self._set_status(f"移动失败：{exc}")
            return

        self._current_prompt_directory_id = moved.directory_id
        if moved.directory_id is None:
            self.refresh_directories(preserve_current=False)
        else:
            self.refresh_directories(selected_directory_id=moved.directory_id, preserve_current=False)
        self.refresh_prompts()
        self._select_prompt_by_id(moved.id)
        self._set_status(f"Prompt 已移动到：{selected_label}")

    def _delete_prompt(self) -> None:
        if self._current_prompt_id is None:
            self._set_status("请先选择 Prompt")
            return

        answer = QMessageBox.question(
            self,
            "确认删除 Prompt",
            "删除后版本历史将一并删除，确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self._repository.delete_prompt(self._current_prompt_id)
        self._reset_prompt_editor()
        self.refresh_prompts()
        self._set_status("Prompt 已删除")

    def _copy_prompt(self) -> None:
        text = self.content_editor.toPlainText()
        if not text.strip():
            self._set_status("复制失败：Prompt 内容为空")
            return

        QApplication.clipboard().setText(text)
        self._set_status("已复制 Prompt")

    def _diff_with_selected_version(self) -> None:
        item = self.version_list.currentItem()
        if item is None:
            self._set_status("请先选择版本")
            return

        version_id = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(version_id, int):
            self._set_status("版本数据异常")
            return

        version = self._repository.get_version(version_id)
        if version is None:
            self._set_status("版本不存在")
            return

        current_text = self.content_editor.toPlainText().splitlines(keepends=True)
        version_text = version.content.splitlines(keepends=True)

        diff_lines = list(
            difflib.unified_diff(
                version_text,
                current_text,
                fromfile=f"v{version.version_no}",
                tofile="current",
                lineterm="",
            )
        )

        if not diff_lines:
            self.diff_preview.setPlainText("无差异")
        else:
            self.diff_preview.setPlainText("\n".join(diff_lines))
        self.preview_tabs.setCurrentWidget(self.diff_preview)
        self._set_status(f"Diff 已生成（对比 v{version.version_no}）")

    def _restore_selected_version(self) -> None:
        item = self.version_list.currentItem()
        if item is None:
            self._set_status("请先选择版本")
            return

        version_id = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(version_id, int):
            self._set_status("版本数据异常")
            return

        version = self._repository.get_version(version_id)
        if version is None:
            self._set_status("版本不存在")
            return

        self.content_editor.setPlainText(version.content)
        self.version_preview.setPlainText(version.content)
        self.preview_tabs.setCurrentWidget(self.version_preview)
        self._set_status(f"已恢复到 v{version.version_no}，点击保存后生效")

    def _selected_directory_id(self) -> int | None:
        item = self.directory_tree.currentItem()
        if item is None:
            return None

        directory_id = item.data(0, Qt.ItemDataRole.UserRole)
        if directory_id is None:
            return None
        if isinstance(directory_id, int):
            return directory_id
        return None

    def _select_directory_by_id(self, directory_id: int) -> None:
        item = self._directory_item_map.get(directory_id)
        if item is None:
            return
        self.directory_tree.setCurrentItem(item)

    def _build_directory_choices(self) -> list[tuple[str, int | None]]:
        directories = self._repository.list_directories()
        children: dict[int | None, list[PromptDirectory]] = {}
        for directory in directories:
            children.setdefault(directory.parent_id, []).append(directory)

        for siblings in children.values():
            siblings.sort(key=lambda item: (item.name, item.id))

        choices: list[tuple[str, int | None]] = [("根目录", None)]

        def walk(parent_id: int | None, prefix: str) -> None:
            for directory in children.get(parent_id, []):
                label = f"{prefix}/{directory.name}" if prefix else directory.name
                choices.append((label, directory.id))
                walk(directory.id, label)

        walk(None, "")
        return choices

    def _select_prompt_by_id(self, prompt_id: int) -> None:
        for index in range(self.prompt_list.count()):
            item = self.prompt_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == prompt_id:
                self.prompt_list.setCurrentRow(index)
                return

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)
