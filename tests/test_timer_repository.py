"""分段计时仓储测试。"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.storage import Database, TimerRepository


def test_timer_repository_session_and_segments(tmp_path) -> None:
    # Given: 初始化仓储
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = TimerRepository(database)

    # When: 创建会话并追加分段
    session = repo.create_session("训练任务", started_at=datetime(2026, 1, 1, 10, 0, 0))
    repo.add_segment(
        session_id=session.id,
        started_at=datetime(2026, 1, 1, 10, 0, 0),
        ended_at=datetime(2026, 1, 1, 10, 0, 30),
        duration_seconds=30,
    )
    repo.finish_session(
        session_id=session.id,
        ended_at=datetime(2026, 1, 1, 10, 1, 0),
        total_seconds=30,
    )

    # Then: 会话与分段可读
    loaded = repo.get_session(session.id)
    segments = repo.list_segments(session.id)
    assert loaded is not None
    assert loaded.total_seconds == 30
    assert loaded.ended_at is not None
    assert len(segments) == 1
    assert segments[0].duration_seconds == 30


def test_timer_repository_list_sessions_order(tmp_path) -> None:
    # Given: 连续创建会话
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = TimerRepository(database)

    s1 = repo.create_session("A", started_at=datetime.now() - timedelta(minutes=2))
    s2 = repo.create_session("B", started_at=datetime.now() - timedelta(minutes=1))

    # When: 列出会话
    sessions = repo.list_sessions(limit=10)

    # Then: 最新会话在前
    assert sessions[0].id == s2.id
    assert sessions[1].id == s1.id
