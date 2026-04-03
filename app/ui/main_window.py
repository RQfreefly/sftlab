"""主窗口实现。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.storage import ConfigRepository, UiState
from app.tools.base import ToolPlugin
from app.tools.registry import ToolRegistry


class MainWindow(QMainWindow):
    """应用主窗口：左侧工具列表，右侧工作区。"""

    def __init__(
        self,
        registry: ToolRegistry,
        config_repo: ConfigRepository,
    ) -> None:
        super().__init__()
        self._registry = registry
        self._config_repo = config_repo
        self._tool_order: list[ToolPlugin] = []

        self.setWindowTitle("sftlab")
        self._load_ui_state()

        self.sidebar = QListWidget(self)
        self.sidebar.setMinimumWidth(240)

        self.workspace = QStackedWidget(self)

        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.workspace, stretch=1)
        self.setCentralWidget(container)

        self._load_tools()
        self.sidebar.currentRowChanged.connect(self._switch_tool)
        self._select_initial_tool()

    def _load_ui_state(self) -> None:
        """加载窗口状态配置。"""
        state = self._config_repo.load_ui_state()
        self.resize(state.window_width, state.window_height)
        self._initial_tool_id = state.last_tool_id

    def _select_initial_tool(self) -> None:
        """根据配置选择初始工具。"""
        if self.sidebar.count() == 0:
            return

        if self._initial_tool_id:
            for index, tool in enumerate(self._tool_order):
                if tool.metadata.tool_id == self._initial_tool_id:
                    self.sidebar.setCurrentRow(index)
                    return
        self.sidebar.setCurrentRow(0)

    def _load_tools(self) -> None:
        """从注册中心加载工具到 UI。"""
        for plugin in self._registry.all():
            self._append_tool(plugin)

    def _append_tool(self, plugin: ToolPlugin) -> None:
        self._tool_order.append(plugin)
        self.sidebar.addItem(QListWidgetItem(plugin.metadata.name))
        widget = plugin.create_widget(self)
        widget.setProperty("tool_id", plugin.metadata.tool_id)
        self.workspace.addWidget(widget)

    def _switch_tool(self, index: int) -> None:
        if index < 0 or index >= self.workspace.count():
            return
        self.workspace.setCurrentIndex(index)
        current = self._tool_order[index]
        self.statusBar().showMessage(current.metadata.description, 3000)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """保留快捷键入口，M0 先支持 Ctrl+1 快速回到首个工具。"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_1:
            if self.sidebar.count() > 0:
                self.sidebar.setCurrentRow(0)
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802
        """关闭时持久化 UI 配置。"""
        current_index = self.sidebar.currentRow()
        last_tool_id = ""
        if 0 <= current_index < len(self._tool_order):
            last_tool_id = self._tool_order[current_index].metadata.tool_id

        state = UiState(
            window_width=self.width(),
            window_height=self.height(),
            last_tool_id=last_tool_id,
        )
        self._config_repo.save_ui_state(state)
        super().closeEvent(event)
