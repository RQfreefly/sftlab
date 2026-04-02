"""Token 工具控件测试。"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.tools.token_counter.tokenizer import TokenStats
from PySide6.QtWidgets import QApplication

from app.tools.token_counter.widget import TokenCounterWidget


def test_token_widget_recounts_realtime(monkeypatch) -> None:
    # Given: Token 统计控件
    def fake_count_tokens(model_name: str, text: str) -> TokenStats:
        return TokenStats(
            model_name=model_name,
            token_count=len(text) + len(model_name),
            char_count=len(text),
        )

    monkeypatch.setattr("app.tools.token_counter.widget.count_tokens", fake_count_tokens)

    app = QApplication.instance() or QApplication(sys.argv)
    widget = TokenCounterWidget()

    # When: 输入文本并切换模型
    widget.text_editor.setPlainText("hello, 世界")
    widget.model_combo.setCurrentText("qwen")

    # Then: 统计标签更新
    expected_token_count = len("hello, 世界") + len("qwen")
    assert widget.token_label.text() == str(expected_token_count)
    assert widget.char_label.text() == str(len("hello, 世界"))

    widget.close()
    app.quit()
