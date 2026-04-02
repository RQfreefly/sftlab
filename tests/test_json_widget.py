"""JSON 工具控件测试。"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.tools.json_tool.widget import JsonToolWidget


def test_json_widget_builds_tree_for_valid_json() -> None:
    # Given: JSON 工具控件
    app = QApplication.instance() or QApplication(sys.argv)
    widget = JsonToolWidget()

    # When: 输入合法 JSON
    widget.text_editor.setPlainText('{"name":"alice","tags":["a","b"]}')

    # Then: 树结构生成
    assert widget.tree.topLevelItemCount() == 1
    assert widget.status_label.text() == "JSON 解析成功"

    widget.close()
    app.quit()


def test_json_widget_shows_full_value_in_preview() -> None:
    # Given: JSON 工具控件和长文本值
    app = QApplication.instance() or QApplication(sys.argv)
    widget = JsonToolWidget()
    widget.text_editor.setPlainText(
        '{"desc":"line1\\nline2\\nline3","meta":{"a":1,"b":2}}'
    )

    # When: 选择 desc 节点
    root = widget.tree.topLevelItem(0)
    desc_item = root.child(0)
    widget.tree.setCurrentItem(desc_item)

    # Then: 预览区应展示完整多行内容
    assert widget.value_preview.toPlainText() == "line1\nline2\nline3"

    # When: 选择对象节点
    meta_item = root.child(1)
    widget.tree.setCurrentItem(meta_item)

    # Then: 预览区展示完整 JSON 对象
    preview = widget.value_preview.toPlainText()
    assert '"a": 1' in preview
    assert '"b": 2' in preview

    widget.close()
    app.quit()
