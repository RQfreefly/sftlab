"""分段计时器页面。"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.storage import TimerRepository


class SegmentTimerWidget(QWidget):
    """支持 start/pause/stop 的分段计时器。"""

    def __init__(self, repository: TimerRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._repository = repository

        self._current_session_id: int | None = None
        self._segment_started_at: datetime | None = None
        self._base_elapsed_seconds = 0

        self._tick = QTimer(self)
        self._tick.setInterval(500)
        self._tick.timeout.connect(self._update_elapsed_label)

        self._build_ui()
        self._bind_events()
        self._refresh_history()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.task_input = QLineEdit(self)
        self.task_input.setPlaceholderText("任务名称（可选）")
        layout.addWidget(self.task_input)

        stats_row = QHBoxLayout()
        self.elapsed_label = QLabel("00:00:00", self)
        self.segment_label = QLabel("分段数：0", self)
        stats_row.addWidget(QLabel("总时长", self))
        stats_row.addWidget(self.elapsed_label)
        stats_row.addStretch(1)
        stats_row.addWidget(self.segment_label)
        layout.addLayout(stats_row)

        button_row = QHBoxLayout()
        self.start_button = QPushButton("Start", self)
        self.pause_button = QPushButton("Pause", self)
        self.stop_button = QPushButton("Stop", self)
        self.refresh_button = QPushButton("刷新历史", self)
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.pause_button)
        button_row.addWidget(self.stop_button)
        button_row.addWidget(self.refresh_button)
        layout.addLayout(button_row)

        self.history_list = QListWidget(self)
        layout.addWidget(self.history_list, stretch=1)

        self.status_label = QLabel("就绪", self)
        layout.addWidget(self.status_label)

    def _bind_events(self) -> None:
        self.start_button.clicked.connect(self._start)
        self.pause_button.clicked.connect(self._pause)
        self.stop_button.clicked.connect(self._stop)
        self.refresh_button.clicked.connect(self._refresh_history)

    def _start(self) -> None:
        if self._segment_started_at is not None:
            self.status_label.setText("计时进行中")
            return

        if self._current_session_id is None:
            session = self._repository.create_session(self.task_input.text())
            self._current_session_id = session.id
            self._base_elapsed_seconds = 0
            self.segment_label.setText("分段数：0")
            self.status_label.setText(f"已开始：会话 {session.id}")
        else:
            self.status_label.setText(f"已恢复：会话 {self._current_session_id}")

        self._segment_started_at = datetime.now()
        self._tick.start()

    def _pause(self) -> None:
        if self._current_session_id is None or self._segment_started_at is None:
            self.status_label.setText("当前未运行")
            return

        start_time = self._segment_started_at
        end_time = datetime.now()
        duration = max(0, int((end_time - start_time).total_seconds()))

        self._repository.add_segment(
            session_id=self._current_session_id,
            started_at=start_time,
            ended_at=end_time,
            duration_seconds=duration,
        )

        self._base_elapsed_seconds += duration
        self._segment_started_at = None
        self._tick.stop()
        self._refresh_segment_count()
        self._update_elapsed_label()
        self.status_label.setText("已暂停")

    def _stop(self) -> None:
        if self._current_session_id is None:
            self.status_label.setText("暂无会话")
            return

        if self._segment_started_at is not None:
            self._pause()

        session_id = self._current_session_id
        self._repository.finish_session(
            session_id=session_id,
            ended_at=datetime.now(),
            total_seconds=self._base_elapsed_seconds,
        )

        self._current_session_id = None
        self._segment_started_at = None
        self._base_elapsed_seconds = 0
        self._tick.stop()
        self.elapsed_label.setText("00:00:00")
        self.segment_label.setText("分段数：0")
        self._refresh_history()
        self.status_label.setText(f"已停止并保存：会话 {session_id}")

    def _refresh_segment_count(self) -> None:
        if self._current_session_id is None:
            self.segment_label.setText("分段数：0")
            return

        segments = self._repository.list_segments(self._current_session_id)
        self.segment_label.setText(f"分段数：{len(segments)}")

    def _refresh_history(self) -> None:
        sessions = self._repository.list_sessions(limit=50)
        self.history_list.clear()

        for session in sessions:
            ended = session.ended_at if session.ended_at is not None else "running"
            label = (
                f"#{session.id} | {session.task_name or '未命名'} | "
                f"{self._format_hms(session.total_seconds)} | {ended}"
            )
            self.history_list.addItem(QListWidgetItem(label))

    def _update_elapsed_label(self) -> None:
        elapsed = self._base_elapsed_seconds
        if self._segment_started_at is not None:
            elapsed += max(0, int((datetime.now() - self._segment_started_at).total_seconds()))
        self.elapsed_label.setText(self._format_hms(elapsed))

    def _format_hms(self, seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
