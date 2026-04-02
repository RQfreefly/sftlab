"""MainWindow 冒烟测试。"""

from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication

from app.main import build_registry
from app.ui.main_window import MainWindow


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_main_window_loads_tools() -> None:
    # Given: Qt Application 和默认工具注册表
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(build_registry())

    # When: 主窗口完成初始化
    sidebar_count = window.sidebar.count()
    workspace_count = window.workspace.count()

    # Then: 侧边栏与工作区数量一致，且至少有 1 个工具
    assert sidebar_count == workspace_count
    assert sidebar_count >= 1

    window.close()
    app.quit()
