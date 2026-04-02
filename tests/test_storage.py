"""存储层与配置仓储测试。"""

from __future__ import annotations

import pytest

from app.storage import ConfigRepository, Database, LlmApiSettings, UiState
from app.storage.migrations import LATEST_SCHEMA_VERSION, migrate_to_v1


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
        assert "sft_param_template_versions" in table_names
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


def test_database_upgrade_from_v1_should_backfill_template_versions(tmp_path) -> None:
    # Given: 一个停留在 v1 的数据库，且已有参数模板数据
    database = Database(tmp_path / "sftlab.db")
    with database.connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        migrate_to_v1(conn)
        conn.execute(
            """
            INSERT INTO sft_param_templates(name, cli_text)
            VALUES('legacy-template', 'swift sft --model /ssd/legacy')
            """
        )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES('schema_version', '1') "
            "ON CONFLICT(key) DO UPDATE SET value='1'"
        )

    # When: 调用 initialize 执行升级迁移
    database.initialize()

    # Then: 旧模板应自动补一条版本记录
    with database.connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM sft_param_template_versions WHERE template_id = 1"
        ).fetchone()
        assert row is not None
        assert int(row["cnt"]) == 1


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


def test_config_repository_can_save_and_load_llm_api_settings(tmp_path) -> None:
    # Given: 已初始化数据库与配置仓储
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = ConfigRepository(database)

    expected = LlmApiSettings(
        base_url="https://api.example.com",
        api_key="sk-test",
        model="deepseek-v3.2",
        temperature="0.2",
        top_p="0.8",
        max_tokens="4096",
        presence_penalty="0.1",
        frequency_penalty="0.1",
        enable_thinking=False,
        stream=False,
        system_prompt="You are a helpful assistant.",
    )

    # When: 保存并读取 LLM 参数
    repo.save_llm_api_settings(expected)
    loaded = repo.load_llm_api_settings()

    # Then: 参数可正确持久化
    assert loaded == expected
