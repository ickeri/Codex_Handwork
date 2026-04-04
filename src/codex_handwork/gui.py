import random
import string
import subprocess
import threading
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from codex_handwork.services.count import get_auth_file_count
from codex_handwork.services.email_store import allocate_next_email
from codex_handwork.services.mail import find_code_by_email
from codex_handwork.services.oauth import get_auth_url
from codex_handwork.services.status import get_auth_status
from codex_handwork.settings import get_settings, save_settings

BACKGROUND_IMAGE = Path(__file__).resolve().parent / "assets" / "background.png"
APP_ICON_IMAGE = Path(__file__).resolve().parent / "assets" / "app_icon.png"
SETTINGS_BACKGROUND_IMAGE = APP_ICON_IMAGE


def build_window_icon(size: int = 256, radius: int = 56, zoom: float = 1.22) -> QIcon:
    source = QPixmap(str(APP_ICON_IMAGE))
    if source.isNull():
        return QIcon()
    target_size = max(int(size * zoom), size)
    scaled = source.scaled(target_size, target_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    canvas = QPixmap(size, size)
    canvas.fill(Qt.transparent)
    offset_x = (scaled.width() - size) / 2
    offset_y = (scaled.height() - size) / 2

    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(-offset_x, -offset_y, scaled)
    painter.end()
    return QIcon(canvas)


class SettingsDialog(QDialog):
    def __init__(self, parent=None, stays_on_top=False):
        flags = Qt.Dialog
        if stays_on_top:
            flags |= Qt.WindowStaysOnTopHint
        super().__init__(parent, flags)
        self.background = QPixmap(str(SETTINGS_BACKGROUND_IMAGE))
        self.setWindowTitle("配置")
        self.setWindowIcon(build_window_icon())
        self.resize(640, 420)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            """
            QDialog {
                background: transparent;
            }
            QLabel {
                color: white;
                font-weight: 700;
                background: transparent;
            }
            #settings_panel {
                background: rgba(8, 15, 30, 170);
                border: 1px solid rgba(255, 255, 255, 72);
                border-radius: 18px;
            }
            #settings_title {
                font-size: 18px;
                font-weight: 800;
                color: rgba(255, 255, 255, 245);
            }
            #settings_hint {
                color: rgba(255, 255, 255, 220);
                font-weight: 600;
            }
            QLineEdit {
                min-width: 360px;
                min-height: 34px;
                background: rgba(255, 255, 255, 188);
                border: 1px solid rgba(255, 255, 255, 170);
                border-radius: 10px;
                padding: 0 10px;
                color: #1f2937;
            }
            QLineEdit:focus {
                background: rgba(255, 255, 255, 225);
                border: 1px solid rgba(59, 130, 246, 225);
            }
            QPushButton {
                min-width: 96px;
                min-height: 34px;
                background: rgba(37, 99, 235, 215);
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: 700;
                padding: 0 12px;
            }
            QPushButton:hover {
                background: rgba(29, 78, 216, 228);
            }
            QPushButton:pressed {
                background: rgba(30, 64, 175, 235);
            }
            """
        )

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(22, 22, 22, 22)

        panel = QWidget()
        panel.setObjectName("settings_panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(22, 20, 22, 20)
        panel_layout.setSpacing(14)

        title = QLabel("配置")
        title.setObjectName("settings_title")
        panel_layout.addWidget(title)

        hint = QLabel("修改后会立即写入 settings.json，并用于后续开始操作。")
        hint.setObjectName("settings_hint")
        hint.setWordWrap(True)
        panel_layout.addWidget(hint)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignTop)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout.setHorizontalSpacing(16)
        form_layout.setVerticalSpacing(12)

        self.default_password_input = QLineEdit()
        self.mail_url_input = QLineEdit()
        self.mail_url_input.setPlaceholderText("https://example.com/api/allEmail/list")
        self.mail_authorization_input = QLineEdit()
        self.mail_authorization_input.setPlaceholderText("eyJ....")
        self.oauth_base_address_input = QLineEdit()
        self.oauth_base_address_input.setPlaceholderText("127.0.0.1:8317")
        self.oauth_authorization_suffix_input = QLineEdit()
        self.oauth_authorization_suffix_input.setPlaceholderText("CPA密码")
        self.email_prefix_input = QLineEdit()
        self.email_prefix_input.setPlaceholderText("test")
        self.email_domain_input = QLineEdit()
        self.email_domain_input.setPlaceholderText("@example.com")

        form_layout.addRow("默认密码", self.default_password_input)
        form_layout.addRow("邮件接口地址", self.mail_url_input)
        form_layout.addRow("邮件Authorization", self.mail_authorization_input)
        form_layout.addRow("CPA接口地址", self.oauth_base_address_input)
        form_layout.addRow("CPAAuthorization", self.oauth_authorization_suffix_input)
        form_layout.addRow("邮箱前缀", self.email_prefix_input)
        form_layout.addRow("邮箱域名", self.email_domain_input)
        panel_layout.addLayout(form_layout)

        button_row = QHBoxLayout()
        button_row.setSpacing(16)
        button_row.addStretch(1)

        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_settings)
        button_row.addWidget(save_button)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_row.addWidget(cancel_button)

        button_row.addStretch(1)

        panel_layout.addLayout(button_row)
        root_layout.addWidget(panel)
        self.setLayout(root_layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background.isNull():
            painter.setOpacity(0.7)
            painter.drawPixmap(self.rect(), self.background)
            painter.setOpacity(1.0)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 92))
        super().paintEvent(event)

    def _display_value(self, value: str, placeholders: tuple[str, ...]) -> str:
        text = (value or "").strip()
        if not text:
            return ""
        if text in placeholders:
            return ""
        if text.startswith("请填写"):
            return ""
        return text

    def _load_values(self):
        settings = get_settings()
        self.default_password_input.setText(
            self._display_value(settings["gui"].get("default_password", ""), ("请填写默认密码",))
        )
        self.mail_url_input.setText(
            self._display_value(settings["mail"].get("url", ""), ("https://example.com/api/allEmail/list",))
        )
        self.mail_authorization_input.setText(
            self._display_value(settings["mail"].get("authorization", ""), ("eyJ....", "请填写邮件接口 authorization"))
        )
        self.oauth_base_address_input.setText(
            self._display_value(settings["oauth"].get("base_address", ""), ("127.0.0.1:8317",))
        )
        self.oauth_authorization_suffix_input.setText(
            self._display_value(settings["oauth"].get("authorization_suffix", ""), ("CPA密码", "请填写CPA密码"))
        )
        self.email_prefix_input.setText(
            self._display_value(settings["email"].get("prefix", ""), ("test",))
        )
        self.email_domain_input.setText(
            self._display_value(settings["email"].get("domain", ""), ("@example.com",))
        )

    def save_settings(self):
        settings = get_settings()
        oauth_auth = self.oauth_authorization_suffix_input.text().strip()
        if oauth_auth.startswith("Bearer "):
            oauth_auth = oauth_auth[len("Bearer "):].strip()

        settings["gui"]["default_password"] = self.default_password_input.text().strip()
        settings["mail"]["url"] = self.mail_url_input.text().strip()
        settings["mail"]["authorization"] = self.mail_authorization_input.text().strip()
        settings["oauth"]["base_address"] = self.oauth_base_address_input.text().strip()
        settings["oauth"]["authorization_suffix"] = oauth_auth
        settings["email"]["prefix"] = self.email_prefix_input.text().strip()
        settings["email"]["domain"] = self.email_domain_input.text().strip()
        settings["oauth"].pop("cookies", None)
        settings["oauth"].pop("cookies_comment", None)

        save_settings(settings)
        QMessageBox.information(self, "提示", "配置已保存")
        self.accept()


class CopyWindow(QWidget):
    authDataLoaded = Signal(int, str, str)
    errorRaised = Signal(int, str)
    codeLoaded = Signal(int, str)
    authStatusLoaded = Signal(int, object)
    accountCountLoaded = Signal(int, str)

    def __init__(self):
        super().__init__()
        self.background = QPixmap(str(BACKGROUND_IMAGE))
        self.setWindowIcon(build_window_icon())
        self.session_id = 0
        self.current_state = None
        self.auth_status_loading = False
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.poll_auth_status)
        self.authDataLoaded.connect(self._apply_auth_data)
        self.errorRaised.connect(self._handle_error)
        self.codeLoaded.connect(self._apply_code)
        self.authStatusLoaded.connect(self._apply_auth_status)
        self.accountCountLoaded.connect(self._apply_account_count)
        self._build_ui()
        self._apply_style()
        self._apply_window_flags()
        self._apply_runtime_settings()

    def _settings(self) -> dict:
        return get_settings()

    def _gui_settings(self) -> dict:
        return self._settings()["gui"]

    def _default_password(self) -> str:
        return self._gui_settings()["default_password"]

    def _callback_port(self) -> int:
        return self._gui_settings()["callback_port"]

    def _apply_runtime_settings(self):
        self.setWindowTitle(self._gui_settings()["window_title"])
        if hasattr(self, "password_input"):
            self.password_input.setText(self._default_password())

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 10, 16, 10)
        main_layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        status_title = QLabel("状态")
        status_title.setFixedWidth(34)
        status_title.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        top_row.addWidget(status_title)

        self.detect_status_label = QLabel("未开始")
        self.detect_status_label.setObjectName("detect_status_label")
        self.detect_status_label.setFixedHeight(32)
        self.detect_status_label.setAlignment(Qt.AlignCenter)
        self.detect_status_label.setMinimumWidth(72)
        self.detect_status_label.setMaximumWidth(88)
        top_row.addWidget(self.detect_status_label)

        self.start_button = QPushButton("开始")
        self.start_button.setFixedSize(96, 34)
        self.start_button.clicked.connect(self.start_flow)
        top_row.addWidget(self.start_button)

        self.pin_checkbox = QCheckBox("固定在屏幕最前")
        self.pin_checkbox.stateChanged.connect(self.toggle_topmost)
        top_row.addWidget(self.pin_checkbox)

        self.loop_checkbox = QCheckBox("循环执行")
        top_row.addWidget(self.loop_checkbox)

        top_row.addStretch(1)
        main_layout.addLayout(top_row)

        self.url_input = self._add_row(main_layout, "URL", "等待获取 URL", read_only=False)
        self.email_input = self._add_row(main_layout, "邮箱", "等待生成邮箱", read_only=False)
        self.password_input = self._add_row(main_layout, "密码", "固定密码", read_only=False)
        self.code_input = self._add_row(main_layout, "验证码", "等待验证码", read_only=False)
        self.nickname_input = self._add_row(main_layout, "昵称", "等待生成昵称", read_only=True)

        footer_row = QHBoxLayout()
        footer_row.setSpacing(8)

        self.status_label = QLabel("点击开始后自动生成邮箱并获取 URL")
        self.status_label.setWordWrap(True)
        footer_row.addWidget(self.status_label, 1)

        footer_row.addStretch(1)

        self.settings_button = QPushButton("配置")
        self.settings_button.setFixedSize(96, 32)
        self.settings_button.clicked.connect(self.open_settings_dialog)
        footer_row.addWidget(self.settings_button)

        self.account_count_title = QLabel("账号数量")
        self.account_count_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        footer_row.addWidget(self.account_count_title)

        self.account_count_label = QLabel("--")
        self.account_count_label.setObjectName("account_count_label")
        self.account_count_label.setAlignment(Qt.AlignCenter)
        self.account_count_label.setFixedHeight(28)
        self.account_count_label.setMinimumWidth(54)
        self.account_count_label.setMaximumWidth(80)
        footer_row.addWidget(self.account_count_label)

        main_layout.addLayout(footer_row)
        self.setLayout(main_layout)
        self.adjustSize()
        self.setFixedSize(self.sizeHint())

    def open_settings_dialog(self):
        dialog = SettingsDialog(self, stays_on_top=self.pin_checkbox.isChecked())
        if dialog.exec():
            self._apply_runtime_settings()
            self._show_short_status("配置已保存")

    def _add_row(self, layout, label_text, placeholder, read_only=False, show_copy_button=True):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)

        label = QLabel(label_text)
        label.setFixedWidth(56)
        label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setFixedHeight(32)
        line_edit.setReadOnly(read_only)

        row_layout.addWidget(label)
        row_layout.addWidget(line_edit, 1)

        if show_copy_button:
            copy_button = QPushButton("复制")
            copy_button.setFixedSize(82, 32)
            copy_button.clicked.connect(lambda _, widget=line_edit: self.copy_text(widget))
            row_layout.addWidget(copy_button)

        layout.addLayout(row_layout)
        return line_edit

    def _apply_style(self):
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            """
            QWidget {
                background: transparent;
                font-size: 13px;
                color: white;
            }
            QCheckBox, QLabel {
                font-weight: 700;
                color: rgba(255, 255, 255, 235);
            }
            QLineEdit {
                background: rgba(255, 255, 255, 178);
                border: 1px solid rgba(255, 255, 255, 165);
                border-radius: 10px;
                padding: 0 10px;
                color: #1f2937;
            }
            QLabel {
                background: transparent;
            }
            #detect_status_label {
                background: rgba(255, 255, 255, 178);
                border: 1px solid rgba(255, 255, 255, 165);
                border-radius: 10px;
                color: #1f2937;
                padding: 0 10px;
            }
            #account_count_label {
                background: rgba(255, 255, 255, 178);
                border: 1px solid rgba(255, 255, 255, 165);
                border-radius: 10px;
                color: #1f2937;
                padding: 0 8px;
            }
            QLineEdit:focus {
                background: rgba(255, 255, 255, 215);
                border: 1px solid rgba(59, 130, 246, 225);
            }
            QPushButton {
                background: rgba(37, 99, 235, 215);
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: 700;
                padding: 0 10px;
            }
            QPushButton:hover {
                background: rgba(29, 78, 216, 228);
            }
            QPushButton:pressed {
                background: rgba(30, 64, 175, 235);
            }
            """
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background.isNull():
            painter.drawPixmap(self.rect(), self.background)
        painter.fillRect(self.rect(), QColor(255, 255, 255, 77))
        super().paintEvent(event)

    def _apply_window_flags(self):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.pin_checkbox.isChecked())
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def toggle_topmost(self, state):
        self._apply_window_flags()

    def _show_short_status(self, message, timeout=None):
        if timeout is None:
            timeout = self._gui_settings()["status_message_timeout_ms"]
        self.status_label.setText(message)
        current_session = self.session_id
        QTimer.singleShot(timeout, lambda: self._restore_status_text(current_session, message))

    def _restore_status_text(self, session_id, previous_message):
        if session_id != self.session_id:
            return
        if self.status_label.text() != previous_message:
            return
        if self.current_state:
            self.status_label.setText("URL 已获取并自动复制，正在监听验证码和认证状态...")
        else:
            self.status_label.setText("点击开始后自动生成邮箱并获取 URL")

    def copy_text(self, line_edit):
        text = line_edit.text().strip()
        if not text:
            QMessageBox.information(self, "提示", "输入框内容为空")
            return
        QApplication.clipboard().setText(text)
        self._show_short_status("已复制")

    def _generate_nickname(self):
        return "".join(random.choice(string.ascii_lowercase) for _ in range(self._gui_settings()["nickname_length"]))

    def _release_callback_port(self):
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{self._callback_port()}"],
            capture_output=True,
            text=True,
            check=False,
        )
        pids = [pid.strip() for pid in result.stdout.splitlines() if pid.strip()]
        if not pids:
            return False
        subprocess.run(["kill", "-9", *pids], check=False)
        return True

    def start_flow(self):
        self.session_id += 1
        session_id = self.session_id
        self.current_state = None
        self.auth_status_loading = False
        self.status_timer.stop()
        self.start_button.setEnabled(False)
        self.code_input.clear()
        self.url_input.clear()
        self.detect_status_label.setText("等待检测")
        self.nickname_input.setText(self._generate_nickname())
        self.status_label.setText("正在检查端口并获取 URL...")

        try:
            released = self._release_callback_port()
            email = allocate_next_email()
        except Exception as e:
            self.start_button.setEnabled(True)
            self.detect_status_label.setText("异常")
            self.status_label.setText(f"启动前检查失败: {e}")
            return

        if released:
            self._show_short_status(f"{self._callback_port()} 端口已释放")

        self.email_input.setText(email)
        self.password_input.setText(self._default_password())

        threading.Thread(target=self._load_auth_data, args=(session_id,), daemon=True).start()
        threading.Thread(target=self._poll_code_loop, args=(session_id, email), daemon=True).start()

    def _load_auth_data(self, session_id):
        try:
            auth_data = get_auth_url()
            state = auth_data.get("state")
            url = auth_data.get("url") or ""
            if not state:
                raise RuntimeError("oauth.py 未返回 state")
            self.authDataLoaded.emit(session_id, state, url)
        except Exception as e:
            self.errorRaised.emit(session_id, f"获取 URL 失败: {e}")

    def _apply_auth_data(self, session_id, state, url):
        if session_id != self.session_id:
            return
        self.current_state = state
        self.auth_status_loading = False
        self.url_input.setText(url)
        if url:
            QApplication.clipboard().setText(url)
        self.detect_status_label.setText("等待检测")
        self.status_label.setText("URL 已获取并自动复制，正在监听验证码和认证状态...")
        if url:
            self._show_short_status("URL 已复制")
        self.status_timer.start(self._gui_settings()["auth_poll_interval_ms"])
        self.start_button.setEnabled(True)

    def _handle_error(self, session_id, message):
        if session_id != self.session_id:
            return
        self.auth_status_loading = False
        self.detect_status_label.setText("异常")
        self.status_label.setText(message)
        self.start_button.setEnabled(True)
        self.status_timer.stop()

    def _poll_code_loop(self, session_id, email):
        while session_id == self.session_id:
            try:
                code = find_code_by_email(email)
                if code:
                    self.codeLoaded.emit(session_id, code)
                    return
            except Exception as e:
                self.errorRaised.emit(session_id, f"监听验证码失败: {e}")
                return
            time.sleep(self._gui_settings()["code_poll_interval_seconds"])

    def _apply_code(self, session_id, code):
        if session_id != self.session_id:
            return
        self.code_input.setText(code)
        QApplication.clipboard().setText(code)
        self.status_label.setText("已匹配到当前邮箱验证码，并自动复制")

    def poll_auth_status(self):
        if not self.current_state or self.auth_status_loading:
            return
        session_id = self.session_id
        self.auth_status_loading = True
        threading.Thread(target=self._load_auth_status, args=(session_id, self.current_state), daemon=True).start()

    def _load_auth_status(self, session_id, state):
        try:
            data = get_auth_status(state)
            self.authStatusLoaded.emit(session_id, data)
        except Exception as e:
            self.errorRaised.emit(session_id, f"查询认证状态失败: {e}")

    def _refresh_account_count(self, session_id):
        try:
            count = get_auth_file_count()
            self.accountCountLoaded.emit(session_id, str(count))
        except Exception as e:
            self.errorRaised.emit(session_id, f"刷新账号数量失败: {e}")

    def _apply_account_count(self, session_id, count_text):
        if session_id != self.session_id:
            return
        self.account_count_label.setText(count_text)

    def _schedule_account_count_refresh(self, session_id):
        QTimer.singleShot(self._gui_settings()["account_count_refresh_delay_ms"], lambda: self._start_account_count_refresh_if_current(session_id))

    def _start_account_count_refresh_if_current(self, session_id):
        if session_id != self.session_id:
            return
        threading.Thread(target=self._refresh_account_count, args=(session_id,), daemon=True).start()

    def _schedule_next_round(self, session_id):
        QTimer.singleShot(self._gui_settings()["next_round_delay_ms"], lambda: self._start_next_round_if_current(session_id))

    def _start_next_round_if_current(self, session_id):
        if session_id != self.session_id:
            return
        if not self.loop_checkbox.isChecked():
            return
        if not self.isVisible():
            return
        self.start_flow()

    def _apply_auth_status(self, session_id, data):
        if session_id != self.session_id:
            return
        self.auth_status_loading = False
        status = data.get("status")
        if status == "ok":
            self.status_timer.stop()
            self.detect_status_label.setText("注册成功")
            self._schedule_account_count_refresh(session_id)
            if self.loop_checkbox.isChecked():
                self.status_label.setText("注册成功，5 秒后开始下一轮")
                self._schedule_next_round(session_id)
            else:
                self.status_label.setText("注册成功")
            return
        if status == "wait":
            self.detect_status_label.setText("注册中")
            self.status_label.setText("等待认证完成中...")
            return
        self.status_timer.stop()
        self.detect_status_label.setText(f"异常: {status}")
        self.status_label.setText(f"认证状态异常: {status}")
