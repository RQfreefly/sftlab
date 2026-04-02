"""LLM API 测试页面。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QKeyEvent, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.storage import ConfigRepository, LlmApiSettings
from app.tools.llm_api_tester.client import LlmApiClient, LlmApiError


class EnterSendPlainTextEdit(QPlainTextEdit):
    """回车发送输入框（Shift+Enter 换行）。"""

    send_pressed = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        is_enter = key in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        if is_enter and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.send_pressed.emit()
            event.accept()
            return
        super().keyPressEvent(event)


@dataclass
class ChatTabState:
    """会话页状态。"""

    messages: list[dict[str, Any]] = field(default_factory=list)
    expanded_reasoning_indices: set[int] = field(default_factory=set)


class ChatTabWidget(QWidget):
    """单个会话 Tab。"""

    send_requested = Signal(object, str)

    def __init__(self, tab_title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = ChatTabState()
        self._title = tab_title
        self._streaming_content = ""
        self._streaming_reasoning = ""
        self._streaming_reasoning_expanded = False
        self._build_ui()
        self._bind_events()

    @property
    def title(self) -> str:
        return self._title

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.chat_view = QTextBrowser(self)
        self.chat_view.setReadOnly(True)
        self.chat_view.setPlaceholderText("会话内容")
        self.chat_view.setOpenLinks(False)
        self.chat_view.setOpenExternalLinks(False)
        self.chat_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_view.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)
        self.chat_view.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(self.chat_view, stretch=1)

        self.user_input = EnterSendPlainTextEdit(self)
        self.user_input.setPlaceholderText("输入用户消息")
        self.user_input.setFixedHeight(90)
        layout.addWidget(self.user_input)

        row = QHBoxLayout()
        self.send_button = QPushButton("发送", self)
        self.clear_button = QPushButton("清空会话", self)
        row.addWidget(self.send_button)
        row.addWidget(self.clear_button)
        row.addStretch(1)
        layout.addLayout(row)

    def _bind_events(self) -> None:
        self.send_button.clicked.connect(self._emit_send)
        self.user_input.send_pressed.connect(self._emit_send)
        self.clear_button.clicked.connect(self.clear_conversation)
        self.chat_view.anchorClicked.connect(self._on_anchor_clicked)

    def _emit_send(self) -> None:
        text = self.user_input.toPlainText().strip()
        if not text:
            return
        self.send_requested.emit(self, text)

    def clear_conversation(self) -> None:
        self.state.messages.clear()
        self.state.expanded_reasoning_indices.clear()
        self._streaming_content = ""
        self._streaming_reasoning = ""
        self._streaming_reasoning_expanded = False
        self._render_chat()

    def append_user_message(self, content: str) -> None:
        self.state.messages.append({"role": "user", "content": content})
        self._render_chat()

    def append_assistant_message(self, content: str, reasoning: str) -> None:
        self.state.messages.append({"role": "assistant", "content": content, "reasoning": reasoning})
        self._streaming_content = ""
        self._streaming_reasoning = ""
        self._streaming_reasoning_expanded = False
        self._render_chat()

    def begin_assistant_stream(self) -> None:
        self._streaming_content = ""
        self._streaming_reasoning = ""
        self._streaming_reasoning_expanded = True
        self._render_chat()

    def append_assistant_stream_delta(self, content_delta: str, reasoning_delta: str) -> None:
        if not content_delta and not reasoning_delta:
            return
        self._streaming_content += content_delta
        self._streaming_reasoning += reasoning_delta
        self._render_chat()

    def cancel_assistant_stream(self) -> None:
        self._streaming_content = ""
        self._streaming_reasoning = ""
        self._streaming_reasoning_expanded = False
        self._render_chat()

    def pop_last_user_message(self) -> None:
        if not self.state.messages:
            return
        if self.state.messages[-1].get("role") == "user":
            self.state.messages.pop()
        self._render_chat()

    def reset_input(self) -> None:
        self.user_input.clear()

    def build_messages(self, system_prompt: str) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})

        for message in self.state.messages:
            role = str(message.get("role", ""))
            content = str(message.get("content", ""))
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

        return messages

    def _escape_html(self, text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def _render_chat(self, *, scroll_to_end: bool = True, focus_anchor: str | None = None) -> None:
        blocks: list[str] = []
        for index, message in enumerate(self.state.messages):
            role = str(message.get("role", ""))
            content = self._escape_html(str(message.get("content", "")))
            if role == "user":
                blocks.append(
                    "<div><b>User:</b></div>"
                    f"<div style='white-space: pre-wrap; word-break: break-word;'>{content}</div>"
                )
                continue
            if role == "assistant":
                message_blocks = ["<div><b>Assistant:</b></div>"]
                reasoning = str(message.get("reasoning", "")).strip()
                if reasoning:
                    expanded = index in self.state.expanded_reasoning_indices
                    toggle_text = "收起思考内容" if expanded else "展开思考内容"
                    message_blocks.append(
                        f"<div><a href='action://toggle-reasoning/{index}'>{toggle_text}</a></div>"
                    )
                    if expanded:
                        message_blocks.append(
                            f"<a name='reasoning-{index}'></a>"
                            "<div style='white-space: pre-wrap; word-break: break-word; "
                            "background:#f5f5f5; border:1px solid #d9d9d9; padding:8px; margin:4px 0;'>"
                            f"{self._escape_html(reasoning)}"
                            "</div>"
                        )
                message_blocks.append(
                    f"<div style='white-space: pre-wrap; word-break: break-word;'>{content}</div>"
                )
                blocks.append("<br/>".join(message_blocks))

        if self._streaming_content or self._streaming_reasoning:
            stream_blocks = ["<div><b>Assistant:</b></div>"]
            if self._streaming_reasoning:
                toggle_text = "收起思考内容" if self._streaming_reasoning_expanded else "展开思考内容"
                stream_blocks.append(
                    f"<div><a href='action://toggle-reasoning/stream'>{toggle_text}</a></div>"
                )
                if self._streaming_reasoning_expanded:
                    stream_blocks.append(
                        "<div style='white-space: pre-wrap; word-break: break-word; "
                        "background:#f5f5f5; border:1px solid #d9d9d9; padding:8px; margin:4px 0;'>"
                        f"{self._escape_html(self._streaming_reasoning)}"
                        "</div>"
                    )
            stream_blocks.append(
                "<div style='white-space: pre-wrap; word-break: break-word;'>"
                f"{self._escape_html(self._streaming_content)}"
                "</div>"
            )
            blocks.append("<br/>".join(stream_blocks))

        self.chat_view.setHtml("<br/><br/>".join(blocks))
        if focus_anchor:
            self.chat_view.scrollToAnchor(focus_anchor)
            return
        if scroll_to_end:
            cursor = self.chat_view.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.chat_view.setTextCursor(cursor)

    def _on_anchor_clicked(self, url: Any) -> None:
        if not isinstance(url, QUrl):
            return

        if url.scheme() != "action" or url.host() != "toggle-reasoning":
            return

        target = url.path().lstrip("/")
        if target == "stream":
            self._streaming_reasoning_expanded = not self._streaming_reasoning_expanded
            self._render_chat(scroll_to_end=False)
            return

        try:
            index = int(target)
        except ValueError:
            return

        if index in self.state.expanded_reasoning_indices:
            self.state.expanded_reasoning_indices.remove(index)
            self._render_chat(scroll_to_end=False)
        else:
            self.state.expanded_reasoning_indices.add(index)
            self._render_chat(scroll_to_end=False, focus_anchor=f"reasoning-{index}")


class LlmApiTesterWidget(QWidget):
    """LLM API 测试工具。"""

    def __init__(
        self,
        config_repo: ConfigRepository,
        client: LlmApiClient | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config_repo = config_repo
        self._client = client or LlmApiClient()
        self._sending = False
        self._tab_counter = 0

        self._build_ui()
        self._bind_events()
        self._load_settings()
        self._add_tab()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        splitter = QSplitter(self)
        root.addWidget(splitter, stretch=1)

        left_panel = QWidget(splitter)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        cfg_group = QGroupBox("接口参数", left_panel)
        cfg_layout = QFormLayout(cfg_group)

        self.base_url_input = QLineEdit(cfg_group)
        self.api_key_input = QLineEdit(cfg_group)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.model_input = QLineEdit(cfg_group)
        self.system_prompt_input = QLineEdit(cfg_group)

        self.temperature_input = QLineEdit(cfg_group)
        self.top_p_input = QLineEdit(cfg_group)
        self.max_tokens_input = QLineEdit(cfg_group)
        self.presence_penalty_input = QLineEdit(cfg_group)
        self.frequency_penalty_input = QLineEdit(cfg_group)

        self.enable_thinking_checkbox = QCheckBox("enable_thinking", cfg_group)
        self.stream_checkbox = QCheckBox("stream", cfg_group)

        cfg_layout.addRow("Base URL", self.base_url_input)
        cfg_layout.addRow("API Key", self.api_key_input)
        cfg_layout.addRow("Model", self.model_input)
        cfg_layout.addRow("System Prompt", self.system_prompt_input)
        cfg_layout.addRow("temperature", self.temperature_input)
        cfg_layout.addRow("top_p", self.top_p_input)
        cfg_layout.addRow("max_tokens", self.max_tokens_input)
        cfg_layout.addRow("presence_penalty", self.presence_penalty_input)
        cfg_layout.addRow("frequency_penalty", self.frequency_penalty_input)

        option_row = QHBoxLayout()
        option_row.addWidget(self.enable_thinking_checkbox)
        option_row.addWidget(self.stream_checkbox)
        option_row.addStretch(1)
        cfg_layout.addRow("选项", option_row)

        self.save_settings_button = QPushButton("保存参数", cfg_group)
        cfg_layout.addRow("", self.save_settings_button)

        left_layout.addWidget(cfg_group, stretch=1)

        right_panel = QWidget(splitter)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        tab_row = QHBoxLayout()
        self.add_tab_button = QPushButton("新建Tab", right_panel)
        self.remove_tab_button = QPushButton("关闭当前Tab", right_panel)
        tab_row.addWidget(self.add_tab_button)
        tab_row.addWidget(self.remove_tab_button)
        tab_row.addStretch(1)
        right_layout.addLayout(tab_row)

        self.tab_widget = QTabWidget(right_panel)
        right_layout.addWidget(self.tab_widget, stretch=1)

        splitter.setSizes([420, 980])

        self.status_label = QLabel("就绪", self)
        root.addWidget(self.status_label)

    def _bind_events(self) -> None:
        self.add_tab_button.clicked.connect(self._add_tab)
        self.remove_tab_button.clicked.connect(self._remove_current_tab)
        self.save_settings_button.clicked.connect(self._save_settings)

    def _load_settings(self) -> None:
        settings = self._config_repo.load_llm_api_settings()
        self.base_url_input.setText(settings.base_url)
        self.api_key_input.setText(settings.api_key)
        self.model_input.setText(settings.model)
        self.system_prompt_input.setText(settings.system_prompt)

        self.temperature_input.setText(settings.temperature)
        self.top_p_input.setText(settings.top_p)
        self.max_tokens_input.setText(settings.max_tokens)
        self.presence_penalty_input.setText(settings.presence_penalty)
        self.frequency_penalty_input.setText(settings.frequency_penalty)

        self.enable_thinking_checkbox.setChecked(settings.enable_thinking)
        self.stream_checkbox.setChecked(settings.stream)

    def _save_settings(self) -> None:
        settings = LlmApiSettings(
            base_url=self.base_url_input.text().strip(),
            api_key=self.api_key_input.text().strip(),
            model=self.model_input.text().strip(),
            temperature=self.temperature_input.text().strip(),
            top_p=self.top_p_input.text().strip(),
            max_tokens=self.max_tokens_input.text().strip(),
            presence_penalty=self.presence_penalty_input.text().strip(),
            frequency_penalty=self.frequency_penalty_input.text().strip(),
            enable_thinking=self.enable_thinking_checkbox.isChecked(),
            stream=self.stream_checkbox.isChecked(),
            system_prompt=self.system_prompt_input.text(),
        )
        self._config_repo.save_llm_api_settings(settings)
        self.status_label.setText("参数已保存")

    def _add_tab(self) -> None:
        self._tab_counter += 1
        tab = ChatTabWidget(tab_title=f"会话 {self._tab_counter}", parent=self.tab_widget)
        tab.send_requested.connect(self._send_message)
        index = self.tab_widget.addTab(tab, tab.title)
        self.tab_widget.setCurrentIndex(index)

    def _remove_current_tab(self) -> None:
        if self.tab_widget.count() <= 1:
            self.status_label.setText("至少保留一个 Tab")
            return

        index = self.tab_widget.currentIndex()
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        if widget is not None:
            widget.deleteLater()

    def _send_message(self, tab: ChatTabWidget, user_text: str) -> None:
        if self._sending:
            self.status_label.setText("请求进行中，请稍候")
            return

        try:
            payload = self._build_payload(tab, user_text)
        except ValueError as exc:
            self.status_label.setText(f"参数错误：{exc}")
            return

        tab.append_user_message(user_text)
        tab.reset_input()

        use_stream = bool(payload.get("stream"))
        if use_stream:
            tab.begin_assistant_stream()

        self._save_settings()
        self._sending = True
        self.status_label.setText("请求中...")

        try:
            result = self._client.create_chat_completion(
                base_url=self.base_url_input.text().strip(),
                api_key=self.api_key_input.text().strip(),
                payload=payload,
                on_delta=self._build_stream_callback(tab) if use_stream else None,
            )
        except LlmApiError as exc:
            if use_stream:
                tab.cancel_assistant_stream()
            tab.pop_last_user_message()
            self.status_label.setText(f"请求失败：{exc}")
            QMessageBox.warning(self, "请求失败", str(exc))
            return
        finally:
            self._sending = False

        if use_stream:
            tab.cancel_assistant_stream()
        tab.append_assistant_message(result.content, result.reasoning)
        self.status_label.setText("请求成功")

    def _build_stream_callback(self, tab: ChatTabWidget) -> Callable[[str, str], None]:
        def callback(content_delta: str, reasoning_delta: str) -> None:
            tab.append_assistant_stream_delta(content_delta, reasoning_delta)
            QApplication.processEvents()

        return callback

    def _build_payload(self, tab: ChatTabWidget, user_text: str) -> dict[str, Any]:
        model = self.model_input.text().strip()
        if not model:
            raise ValueError("model 不能为空")

        base_url = self.base_url_input.text().strip()
        if not base_url:
            raise ValueError("Base URL 不能为空")

        api_key = self.api_key_input.text().strip()
        if not api_key:
            raise ValueError("API Key 不能为空")

        payload: dict[str, Any] = {
            "model": model,
            "messages": tab.build_messages(self.system_prompt_input.text())
            + [{"role": "user", "content": user_text}],
        }

        self._assign_optional_float(payload, "temperature", self.temperature_input.text())
        self._assign_optional_float(payload, "top_p", self.top_p_input.text())
        self._assign_optional_int(payload, "max_tokens", self.max_tokens_input.text())
        self._assign_optional_float(payload, "presence_penalty", self.presence_penalty_input.text())
        self._assign_optional_float(payload, "frequency_penalty", self.frequency_penalty_input.text())

        if self.enable_thinking_checkbox.isChecked():
            payload["enable_thinking"] = True
        if self.stream_checkbox.isChecked():
            payload["stream"] = True

        return payload

    def _assign_optional_float(self, payload: dict[str, Any], key: str, raw: str) -> None:
        text = raw.strip()
        if not text:
            return
        try:
            payload[key] = float(text)
        except ValueError as exc:
            raise ValueError(f"{key} 必须是数字") from exc

    def _assign_optional_int(self, payload: dict[str, Any], key: str, raw: str) -> None:
        text = raw.strip()
        if not text:
            return
        try:
            payload[key] = int(text)
        except ValueError as exc:
            raise ValueError(f"{key} 必须是整数") from exc
