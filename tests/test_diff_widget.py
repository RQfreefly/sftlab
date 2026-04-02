"""Diff 工具控件测试。"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.tools.diff_tool.widget import DiffToolWidget


def test_diff_widget_compares_line_diff() -> None:
    # Given: Diff 工具控件
    app = QApplication.instance() or QApplication(sys.argv)
    widget = DiffToolWidget()

    # When: 输入左右文本并执行行级比较
    widget.mode_combo.setCurrentText("line")
    widget.type_combo.setCurrentText("text")
    widget.left_editor.setPlainText("a\nb")
    widget.right_editor.setPlainText("a\nc")
    widget.compare_button.click()

    # Then: 结果区包含差异
    output = widget.result_view.toPlainText()
    assert "-b" in output
    assert "+c" in output
    assert "行级差异" in widget.status_label.text()

    widget.close()
    app.quit()


def test_diff_widget_swap_and_clear() -> None:
    # Given: Diff 工具控件
    app = QApplication.instance() or QApplication(sys.argv)
    widget = DiffToolWidget()
    widget.left_editor.setPlainText("left")
    widget.right_editor.setPlainText("right")

    # When: 互换文本
    widget.swap_button.click()

    # Then: 左右文本已交换
    assert widget.left_editor.toPlainText() == "right"
    assert widget.right_editor.toPlainText() == "left"

    # When: 清空
    widget.clear_button.click()

    # Then: 输入与结果都清空
    assert widget.left_editor.toPlainText() == ""
    assert widget.right_editor.toPlainText() == ""
    assert widget.result_view.toPlainText() == ""

    widget.close()
    app.quit()
