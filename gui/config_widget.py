from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QGroupBox, QGridLayout,
                             QSpinBox, QDoubleSpinBox, QSlider, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from utils.config_manager import load_config, save_config, AppConfig


class ConfigWidget(QWidget):
    config_saved = pyqtSignal()
    mt5_test_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.init_ui()
        self.load_values()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        mt5_group = QGroupBox("MT5 连接设置")
        mt5_layout = QGridLayout()
        
        mt5_layout.addWidget(QLabel("经纪商服务器:"), 0, 0)
        self.server_edit = QLineEdit()
        mt5_layout.addWidget(self.server_edit, 0, 1)
        
        mt5_layout.addWidget(QLabel("账户登录:"), 1, 0)
        self.login_edit = QLineEdit()
        mt5_layout.addWidget(self.login_edit, 1, 1)
        
        mt5_layout.addWidget(QLabel("密码:"), 2, 0)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        mt5_layout.addWidget(self.password_edit, 2, 1)
        
        mt5_layout.addWidget(QLabel("交易品种:"), 3, 0)
        self.symbol_edit = QLineEdit()
        mt5_layout.addWidget(self.symbol_edit, 3, 1)
        
        self.test_mt5_btn = QPushButton("🔌 测试连接")
        self.test_mt5_btn.clicked.connect(self.mt5_test_requested.emit)
        mt5_layout.addWidget(self.test_mt5_btn, 4, 0, 1, 2)
        
        mt5_group.setLayout(mt5_layout)
        layout.addWidget(mt5_group)
        
        strategy_group = QGroupBox("策略参数")
        strategy_layout = QGridLayout()
        
        strategy_layout.addWidget(QLabel("EMA 周期:"), 0, 0)
        self.ema_spin = QSpinBox()
        self.ema_spin.setRange(5, 200)
        strategy_layout.addWidget(self.ema_spin, 0, 1)
        
        strategy_layout.addWidget(QLabel("ATR 周期:"), 1, 0)
        self.atr_spin = QSpinBox()
        self.atr_spin.setRange(5, 50)
        strategy_layout.addWidget(self.atr_spin, 1, 1)
        
        strategy_layout.addWidget(QLabel("TP 倍数 (k1):"), 2, 0)
        self.tp_slider = QSlider(Qt.Horizontal)
        self.tp_slider.setRange(5, 30)
        self.tp_slider.setValue(15)
        self.tp_label = QLabel("1.5")
        self.tp_slider.valueChanged.connect(lambda v: self.tp_label.setText(f"{v/10:.1f}"))
        tp_layout = QHBoxLayout()
        tp_layout.addWidget(self.tp_slider)
        tp_layout.addWidget(self.tp_label)
        strategy_layout.addLayout(tp_layout, 2, 1)
        
        strategy_layout.addWidget(QLabel("SL 倍数 (k2):"), 3, 0)
        self.sl_slider = QSlider(Qt.Horizontal)
        self.sl_slider.setRange(5, 20)
        self.sl_slider.setValue(10)
        self.sl_label = QLabel("1.0")
        self.sl_slider.valueChanged.connect(lambda v: self.sl_label.setText(f"{v/10:.1f}"))
        sl_layout = QHBoxLayout()
        sl_layout.addWidget(self.sl_slider)
        sl_layout.addWidget(self.sl_label)
        strategy_layout.addLayout(sl_layout, 3, 1)
        
        strategy_layout.addWidget(QLabel("点差:"), 4, 0)
        self.spread_spin = QDoubleSpinBox()
        self.spread_spin.setRange(0.0, 100.0)
        strategy_layout.addWidget(self.spread_spin, 4, 1)
        
        strategy_layout.addWidget(QLabel("持仓周期 (bar):"), 5, 0)
        self.holding_spin = QSpinBox()
        self.holding_spin.setRange(12, 48)
        strategy_layout.addWidget(self.holding_spin, 5, 1)
        
        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)
        
        risk_group = QGroupBox("风控设置")
        risk_layout = QGridLayout()
        
        risk_layout.addWidget(QLabel("每单风险 (%):"), 0, 0)
        self.risk_spin = QDoubleSpinBox()
        self.risk_spin.setRange(0.25, 1.0)
        self.risk_spin.setSingleStep(0.05)
        risk_layout.addWidget(self.risk_spin, 0, 1)
        
        risk_layout.addWidget(QLabel("最大日亏损 (%):"), 1, 0)
        self.max_loss_spin = QDoubleSpinBox()
        self.max_loss_spin.setRange(1.0, 10.0)
        risk_layout.addWidget(self.max_loss_spin, 1, 1)
        
        risk_layout.addWidget(QLabel("最大持仓数:"), 2, 0)
        self.max_pos_spin = QSpinBox()
        self.max_pos_spin.setRange(1, 10)
        risk_layout.addWidget(self.max_pos_spin, 2, 1)
        
        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)
        
        model_group = QGroupBox("模型参数")
        model_layout = QGridLayout()
        
        model_layout.addWidget(QLabel("回望窗口:"), 0, 0)
        self.window_combo = QComboBox()
        self.window_combo.addItems(['64', '128', '256'])
        model_layout.addWidget(self.window_combo, 0, 1)
        
        model_layout.addWidget(QLabel("概率阈值:"), 1, 0)
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.5, 0.9)
        self.threshold_spin.setSingleStep(0.05)
        model_layout.addWidget(self.threshold_spin, 1, 1)
        
        model_layout.addWidget(QLabel("模型选择:"), 2, 0)
        self.model_combo = QComboBox()
        self.model_combo.addItems(['TCN', 'Transformer'])
        model_layout.addWidget(self.model_combo, 2, 1)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 保存配置")
        self.save_btn.clicked.connect(self.save_configuration)
        self.restore_btn = QPushButton("🔄 恢复默认")
        self.restore_btn.clicked.connect(self.restore_defaults)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.restore_btn)
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_values(self):
        self.server_edit.setText(self.config.mt5.server)
        self.login_edit.setText(self.config.mt5.login)
        self.password_edit.setText(self.config.mt5.password)
        self.symbol_edit.setText(self.config.mt5.symbol)
        
        self.ema_spin.setValue(self.config.strategy.ema_period)
        self.atr_spin.setValue(self.config.strategy.atr_period)
        self.tp_slider.setValue(int(self.config.strategy.tp_multiplier * 10))
        self.sl_slider.setValue(int(self.config.strategy.sl_multiplier * 10))
        self.spread_spin.setValue(self.config.strategy.spread)
        self.holding_spin.setValue(self.config.strategy.holding_period)
        
        self.risk_spin.setValue(self.config.risk.risk_per_trade)
        self.max_loss_spin.setValue(self.config.risk.max_daily_loss)
        self.max_pos_spin.setValue(self.config.risk.max_positions)
        
        self.window_combo.setCurrentText(str(self.config.model.window_size))
        self.threshold_spin.setValue(self.config.model.threshold)
        self.model_combo.setCurrentText(self.config.model.model_type)
    
    def save_configuration(self):
        self.config.mt5.server = self.server_edit.text()
        self.config.mt5.login = self.login_edit.text()
        self.config.mt5.password = self.password_edit.text()
        self.config.mt5.symbol = self.symbol_edit.text()
        
        self.config.strategy.ema_period = self.ema_spin.value()
        self.config.strategy.atr_period = self.atr_spin.value()
        self.config.strategy.tp_multiplier = self.tp_slider.value() / 10.0
        self.config.strategy.sl_multiplier = self.sl_slider.value() / 10.0
        self.config.strategy.spread = self.spread_spin.value()
        self.config.strategy.holding_period = self.holding_spin.value()
        
        self.config.risk.risk_per_trade = self.risk_spin.value()
        self.config.risk.max_daily_loss = self.max_loss_spin.value()
        self.config.risk.max_positions = self.max_pos_spin.value()
        
        self.config.model.window_size = int(self.window_combo.currentText())
        self.config.model.threshold = self.threshold_spin.value()
        self.config.model.model_type = self.model_combo.currentText()
        
        save_config(self.config)
        self.config_saved.emit()
    
    def restore_defaults(self):
        self.config = AppConfig()
        self.load_values()
