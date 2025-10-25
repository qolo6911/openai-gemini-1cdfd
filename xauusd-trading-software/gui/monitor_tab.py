"""Real-time monitoring with candlestick chart and EMA overlay."""
from __future__ import annotations

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout

from core.data.mt5_connector import MT5Connector
from core.features.indicators import add_ema
from utils.config_manager import ConfigManager


class MonitorTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigManager()
        self.connector = MT5Connector()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(10000)
        self.refresh_timer.timeout.connect(self._refresh_chart)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        self.status_label = QLabel("未连接")

        connect_layout = QHBoxLayout()
        self.start_monitor_btn = QPushButton("开始监控")
        self.start_monitor_btn.clicked.connect(self._start_monitoring)
        self.stop_monitor_btn = QPushButton("停止监控")
        self.stop_monitor_btn.clicked.connect(self._stop_monitoring)
        self.stop_monitor_btn.setEnabled(False)
        connect_layout.addWidget(self.start_monitor_btn)
        connect_layout.addWidget(self.stop_monitor_btn)
        connect_layout.addStretch()

        self.figure = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("XAUUSD M15 实时图表")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Price")

        layout.addWidget(self.status_label)
        layout.addLayout(connect_layout)
        layout.addWidget(self.canvas)
        layout.addStretch()
        self.setLayout(layout)

    def _start_monitoring(self) -> None:
        login = self.config.get("mt5.login")
        password = self.config.get("mt5.password")
        server = self.config.get("mt5.server")

        if not self.connector.connect(login, password, server):
            self.status_label.setText("❌ MT5 连接失败")
            return

        self.refresh_timer.start()
        self.status_label.setText("✅ 监控中...")
        self.start_monitor_btn.setEnabled(False)
        self.stop_monitor_btn.setEnabled(True)
        self._refresh_chart()

    def _stop_monitoring(self) -> None:
        self.refresh_timer.stop()
        self.connector.disconnect()
        self.status_label.setText("监控已停止")
        self.start_monitor_btn.setEnabled(True)
        self.stop_monitor_btn.setEnabled(False)

    def _refresh_chart(self) -> None:
        df = self.connector.fetch_data(timeframe="M15", bars=200)
        if df is None:
            return

        ema_period = self.config.get("strategy.ema_period", 21)
        df = add_ema(df, ema_period)

        self.ax.clear()
        self.ax.plot(df.index[-100:], df["close"].iloc[-100:], label="Close", color="#4a9eff")
        self.ax.plot(
            df.index[-100:],
            df[f"ema_{ema_period}"].iloc[-100:],
            label=f"EMA{ema_period}",
            color="#f59e0b",
            linestyle="--",
        )
        self.ax.set_title("XAUUSD M15 实时图表")
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Price")
        self.ax.legend()
        self.ax.grid(alpha=0.3)
        self.canvas.draw()
