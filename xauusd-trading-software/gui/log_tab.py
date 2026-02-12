"""Log viewer tab displaying application logs in real time."""
from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton

from utils.logger import _LOG_FILE


class LogTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._init_ui()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(3000)
        self.refresh_timer.timeout.connect(self._load_logs)
        self.refresh_timer.start()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        refresh_btn = QPushButton("刷新日志")
        refresh_btn.clicked.connect(self._load_logs)

        layout.addWidget(self.log_view)
        layout.addWidget(refresh_btn)
        layout.addStretch()
        self.setLayout(layout)

    def _load_logs(self) -> None:
        log_path = Path(_LOG_FILE)
        if not log_path.exists():
            self.log_view.setPlainText("日志文件不存在")
            return
        with open(log_path, "r", encoding="utf-8") as handle:
            self.log_view.setPlainText(handle.read())
