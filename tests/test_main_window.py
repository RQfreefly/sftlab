"""MainWindow 冒烟与配置联动测试。"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.main import build_registry
from app.storage import ConfigRepository, Database
from app.ui.main_window import MainWindow


def test_main_window_loads_tools(tmp_path) -> None:
    # Given: Qt Application、默认注册表与配置仓储
    app = QApplication.instance() or QApplication(sys.argv)
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = ConfigRepository(database)
    window = MainWindow(build_registry(), config_repo=repo)

    # When: 主窗口完成初始化
    sidebar_count = window.sidebar.count()
    workspace_count = window.workspace.count()

    # Then: 侧边栏与工作区数量一致，且至少有 1 个工具
    assert sidebar_count == workspace_count
    assert sidebar_count >= 1

    window.close()
    app.quit()


def test_main_window_persists_ui_state_on_close(tmp_path) -> None:
    # Given: 一个可写配置仓储
    app = QApplication.instance() or QApplication(sys.argv)
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = ConfigRepository(database)

    # When: 调整窗口尺寸并关闭
    window = MainWindow(build_registry(), config_repo=repo)
    window.resize(1400, 880)
    window.close()

    # Then: UI 状态写入配置
    state = repo.load_ui_state()
    assert state.window_width == 1400
    assert state.window_height == 880
    assert state.last_tool_id == "sample_tool"

    app.quit()
