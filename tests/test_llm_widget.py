"""LLM API 测试控件测试。"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt, QUrl
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.storage import ConfigRepository, Database
from app.tools.llm_api_tester.client import LlmApiResult
from app.tools.llm_api_tester.widget import LlmApiTesterWidget


@dataclass
class FakeClient:
    calls: list[dict[str, Any]]

    def create_chat_completion(
        self,
        base_url: str,
        api_key: str,
        payload: dict[str, Any],
        on_delta: Any = None,
    ) -> LlmApiResult:
        self.calls.append(
            {
                "base_url": base_url,
                "api_key": api_key,
                "payload": payload,
                "has_on_delta": on_delta is not None,
            }
        )
        if on_delta is not None:
            on_delta("o", "")
            on_delta("k", "think")
        return LlmApiResult(content="ok", reasoning="think", raw_json="{}")


def test_llm_widget_uses_current_page_params_when_sending(tmp_path) -> None:
    # Given: 配置仓储 + fake client
    app = QApplication.instance() or QApplication(sys.argv)
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = ConfigRepository(database)
    fake_client = FakeClient(calls=[])

    widget = LlmApiTesterWidget(config_repo=repo, client=fake_client)

    # When: 在页面上修改参数并发送
    widget.base_url_input.setText("https://api.example.com")
    widget.api_key_input.setText("sk-live")
    widget.model_input.setText("deepseek-v3.2")
    widget.temperature_input.setText("")
    widget.top_p_input.setText("0.8")
    widget.max_tokens_input.setText("2048")
    widget.presence_penalty_input.setText("")
    widget.frequency_penalty_input.setText("0.1")
    widget.enable_thinking_checkbox.setChecked(True)
    widget.stream_checkbox.setChecked(False)

    tab = widget.tab_widget.currentWidget()
    assert tab is not None
    tab.user_input.setPlainText("你好")
    tab.send_button.click()

    # Then: 调用参数来自当前页面，空值不进 payload
    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["base_url"] == "https://api.example.com"
    assert call["api_key"] == "sk-live"
    payload = call["payload"]
    assert payload["model"] == "deepseek-v3.2"
    assert payload["top_p"] == 0.8
    assert payload["max_tokens"] == 2048
    assert "temperature" not in payload
    assert "presence_penalty" not in payload
    assert payload["enable_thinking"] is True
    assert "stream" not in payload
    assert call["has_on_delta"] is False

    widget.close()
    app.quit()


def test_llm_widget_passes_stream_callback_and_renders_stream(tmp_path) -> None:
    # Given: 开启 stream 的配置
    app = QApplication.instance() or QApplication(sys.argv)
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = ConfigRepository(database)
    fake_client = FakeClient(calls=[])
    widget = LlmApiTesterWidget(config_repo=repo, client=fake_client)

    widget.base_url_input.setText("https://api.example.com")
    widget.api_key_input.setText("sk-live")
    widget.model_input.setText("deepseek-v3.2")
    widget.stream_checkbox.setChecked(True)

    tab = widget.tab_widget.currentWidget()
    assert tab is not None
    tab.user_input.setPlainText("你好")

    # When: 发送消息
    tab.send_button.click()

    # Then: client 收到 stream 回调，页面显示最终回复
    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["has_on_delta"] is True
    assert call["payload"]["stream"] is True
    plain_text = tab.chat_view.toPlainText()
    assert "Assistant:" in plain_text
    assert "ok" in plain_text

    widget.close()
    app.quit()


def test_llm_widget_enter_key_sends_message(tmp_path) -> None:
    # Given: 初始化控件并填充参数
    app = QApplication.instance() or QApplication(sys.argv)
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = ConfigRepository(database)
    fake_client = FakeClient(calls=[])
    widget = LlmApiTesterWidget(config_repo=repo, client=fake_client)

    widget.base_url_input.setText("https://api.example.com")
    widget.api_key_input.setText("sk-live")
    widget.model_input.setText("deepseek-v3.2")
    tab = widget.tab_widget.currentWidget()
    assert tab is not None
    tab.user_input.setPlainText("回车发送")
    tab.user_input.setFocus()

    # When: 按回车
    QTest.keyClick(tab.user_input, Qt.Key.Key_Return)

    # Then: 等价于点击发送
    assert len(fake_client.calls) == 1
    payload = fake_client.calls[0]["payload"]
    assert payload["messages"][-1] == {"role": "user", "content": "回车发送"}

    widget.close()
    app.quit()


def test_llm_widget_can_toggle_reasoning_after_completed_response(tmp_path) -> None:
    # Given: 一条已完成的 assistant 回复（含思考）
    app = QApplication.instance() or QApplication(sys.argv)
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = ConfigRepository(database)
    fake_client = FakeClient(calls=[])
    widget = LlmApiTesterWidget(config_repo=repo, client=fake_client)

    tab = widget.tab_widget.currentWidget()
    assert tab is not None
    tab.append_user_message("你好")
    tab.append_assistant_message("回答", "这是思考内容")

    collapsed_text = tab.chat_view.toPlainText()
    assert "展开思考内容" in collapsed_text
    assert "这是思考内容" not in collapsed_text

    # When: 点击“展开思考内容”
    tab._on_anchor_clicked(QUrl("action://toggle-reasoning/1"))

    # Then: 思考内容可见
    expanded_text = tab.chat_view.toPlainText()
    assert "收起思考内容" in expanded_text
    assert "这是思考内容" in expanded_text

    widget.close()
    app.quit()
