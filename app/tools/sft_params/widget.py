"""SFT 参数管理页面。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.storage import SftParamTemplate, SftParamTemplateRepository, SftParamTemplateVersion
from app.tools.sft_params.parser import validate_cli_template


class SftParamManagerWidget(QWidget):
    """参数模板管理主界面。"""

    def __init__(self, repository: SftParamTemplateRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._repository = repository
        self._current_template_id: int | None = None

        self._build_ui()
        self._bind_events()
        self.refresh_templates()

    def _build_ui(self) -> None:
        """构建页面布局。"""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        root_layout.addWidget(splitter, stretch=1)

        left_panel = QWidget(splitter)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(QLabel("模板列表", left_panel))

        self.template_list = QListWidget(left_panel)
        self.template_list.setMinimumWidth(240)
        left_layout.addWidget(self.template_list, stretch=1)

        left_button_row = QHBoxLayout()
        self.new_button = QPushButton("新建", left_panel)
        self.delete_button = QPushButton("删除", left_panel)
        self.refresh_button = QPushButton("刷新", left_panel)
        left_button_row.addWidget(self.new_button)
        left_button_row.addWidget(self.delete_button)
        left_button_row.addWidget(self.refresh_button)
        left_layout.addLayout(left_button_row)

        right_panel = QWidget(splitter)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        right_layout.addWidget(QLabel("模板名称", right_panel))
        self.name_input = QLineEdit(right_panel)
        self.name_input.setPlaceholderText("例如：Nanbeige4.1-3B-Lora")
        right_layout.addWidget(self.name_input)

        right_layout.addWidget(QLabel("CLI 文本", right_panel))
        self.cli_editor = QPlainTextEdit(right_panel)
        self.cli_editor.setPlaceholderText("在此粘贴或编辑完整训练命令")
        right_layout.addWidget(self.cli_editor, stretch=1)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("保存", right_panel)
        self.validate_button = QPushButton("校验", right_panel)
        self.copy_button = QPushButton("复制CLI", right_panel)
        action_row.addWidget(self.save_button)
        action_row.addWidget(self.validate_button)
        action_row.addWidget(self.copy_button)
        right_layout.addLayout(action_row)

        version_panel = QWidget(right_panel)
        version_layout = QHBoxLayout(version_panel)
        version_layout.setContentsMargins(0, 0, 0, 0)
        version_layout.setSpacing(8)

        history_panel = QWidget(version_panel)
        history_layout = QVBoxLayout(history_panel)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.setSpacing(4)
        history_layout.addWidget(QLabel("版本历史", history_panel))
        self.version_list = QListWidget(history_panel)
        self.version_list.setMinimumWidth(280)
        history_layout.addWidget(self.version_list, stretch=1)

        preview_panel = QWidget(version_panel)
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(4)
        preview_layout.addWidget(QLabel("版本预览（只读）", preview_panel))
        self.version_preview = QPlainTextEdit(preview_panel)
        self.version_preview.setReadOnly(True)
        self.version_preview.setPlaceholderText("选择历史版本后，在此预览 CLI 内容")
        preview_layout.addWidget(self.version_preview, stretch=1)

        version_layout.addWidget(history_panel, stretch=1)
        version_layout.addWidget(preview_panel, stretch=2)
        right_layout.addWidget(version_panel, stretch=1)

        version_row = QHBoxLayout()
        self.restore_button = QPushButton("恢复所选版本", right_panel)
        version_row.addWidget(self.restore_button)
        right_layout.addLayout(version_row)

        self.status_label = QLabel("就绪", self)
        root_layout.addWidget(self.status_label)

        splitter.setSizes([280, 900])

    def _bind_events(self) -> None:
        """绑定交互事件。"""
        self.template_list.currentItemChanged.connect(self._on_template_selected)
        self.new_button.clicked.connect(self._reset_editor)
        self.delete_button.clicked.connect(self._delete_current_template)
        self.refresh_button.clicked.connect(self.refresh_templates)
        self.save_button.clicked.connect(self._save_template)
        self.validate_button.clicked.connect(self._validate_template)
        self.copy_button.clicked.connect(self._copy_cli_text)
        self.version_list.currentItemChanged.connect(self._on_version_selected)
        self.restore_button.clicked.connect(self._restore_selected_version)

    def refresh_templates(self) -> None:
        """刷新模板列表。"""
        templates = self._repository.list_templates()

        self.template_list.clear()
        for template in templates:
            item = QListWidgetItem(template.name)
            item.setData(Qt.ItemDataRole.UserRole, template.id)
            self.template_list.addItem(item)

        self._set_status(f"已加载模板 {len(templates)} 个")

        if self._current_template_id is None:
            return

        self._select_template_by_id(self._current_template_id)

    def _select_template_by_id(self, template_id: int) -> None:
        for index in range(self.template_list.count()):
            item = self.template_list.item(index)
            item_id = item.data(Qt.ItemDataRole.UserRole)
            if item_id == template_id:
                self.template_list.setCurrentRow(index)
                return

    def _on_template_selected(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            return

        template_id = current.data(Qt.ItemDataRole.UserRole)
        if not isinstance(template_id, int):
            return

        template = self._repository.get_template(template_id)
        if template is None:
            self._set_status("模板不存在，可能已被删除")
            return

        self._load_template(template)

    def _load_template(self, template: SftParamTemplate) -> None:
        self._current_template_id = template.id
        self.name_input.setText(template.name)
        self.cli_editor.setPlainText(template.cli_text)
        self._load_versions(template.id)
        self._set_preview_text(template.cli_text)
        self._set_status(f"已加载模板: {template.name}")

    def _load_versions(self, template_id: int) -> None:
        versions = self._repository.list_versions(template_id)
        self.version_list.clear()

        for version in versions:
            label = f"v{version.version_no}  {version.created_at}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, version.id)
            self.version_list.addItem(item)

        if self.version_list.count() > 0:
            self.version_list.setCurrentRow(0)
        else:
            self._set_preview_text("")

    def _reset_editor(self) -> None:
        self._current_template_id = None
        self.name_input.clear()
        self.cli_editor.clear()
        self.version_list.clear()
        self._set_preview_text("")
        self.template_list.clearSelection()
        self._set_status("新建模式")

    def _save_template(self) -> None:
        name = self.name_input.text()
        cli_text = self.cli_editor.toPlainText()

        result = validate_cli_template(name, cli_text)
        if not result.is_valid:
            self._set_status("保存失败：" + "；".join(result.errors))
            return

        if result.warnings:
            self._set_status("校验通过（含警告）：" + "；".join(result.warnings))

        try:
            if self._current_template_id is None:
                template = self._repository.create_template(name=name, cli_text=cli_text)
            else:
                template = self._repository.update_template(
                    template_id=self._current_template_id,
                    name=name,
                    cli_text=cli_text,
                )
        except (ValueError, KeyError) as exc:
            self._set_status(f"保存失败：{exc}")
            return

        self._current_template_id = template.id
        self.refresh_templates()
        self._select_template_by_id(template.id)
        self._set_status(f"保存成功：{template.name}")

    def _delete_current_template(self) -> None:
        if self._current_template_id is None:
            self._set_status("请先选择模板")
            return

        template = self._repository.get_template(self._current_template_id)
        if template is None:
            self._set_status("模板不存在")
            return

        answer = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除模板“{template.name}”吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self._set_status("已取消删除")
            return

        self._repository.delete_template(template.id)
        self._reset_editor()
        self.refresh_templates()
        self._set_status(f"已删除模板：{template.name}")

    def _validate_template(self) -> None:
        result = validate_cli_template(
            name=self.name_input.text(),
            cli_text=self.cli_editor.toPlainText(),
        )
        if result.is_valid:
            warning_text = f"；警告 {len(result.warnings)}" if result.warnings else ""
            self._set_status(
                "校验通过："
                f"环境变量 {len(result.analysis.env_vars)}，参数 {len(result.analysis.param_flags)}"
                f"{warning_text}"
            )
            return

        self._set_status("校验失败：" + "；".join(result.errors))

    def _copy_cli_text(self) -> None:
        text = self.cli_editor.toPlainText()
        if not text.strip():
            self._set_status("复制失败：CLI 内容为空")
            return

        QApplication.clipboard().setText(text)
        self._set_status("已复制 CLI 到剪贴板")

    def _restore_selected_version(self) -> None:
        item = self.version_list.currentItem()
        if item is None:
            self._set_status("请先选择一个历史版本")
            return

        version_id = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(version_id, int):
            self._set_status("历史版本数据异常")
            return

        version = self._repository.get_version(version_id)
        if version is None:
            self._set_status("历史版本不存在")
            return

        self._apply_version(version)

    def _on_version_selected(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            self._set_preview_text("")
            return

        version_id = current.data(Qt.ItemDataRole.UserRole)
        if not isinstance(version_id, int):
            self._set_status("历史版本数据异常")
            self._set_preview_text("")
            return

        version = self._repository.get_version(version_id)
        if version is None:
            self._set_status("历史版本不存在")
            self._set_preview_text("")
            return

        self._set_preview_text(version.cli_text)
        self._set_status(f"已预览 v{version.version_no}")

    def _apply_version(self, version: SftParamTemplateVersion) -> None:
        self.cli_editor.setPlainText(version.cli_text)
        self._set_preview_text(version.cli_text)
        self._set_status(f"已恢复到 v{version.version_no}，点击保存后生效")

    def _set_preview_text(self, text: str) -> None:
        self.version_preview.setPlainText(text)

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)
