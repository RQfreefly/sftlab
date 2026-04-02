"""分段计时器仓储。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.storage.database import Database


@dataclass(frozen=True)
class TimerSession:
    """计时任务会话。"""

    id: int
    task_name: str
    started_at: str
    ended_at: str | None
    total_seconds: int


@dataclass(frozen=True)
class TimerSegment:
    """计时分段记录。"""

    id: int
    session_id: int
    started_at: str
    ended_at: str | None
    duration_seconds: int


class TimerRepository:
    """管理计时会话与分段。"""

    def __init__(self, database: Database) -> None:
        self._database = database

    def create_session(self, task_name: str, started_at: datetime | None = None) -> TimerSession:
        """创建计时会话。"""
        start = (started_at or datetime.now()).isoformat(timespec="seconds")
        name = task_name.strip()

        with self._database.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO timer_sessions(task_name, started_at)
                VALUES(?, ?)
                """,
                (name, start),
            )
            session_id = int(cursor.lastrowid)

        loaded = self.get_session(session_id)
        if loaded is None:
            raise RuntimeError("Session created but cannot be loaded")
        return loaded

    def get_session(self, session_id: int) -> TimerSession | None:
        """按 id 获取会话。"""
        with self._database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, task_name, started_at, ended_at, total_seconds
                FROM timer_sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return TimerSession(
            id=int(row["id"]),
            task_name=str(row["task_name"] or ""),
            started_at=str(row["started_at"]),
            ended_at=str(row["ended_at"]) if row["ended_at"] is not None else None,
            total_seconds=int(row["total_seconds"]),
        )

    def list_sessions(self, limit: int = 30) -> list[TimerSession]:
        """按时间倒序列出最近会话。"""
        with self._database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, task_name, started_at, ended_at, total_seconds
                FROM timer_sessions
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            TimerSession(
                id=int(row["id"]),
                task_name=str(row["task_name"] or ""),
                started_at=str(row["started_at"]),
                ended_at=str(row["ended_at"]) if row["ended_at"] is not None else None,
                total_seconds=int(row["total_seconds"]),
            )
            for row in rows
        ]

    def add_segment(
        self,
        session_id: int,
        started_at: datetime,
        ended_at: datetime,
        duration_seconds: int,
    ) -> TimerSegment:
        """追加一个已结束分段。"""
        if duration_seconds < 0:
            raise ValueError("duration_seconds must be >= 0")

        self._ensure_session_exists(session_id)

        start_text = started_at.isoformat(timespec="seconds")
        end_text = ended_at.isoformat(timespec="seconds")

        with self._database.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO timer_segments(session_id, started_at, ended_at, duration_seconds)
                VALUES(?, ?, ?, ?)
                """,
                (session_id, start_text, end_text, duration_seconds),
            )
            segment_id = int(cursor.lastrowid)

        loaded = self.get_segment(segment_id)
        if loaded is None:
            raise RuntimeError("Segment created but cannot be loaded")
        return loaded

    def get_segment(self, segment_id: int) -> TimerSegment | None:
        """按 id 获取分段。"""
        with self._database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, session_id, started_at, ended_at, duration_seconds
                FROM timer_segments
                WHERE id = ?
                """,
                (segment_id,),
            ).fetchone()
        if row is None:
            return None

        return TimerSegment(
            id=int(row["id"]),
            session_id=int(row["session_id"]),
            started_at=str(row["started_at"]),
            ended_at=str(row["ended_at"]) if row["ended_at"] is not None else None,
            duration_seconds=int(row["duration_seconds"]),
        )

    def list_segments(self, session_id: int) -> list[TimerSegment]:
        """列出某会话的所有分段。"""
        with self._database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, session_id, started_at, ended_at, duration_seconds
                FROM timer_segments
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

        return [
            TimerSegment(
                id=int(row["id"]),
                session_id=int(row["session_id"]),
                started_at=str(row["started_at"]),
                ended_at=str(row["ended_at"]) if row["ended_at"] is not None else None,
                duration_seconds=int(row["duration_seconds"]),
            )
            for row in rows
        ]

    def finish_session(
        self,
        session_id: int,
        ended_at: datetime | None,
        total_seconds: int,
    ) -> TimerSession:
        """结束会话并写入总时长。"""
        if total_seconds < 0:
            raise ValueError("total_seconds must be >= 0")

        self._ensure_session_exists(session_id)
        end_text = ended_at.isoformat(timespec="seconds") if ended_at is not None else None

        with self._database.connect() as conn:
            conn.execute(
                """
                UPDATE timer_sessions
                SET ended_at = ?, total_seconds = ?
                WHERE id = ?
                """,
                (end_text, total_seconds, session_id),
            )

        loaded = self.get_session(session_id)
        if loaded is None:
            raise RuntimeError("Session updated but cannot be loaded")
        return loaded

    def _ensure_session_exists(self, session_id: int) -> None:
        with self._database.connect() as conn:
            row = conn.execute("SELECT id FROM timer_sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            raise KeyError(f"Session not found: {session_id}")
