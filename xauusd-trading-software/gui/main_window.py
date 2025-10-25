"""Main window hosting navigation tabs."""
from __future__ import annotations

from PyQt5.QtWidgets import QMainWindow, QTabWidget

from gui.config_tab import ConfigTab
from gui.training_tab import TrainingTab
from gui.backtest_tab import BacktestTab
from gui.live_tab import LiveTab
from gui.monitor_tab import MonitorTab
from gui.log_tab import LogTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("XAUUSD AI Trading System")
        self.setGeometry(100, 100, 1400, 900)
        self._init_ui()

    def _init_ui(self) -> None:
        tab_widget = QTabWidget()
        tab_widget.addTab(ConfigTab(), "⚙️ 配置")
        tab_widget.addTab(TrainingTab(), "🎓 训练")
        tab_widget.addTab(BacktestTab(), "📈 回测")
        tab_widget.addTab(LiveTab(), "🚀 实盘")
        tab_widget.addTab(MonitorTab(), "📊 监控")
        tab_widget.addTab(LogTab(), "🧾 日志")
        self.setCentralWidget(tab_widget)
