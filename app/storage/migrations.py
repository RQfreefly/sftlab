"""SQLite 迁移定义。"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

Migration = Callable[[sqlite3.Connection], None]


def migrate_to_v1(conn: sqlite3.Connection) -> None:
    """初始化 V1 schema。"""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS app_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sft_param_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            cli_text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS prompt_directories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, parent_id),
            FOREIGN KEY(parent_id) REFERENCES prompt_directories(id)
        );

        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            directory_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(directory_id) REFERENCES prompt_directories(id)
        );

        CREATE TABLE IF NOT EXISTS prompt_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id INTEGER NOT NULL,
            version_no INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(prompt_id, version_no),
            FOREIGN KEY(prompt_id) REFERENCES prompts(id)
        );

        CREATE TABLE IF NOT EXISTS timer_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            total_seconds INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS timer_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            duration_seconds INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(session_id) REFERENCES timer_sessions(id)
        );
        """
    )


def migrate_to_v2(conn: sqlite3.Connection) -> None:
    """新增参数模板版本历史表。"""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sft_param_template_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            version_no INTEGER NOT NULL,
            cli_text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(template_id, version_no),
            FOREIGN KEY(template_id) REFERENCES sft_param_templates(id)
        );

        INSERT INTO sft_param_template_versions(template_id, version_no, cli_text)
        SELECT t.id, 1, t.cli_text
        FROM sft_param_templates t
        WHERE NOT EXISTS (
            SELECT 1
            FROM sft_param_template_versions v
            WHERE v.template_id = t.id
        );
        """
    )


MIGRATIONS: dict[int, Migration] = {
    1: migrate_to_v1,
    2: migrate_to_v2,
}

LATEST_SCHEMA_VERSION = max(MIGRATIONS)
