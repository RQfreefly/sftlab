"""Token 统计页面。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.tools.token_counter.tokenizer import count_tokens, list_supported_models


class TokenCounterWidget(QWidget):
    """支持模型切换与实时统计。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._bind_events()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        form = QFormLayout()
        self.model_combo = QComboBox(self)
        for model in list_supported_models():
            self.model_combo.addItem(model)

        self.token_label = QLabel("0", self)
        self.char_label = QLabel("0", self)

        form.addRow("模型", self.model_combo)
        form.addRow("Token 数", self.token_label)
        form.addRow("字符数", self.char_label)
        layout.addLayout(form)

        self.text_editor = QPlainTextEdit(self)
        self.text_editor.setPlaceholderText("输入文本后实时统计 Token 数")
        layout.addWidget(self.text_editor, stretch=1)

        self.status_label = QLabel("就绪", self)
        layout.addWidget(self.status_label)

    def _bind_events(self) -> None:
        self.model_combo.currentIndexChanged.connect(self._recount)
        self.text_editor.textChanged.connect(self._recount)

    def _recount(self) -> None:
        model = self.model_combo.currentText()
        text = self.text_editor.toPlainText()
        if not text:
            self.token_label.setText("0")
            self.char_label.setText("0")
            self.status_label.setText("就绪")
            return

        try:
            stats = count_tokens(model, text)
        except (ValueError, RuntimeError) as exc:
            self.status_label.setText(f"统计失败：{exc}")
            return

        self.token_label.setText(str(stats.token_count))
        self.char_label.setText(str(stats.char_count))
        self.status_label.setText(f"已统计：{stats.model_name}")
