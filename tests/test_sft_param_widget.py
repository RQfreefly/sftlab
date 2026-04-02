"""SFT 参数管理控件测试。"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.storage import Database, SftParamTemplateRepository
from app.tools.sft_params.widget import SftParamManagerWidget


SAMPLE_CLI = "swift sft --model /ssd/model --learning_rate 1e-4"
UPDATED_CLI = "swift sft --model /ssd/model2 --learning_rate 5e-5"


def test_select_version_should_preview_and_restore(tmp_path) -> None:
    # Given: 一个包含 v1/v2 的模板
    app = QApplication.instance() or QApplication(sys.argv)
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = SftParamTemplateRepository(database)
    created = repo.create_template(name="baseline", cli_text=SAMPLE_CLI)
    repo.update_template(created.id, name="baseline", cli_text=UPDATED_CLI)

    widget = SftParamManagerWidget(repository=repo)
    widget.template_list.setCurrentRow(0)

    # When: 选择 v1（索引 1）进行预览
    widget.version_list.setCurrentRow(1)

    # Then: 预览区显示 v1，编辑区仍保持当前版本 v2
    assert widget.version_preview.toPlainText() == SAMPLE_CLI
    assert widget.cli_editor.toPlainText() == UPDATED_CLI

    # When: 点击恢复所选版本
    widget.restore_button.click()

    # Then: 编辑区切换为 v1
    assert widget.cli_editor.toPlainText() == SAMPLE_CLI

    widget.close()
    app.quit()
