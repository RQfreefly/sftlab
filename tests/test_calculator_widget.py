"""CLI 计算器控件测试。"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.tools.cli_calculator.widget import CliCalculatorWidget


def test_calculator_widget_runs_command_and_updates_history() -> None:
    # Given: 计算器控件
    app = QApplication.instance() or QApplication(sys.argv)
    widget = CliCalculatorWidget()

    # When: 输入并执行命令
    widget.input_line.setText("a = 10")
    widget.run_button.click()
    widget.input_line.setText("a + 5")
    widget.run_button.click()

    # Then: 历史记录包含命令与结果
    history = [widget.history_list.item(i).text() for i in range(widget.history_list.count())]
    assert "> a = 10" in history
    assert "= a = 10" in history
    assert "= 15" in history

    widget.close()
    app.quit()
