import sys
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QStatusBar, QMenuBar, 
                             QAction, QMessageBox, QVBoxLayout, QWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
import os

from gui.config_widget import ConfigWidget
from gui.training_widget import TrainingWidget
from gui.backtest_widget import BacktestWidget
from gui.live_widget import LiveWidget
from gui.monitor_widget import MonitorWidget
from gui.log_widget import LogWidget


class MT5ConnectionThread(QThread):
    connection_status = pyqtSignal(str, str)
    
    def run(self):
        try:
            import MetaTrader5 as mt5
            if mt5.initialize():
                account_info = mt5.account_info()
                if account_info:
                    self.connection_status.emit("connected", f"账户: {account_info.login}")
                else:
                    self.connection_status.emit("connected", "已连接")
                mt5.shutdown()
            else:
                self.connection_status.emit("failed", "初始化失败")
        except Exception as e:
            self.connection_status.emit("error", str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XAUUSD AI Trading System v1.0")
        self.setGeometry(100, 100, 1400, 900)
        
        self.init_ui()
        self.load_stylesheet()
        self.update_status("就绪")
    
    def init_ui(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('文件')
        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        help_menu = menubar.addMenu('帮助')
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.config_widget = ConfigWidget()
        self.training_widget = TrainingWidget()
        self.backtest_widget = BacktestWidget()
        self.live_widget = LiveWidget()
        self.monitor_widget = MonitorWidget()
        self.log_widget = LogWidget()
        
        self.tabs.addTab(self.config_widget, "⚙️ 配置")
        self.tabs.addTab(self.training_widget, "🎓 训练")
        self.tabs.addTab(self.backtest_widget, "📊 回测")
        self.tabs.addTab(self.live_widget, "🚀 实盘")
        self.tabs.addTab(self.monitor_widget, "📈 监控")
        self.tabs.addTab(self.log_widget, "📝 日志")
        
        self.config_widget.config_saved.connect(self.on_config_saved)
        self.config_widget.mt5_test_requested.connect(self.test_mt5_connection)
        
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
    
    def load_stylesheet(self):
        qss_path = os.path.join(os.path.dirname(__file__), 'styles.qss')
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        else:
            stylesheet = """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2196F3;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QGroupBox {
                border: 2px solid #2196F3;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
                border: 2px solid #2196F3;
            }
            """
            self.setStyleSheet(stylesheet)
    
    def update_status(self, message):
        self.statusBar.showMessage(message)
    
    def test_mt5_connection(self):
        self.update_status("正在测试 MT5 连接...")
        self.mt5_thread = MT5ConnectionThread()
        self.mt5_thread.connection_status.connect(self.on_mt5_status)
        self.mt5_thread.start()
    
    def on_mt5_status(self, status, message):
        if status == "connected":
            self.update_status(f"✅ MT5 已连接 | {message}")
            QMessageBox.information(self, "连接成功", f"MT5 连接成功！\n{message}")
        elif status == "failed":
            self.update_status(f"❌ MT5 连接失败: {message}")
            QMessageBox.warning(self, "连接失败", f"MT5 连接失败！\n{message}")
        else:
            self.update_status(f"❌ MT5 错误: {message}")
            QMessageBox.critical(self, "错误", f"MT5 错误！\n{message}")
    
    def on_config_saved(self):
        self.update_status("配置已保存")
        self.log_widget.add_log("INFO", "配置已保存")
    
    def show_about(self):
        QMessageBox.about(
            self,
            "关于",
            "<h2>XAUUSD AI Trading System</h2>"
            "<p>版本 1.0</p>"
            "<p>基于深度学习的 XAUUSD 交易系统</p>"
            "<p>集成 TCN 模型、MT5 连接、风险管理</p>"
        )
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            '确认退出',
            '确定要退出程序吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
