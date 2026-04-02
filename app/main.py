"""应用入口。"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.core.app_paths import get_db_path
from app.core.exceptions import install_global_exception_handler
from app.core.logging_config import configure_logging, get_logger
from app.storage import ConfigRepository, Database
from app.tools.registry import ToolRegistry
from app.tools.sample_tool import SampleTool
from app.ui.main_window import MainWindow

LOGGER = get_logger(__name__)


def build_registry() -> ToolRegistry:
    """构建默认工具注册表。"""
    registry = ToolRegistry()
    registry.register(SampleTool())
    return registry


def run() -> int:
    """启动应用。"""
    configure_logging()
    install_global_exception_handler()

    database = Database(get_db_path())
    database.initialize()
    config_repo = ConfigRepository(database)

    app = QApplication(sys.argv)
    window = MainWindow(build_registry(), config_repo=config_repo)
    window.show()

    LOGGER.info("Application started")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
