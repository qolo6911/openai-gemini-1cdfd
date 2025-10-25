"""Live trading tab with execution controls."""
from __future__ import annotations

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from core.data.mt5_connector import MT5Connector
from core.live.executor import LiveExecutor
from utils.config_manager import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


class LiveTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigManager()
        self.connector = MT5Connector()
        self.executor = LiveExecutor(self.connector)
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(5000)
        self.poll_timer.timeout.connect(self._poll_market)
        self.last_signal_direction: str | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        self.status_label = QLabel("实盘未启动")
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)

        self.start_btn = QPushButton("启动实盘")
        self.start_btn.clicked.connect(self._start_live)

        self.stop_btn = QPushButton("停止实盘")
        self.stop_btn.clicked.connect(self._stop_live)
        self.stop_btn.setEnabled(False)

        self.positions_table = QTableWidget(0, 6)
        self.positions_table.setHorizontalHeaderLabels(["订单号", "方向", "手数", "开仓价", "当前价", "收益"])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.status_label)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.positions_table)
        layout.addWidget(QLabel("交易日志"))
        layout.addWidget(self.logs)
        layout.addStretch()
        self.setLayout(layout)

    def _start_live(self) -> None:
        login = self.config.get("mt5.login")
        password = self.config.get("mt5.password")
        server = self.config.get("mt5.server")

        if not self.connector.connect(login, password, server):
            self.status_label.setText("❌ MT5 连接失败")
            return

        self.poll_timer.start()
        self.status_label.setText("✅ 实盘运行中")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._log("实盘已启动")

    def _stop_live(self) -> None:
        self.poll_timer.stop()
        self.connector.disconnect()
        self.status_label.setText("实盘已停止")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._log("实盘已停止")

    def _poll_market(self) -> None:
        self._refresh_positions()
        positions = self.connector.get_positions()
        if len(positions) > 0:
            self._log("已有持仓，跳过信号评估")
            return

        df = self.connector.fetch_data(timeframe="M15", bars=100)
        if df is None:
            self._log("获取数据失败")
            return

        signal = self.executor.evaluate_signal(df)
        if not signal:
            self.last_signal_direction = None
            return

        if signal.direction != self.last_signal_direction:
            self._log(f"检测到信号: {signal.direction} @ {signal.entry_price:.2f}")
            success = self.executor.execute(signal)
            if success:
                self.last_signal_direction = signal.direction
                self._log(f"订单执行成功: {signal.direction}")
            else:
                self._log(f"订单执行失败: {signal.direction}")

    def _refresh_positions(self) -> None:
        positions = self.connector.get_positions()
        self.positions_table.setRowCount(len(positions))
        for row, position in enumerate(positions):
            self.positions_table.setItem(row, 0, QTableWidgetItem(str(position["ticket"])))
            self.positions_table.setItem(row, 1, QTableWidgetItem(position["type"]))
            self.positions_table.setItem(row, 2, QTableWidgetItem(str(position["volume"])))
            self.positions_table.setItem(row, 3, QTableWidgetItem(f"{position['price_open']:.2f}"))
            self.positions_table.setItem(row, 4, QTableWidgetItem(f"{position['price_current']:.2f}"))
            self.positions_table.setItem(row, 5, QTableWidgetItem(f"{position['profit']:.2f}"))

    def _log(self, message: str) -> None:
        logger.info(message)
        self.logs.append(message)
