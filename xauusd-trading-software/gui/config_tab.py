"""Configuration tab for MT5 connection and strategy parameters."""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QLabel,
    QMessageBox,
)

from core.data.mt5_connector import MT5Connector
from utils.config_manager import ConfigManager


class ConfigTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigManager()
        self.connector = MT5Connector()
        self._init_ui()
        self._load_config()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        mt5_group = QGroupBox("MT5 连接配置")
        mt5_layout = QFormLayout()
        self.login_input = QSpinBox()
        self.login_input.setMaximum(999999999)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.server_input = QLineEdit()
        mt5_layout.addRow("账号:", self.login_input)
        mt5_layout.addRow("密码:", self.password_input)
        mt5_layout.addRow("服务器:", self.server_input)
        mt5_group.setLayout(mt5_layout)

        connect_layout = QHBoxLayout()
        self.connect_btn = QPushButton("连接 MT5")
        self.connect_btn.clicked.connect(self._connect_mt5)
        self.status_label = QLabel("未连接")
        connect_layout.addWidget(self.connect_btn)
        connect_layout.addWidget(self.status_label)
        connect_layout.addStretch()

        strategy_group = QGroupBox("策略参数")
        strategy_layout = QFormLayout()
        self.spread_input = QSpinBox()
        self.spread_input.setMaximum(100)
        self.lot_size_input = QDoubleSpinBox()
        self.lot_size_input.setSingleStep(0.01)
        self.lot_size_input.setDecimals(2)
        self.lot_size_input.setMaximum(10.0)
        self.ema_period_input = QSpinBox()
        self.ema_period_input.setMaximum(200)
        self.atr_period_input = QSpinBox()
        self.atr_period_input.setMaximum(100)
        self.atr_sl_input = QDoubleSpinBox()
        self.atr_sl_input.setSingleStep(0.1)
        self.atr_sl_input.setDecimals(1)
        self.atr_tp_input = QDoubleSpinBox()
        self.atr_tp_input.setSingleStep(0.1)
        self.atr_tp_input.setDecimals(1)

        strategy_layout.addRow("点差 (点):", self.spread_input)
        strategy_layout.addRow("手数:", self.lot_size_input)
        strategy_layout.addRow("EMA 周期:", self.ema_period_input)
        strategy_layout.addRow("ATR 周期:", self.atr_period_input)
        strategy_layout.addRow("ATR 止损倍数:", self.atr_sl_input)
        strategy_layout.addRow("ATR 止盈倍数:", self.atr_tp_input)
        strategy_group.setLayout(strategy_layout)

        save_btn = QPushButton("保存配置")
        save_btn.clicked.connect(self._save_config)

        layout.addWidget(mt5_group)
        layout.addLayout(connect_layout)
        layout.addWidget(strategy_group)
        layout.addWidget(save_btn)
        layout.addStretch()
        self.setLayout(layout)

    def _load_config(self) -> None:
        self.login_input.setValue(self.config.get("mt5.login", 0))
        self.password_input.setText(self.config.get("mt5.password", ""))
        self.server_input.setText(self.config.get("mt5.server", ""))
        self.spread_input.setValue(self.config.get("strategy.spread_points", 16))
        self.lot_size_input.setValue(self.config.get("strategy.lot_size", 0.1))
        self.ema_period_input.setValue(self.config.get("strategy.ema_period", 21))
        self.atr_period_input.setValue(self.config.get("strategy.atr_period", 14))
        self.atr_sl_input.setValue(self.config.get("strategy.atr_sl_multiplier", 2.0))
        self.atr_tp_input.setValue(self.config.get("strategy.atr_tp_multiplier", 3.0))

    def _save_config(self) -> None:
        self.config.set("mt5.login", self.login_input.value())
        self.config.set("mt5.password", self.password_input.text())
        self.config.set("mt5.server", self.server_input.text())
        self.config.set("strategy.spread_points", self.spread_input.value())
        self.config.set("strategy.lot_size", self.lot_size_input.value())
        self.config.set("strategy.ema_period", self.ema_period_input.value())
        self.config.set("strategy.atr_period", self.atr_period_input.value())
        self.config.set("strategy.atr_sl_multiplier", self.atr_sl_input.value())
        self.config.set("strategy.atr_tp_multiplier", self.atr_tp_input.value())
        QMessageBox.information(self, "成功", "配置已保存")

    def _connect_mt5(self) -> None:
        login = self.login_input.value()
        password = self.password_input.text()
        server = self.server_input.text()

        if not login or not password or not server:
            QMessageBox.warning(self, "错误", "请填写完整的连接信息")
            return

        success = self.connector.connect(login, password, server)
        if success:
            self.status_label.setText("✅ 已连接")
            self.status_label.setStyleSheet("color: #4ade80;")
            QMessageBox.information(self, "成功", "MT5 连接成功")
        else:
            self.status_label.setText("❌ 连接失败")
            self.status_label.setStyleSheet("color: #f87171;")
            QMessageBox.critical(self, "错误", "MT5 连接失败，请检查账号信息")
