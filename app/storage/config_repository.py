"""应用配置仓储。"""

from __future__ import annotations

from dataclasses import dataclass

from app.storage.database import Database


@dataclass
class UiState:
    """UI 相关配置。"""

    window_width: int = 1200
    window_height: int = 760
    last_tool_id: str = ""


class ConfigRepository:
    """管理 app_config 表中的键值配置。"""

    def __init__(self, database: Database) -> None:
        self._database = database

    def set(self, key: str, value: str) -> None:
        with self._database.connect() as conn:
            conn.execute(
                """
                INSERT INTO app_config(key, value)
                VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, value),
            )

    def get(self, key: str, default: str = "") -> str:
        with self._database.connect() as conn:
            row = conn.execute(
                "SELECT value FROM app_config WHERE key = ?",
                (key,),
            ).fetchone()
            if row is None:
                return default
            return str(row["value"])

    def load_ui_state(self) -> UiState:
        """读取 UI 配置，不存在时返回默认值。"""
        width = int(self.get("ui.window_width", "1200"))
        height = int(self.get("ui.window_height", "760"))
        last_tool_id = self.get("ui.last_tool_id", "")
        return UiState(window_width=width, window_height=height, last_tool_id=last_tool_id)

    def save_ui_state(self, state: UiState) -> None:
        """保存 UI 配置。"""
        self.set("ui.window_width", str(state.window_width))
        self.set("ui.window_height", str(state.window_height))
        self.set("ui.last_tool_id", state.last_tool_id)
