"""存储层与配置仓储测试。"""

from __future__ import annotations

import pytest

from app.storage import ConfigRepository, Database, UiState
from app.storage.migrations import LATEST_SCHEMA_VERSION


def test_database_initialize_runs_migrations(tmp_path) -> None:
    # Given: 一个新的数据库路径
    db_path = tmp_path / "sftlab.db"
    database = Database(db_path)

    # When: 执行初始化
    database.initialize()

    # Then: schema_version 与核心表创建完成
    with database.connect() as conn:
        row = conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
        assert row is not None
        assert int(row["value"]) == LATEST_SCHEMA_VERSION

        table_names = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "app_config" in table_names
        assert "sft_param_templates" in table_names
        assert "prompt_directories" in table_names


def test_database_initialize_is_idempotent(tmp_path) -> None:
    # Given: 已完成首次初始化的数据库
    database = Database(tmp_path / "sftlab.db")
    database.initialize()

    # When: 再次初始化
    database.initialize()

    # Then: 版本保持不变
    with database.connect() as conn:
        row = conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
        assert row is not None
        assert int(row["value"]) == LATEST_SCHEMA_VERSION


def test_database_future_schema_version_should_raise(tmp_path) -> None:
    # Given: 元数据中写入高于当前代码的 schema 版本
    database = Database(tmp_path / "sftlab.db")
    with database.connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute(
            "INSERT INTO meta(key, value) VALUES('schema_version', '999') "
            "ON CONFLICT(key) DO UPDATE SET value='999'"
        )

    # When / Then: 初始化时应报错，避免降级覆盖
    with pytest.raises(RuntimeError):
        database.initialize()


def test_config_repository_can_save_and_load_ui_state(tmp_path) -> None:
    # Given: 已初始化数据库与配置仓储
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = ConfigRepository(database)

    # When: 保存并读取 UI 状态
    expected = UiState(window_width=1366, window_height=900, last_tool_id="sample_tool")
    repo.save_ui_state(expected)
    loaded = repo.load_ui_state()

    # Then: 配置可正确持久化
    assert loaded == expected


def test_config_repository_get_returns_default(tmp_path) -> None:
    # Given: 空配置
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = ConfigRepository(database)

    # When: 读取不存在的 key
    value = repo.get("missing.key", default="fallback")

    # Then: 返回默认值
    assert value == "fallback"
