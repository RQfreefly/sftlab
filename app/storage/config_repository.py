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


@dataclass
class LlmApiSettings:
    """LLM API 测试配置。"""

    base_url: str = "https://api.deepseek.com"
    api_key: str = ""
    model: str = "deepseek-v3.2"
    temperature: str = "0.1"
    top_p: str = "0.9"
    max_tokens: str = "8192"
    presence_penalty: str = "0.2"
    frequency_penalty: str = "0.1"
    enable_thinking: bool = True
    stream: bool = False
    system_prompt: str = "You are a helpful assistant."


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

    def load_llm_api_settings(self) -> LlmApiSettings:
        """读取 LLM API 配置。"""
        return LlmApiSettings(
            base_url=self.get("llm.base_url", "https://api.deepseek.com"),
            api_key=self.get("llm.api_key", ""),
            model=self.get("llm.model", "deepseek-v3.2"),
            temperature=self.get("llm.temperature", "0.1"),
            top_p=self.get("llm.top_p", "0.9"),
            max_tokens=self.get("llm.max_tokens", "8192"),
            presence_penalty=self.get("llm.presence_penalty", "0.2"),
            frequency_penalty=self.get("llm.frequency_penalty", "0.1"),
            enable_thinking=self.get("llm.enable_thinking", "1") == "1",
            stream=self.get("llm.stream", "0") == "1",
            system_prompt=self.get("llm.system_prompt", "You are a helpful assistant."),
        )

    def save_llm_api_settings(self, settings: LlmApiSettings) -> None:
        """保存 LLM API 配置。"""
        self.set("llm.base_url", settings.base_url)
        self.set("llm.api_key", settings.api_key)
        self.set("llm.model", settings.model)
        self.set("llm.temperature", settings.temperature)
        self.set("llm.top_p", settings.top_p)
        self.set("llm.max_tokens", settings.max_tokens)
        self.set("llm.presence_penalty", settings.presence_penalty)
        self.set("llm.frequency_penalty", settings.frequency_penalty)
        self.set("llm.enable_thinking", "1" if settings.enable_thinking else "0")
        self.set("llm.stream", "1" if settings.stream else "0")
        self.set("llm.system_prompt", settings.system_prompt)
