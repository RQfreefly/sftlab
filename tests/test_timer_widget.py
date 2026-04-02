"""分段计时控件测试。"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.storage import Database, TimerRepository
from app.tools.segment_timer.widget import SegmentTimerWidget


def test_timer_widget_start_pause_stop(tmp_path) -> None:
    # Given: 计时器控件
    app = QApplication.instance() or QApplication(sys.argv)
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = TimerRepository(database)
    widget = SegmentTimerWidget(repository=repo)

    # When: 启动并模拟运行 2 秒后暂停
    widget.task_input.setText("测试任务")
    widget.start_button.click()
    assert widget._current_session_id is not None

    widget._segment_started_at = datetime.now() - timedelta(seconds=2)
    widget.pause_button.click()

    # Then: 分段数应更新
    assert "分段数：1" == widget.segment_label.text()

    # When: 停止
    session_id = widget._current_session_id
    widget.stop_button.click()

    # Then: 会话落库且已结束
    assert session_id is not None
    session = repo.get_session(session_id)
    assert session is not None
    assert session.ended_at is not None
    assert session.total_seconds >= 2

    widget.close()
    app.quit()
