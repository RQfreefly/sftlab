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

from app.tools.base import ToolPlugin
from app.tools.registry import ToolRegistry


class MainWindow(QMainWindow):
    """应用主窗口：左侧工具列表，右侧工作区。"""

    def __init__(self, registry: ToolRegistry) -> None:
        super().__init__()
        self._registry = registry
        self._tool_order: list[ToolPlugin] = []

        self.setWindowTitle("SFT 工具集")
        self.resize(1200, 760)

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
        if self.sidebar.count() > 0:
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
