"""SQLite 数据库管理。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.storage.migrations import LATEST_SCHEMA_VERSION, MIGRATIONS


class Database:
    """数据库连接与迁移入口。"""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    @property
    def path(self) -> Path:
        return self._db_path

    def connect(self) -> sqlite3.Connection:
        """创建数据库连接。"""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        """初始化数据库并执行迁移。"""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        with self.connect() as conn:
            self._ensure_meta_table(conn)
            current_version = self._get_schema_version(conn)
            target_version = LATEST_SCHEMA_VERSION

            if current_version > target_version:
                raise RuntimeError(
                    f"Unsupported schema version: {current_version}, latest={target_version}"
                )

            for version in range(current_version + 1, target_version + 1):
                migration = MIGRATIONS[version]
                migration(conn)
                self._set_schema_version(conn, version)

    def _ensure_meta_table(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

    def _get_schema_version(self, conn: sqlite3.Connection) -> int:
        row = conn.execute(
            "SELECT value FROM meta WHERE key = ?",
            ("schema_version",),
        ).fetchone()
        if row is None:
            return 0
        return int(row["value"])

    def _set_schema_version(self, conn: sqlite3.Connection, version: int) -> None:
        conn.execute(
            """
            INSERT INTO meta(key, value)
            VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            ("schema_version", str(version)),
        )
