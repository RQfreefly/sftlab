"""Diff 工具页面。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
)

from app.tools.diff_tool.engine import DIFF_MODES, DIFF_TYPES, compute_diff


class DiffToolWidget(QWidget):
    """文本差异比较控件。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._bind_events()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        control_row = QHBoxLayout()

        control_row.addWidget(QLabel("比较模式", self))
        self.mode_combo = QComboBox(self)
        self.mode_combo.addItems(DIFF_MODES)
        control_row.addWidget(self.mode_combo)

        control_row.addWidget(QLabel("文本类型", self))
        self.type_combo = QComboBox(self)
        self.type_combo.addItems(DIFF_TYPES)
        control_row.addWidget(self.type_combo)

        self.compare_button = QPushButton("开始比较", self)
        self.swap_button = QPushButton("左右互换", self)
        self.clear_button = QPushButton("清空", self)
        control_row.addWidget(self.compare_button)
        control_row.addWidget(self.swap_button)
        control_row.addWidget(self.clear_button)

        control_row.addStretch(1)
        root_layout.addLayout(control_row)

        editor_splitter = QSplitter(self)
        self.left_editor = QPlainTextEdit(editor_splitter)
        self.left_editor.setPlaceholderText("左侧文本")
        self.right_editor = QPlainTextEdit(editor_splitter)
        self.right_editor.setPlaceholderText("右侧文本")
        editor_splitter.setSizes([500, 500])
        root_layout.addWidget(editor_splitter, stretch=2)

        self.result_view = QTextEdit(self)
        self.result_view.setReadOnly(True)
        self.result_view.setPlaceholderText("差异结果")
        root_layout.addWidget(self.result_view, stretch=1)

        self.status_label = QLabel("就绪", self)
        root_layout.addWidget(self.status_label)

    def _bind_events(self) -> None:
        self.compare_button.clicked.connect(self._compare)
        self.swap_button.clicked.connect(self._swap)
        self.clear_button.clicked.connect(self._clear)

    def _compare(self) -> None:
        result = compute_diff(
            left_text=self.left_editor.toPlainText(),
            right_text=self.right_editor.toPlainText(),
            mode=self.mode_combo.currentText(),
            diff_type=self.type_combo.currentText(),
        )

        self.result_view.setHtml(result.html_text)
        self.status_label.setText(result.summary)

    def _swap(self) -> None:
        left = self.left_editor.toPlainText()
        right = self.right_editor.toPlainText()
        self.left_editor.setPlainText(right)
        self.right_editor.setPlainText(left)
        self.status_label.setText("左右文本已互换")

    def _clear(self) -> None:
        self.left_editor.clear()
        self.right_editor.clear()
        self.result_view.clear()
        self.status_label.setText("已清空")
