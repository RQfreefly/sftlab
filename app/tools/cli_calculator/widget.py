"""命令行计算器页面。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.tools.cli_calculator.engine import CalculatorContext, CalculatorError, execute_command


class CliCalculatorWidget(QWidget):
    """CLI 计算器界面。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = CalculatorContext()
        self._build_ui()
        self._bind_events()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.history_list = QListWidget(self)
        layout.addWidget(self.history_list, stretch=1)

        row = QHBoxLayout()
        self.input_line = QLineEdit(self)
        self.input_line.setPlaceholderText("输入表达式，例如：a = 10 或 log(100, 10)")
        self.run_button = QPushButton("执行", self)
        self.clear_button = QPushButton("清空历史", self)
        row.addWidget(self.input_line, stretch=1)
        row.addWidget(self.run_button)
        row.addWidget(self.clear_button)
        layout.addLayout(row)

        self.status_label = QLabel("就绪", self)
        layout.addWidget(self.status_label)

    def _bind_events(self) -> None:
        self.run_button.clicked.connect(self._run_command)
        self.clear_button.clicked.connect(self._clear_history)
        self.input_line.returnPressed.connect(self._run_command)

    def _run_command(self) -> None:
        command = self.input_line.text().strip()
        if not command:
            self.status_label.setText("输入不能为空")
            return

        self._append_history(f"> {command}")
        try:
            output = execute_command(command, self._context)
            self._append_history(f"= {output}")
            self.status_label.setText("执行成功")
        except CalculatorError as exc:
            self._append_history(f"! {exc}")
            self.status_label.setText(f"执行失败：{exc}")

        self.input_line.clear()

    def _clear_history(self) -> None:
        self.history_list.clear()
        self.status_label.setText("历史已清空")

    def _append_history(self, text: str) -> None:
        self.history_list.addItem(QListWidgetItem(text))
        self.history_list.scrollToBottom()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_L:
            self._clear_history()
            return
        super().keyPressEvent(event)
