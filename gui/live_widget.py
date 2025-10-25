from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QGroupBox, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QTimer


class LiveWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.trading_active = False
        self.init_ui()
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_account_info)
        self.update_timer.start(5000)
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        control_group = QGroupBox("交易控制")
        control_layout = QVBoxLayout()
        
        status_layout = QHBoxLayout()
        self.connection_label = QLabel("MT5 连接: ⚪ 未连接")
        status_layout.addWidget(self.connection_label)
        control_layout.addLayout(status_layout)
        
        account_layout = QVBoxLayout()
        self.balance_label = QLabel("账户余额: $-")
        self.margin_label = QLabel("已用保证金: $-")
        self.free_margin_label = QLabel("可用保证金: $-")
        account_layout.addWidget(self.balance_label)
        account_layout.addWidget(self.margin_label)
        account_layout.addWidget(self.free_margin_label)
        control_layout.addLayout(account_layout)
        
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("🚀 启动自动交易")
        self.start_btn.clicked.connect(self.start_trading)
        self.pause_btn = QPushButton("⏸️ 暂停")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_trading)
        self.close_all_btn = QPushButton("❌ 全部平仓")
        self.close_all_btn.clicked.connect(self.close_all_positions)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.close_all_btn)
        control_layout.addLayout(btn_layout)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        positions_group = QGroupBox("当前持仓")
        positions_layout = QVBoxLayout()
        
        self.positions_table = QTableWidget(0, 6)
        self.positions_table.setHorizontalHeaderLabels(
            ["Ticket", "Type", "Lots", "Entry", "Current", "P/L"]
        )
        self.positions_table.horizontalHeader().setStretchLastSection(True)
        positions_layout.addWidget(self.positions_table)
        
        positions_group.setLayout(positions_layout)
        layout.addWidget(positions_group)
        
        signal_group = QGroupBox("最新信号")
        signal_layout = QVBoxLayout()
        
        self.signal_time_label = QLabel("时间: -")
        self.signal_regime_label = QLabel("Regime: -")
        self.signal_action_label = QLabel("信号: -")
        self.signal_entry_label = QLabel("入场: -")
        self.signal_sl_label = QLabel("止损: -")
        self.signal_tp_label = QLabel("止盈: -")
        
        signal_layout.addWidget(self.signal_time_label)
        signal_layout.addWidget(self.signal_regime_label)
        signal_layout.addWidget(self.signal_action_label)
        signal_layout.addWidget(self.signal_entry_label)
        signal_layout.addWidget(self.signal_sl_label)
        signal_layout.addWidget(self.signal_tp_label)
        
        signal_btn_layout = QHBoxLayout()
        self.execute_btn = QPushButton("✅ 执行交易")
        self.execute_btn.setEnabled(False)
        self.ignore_btn = QPushButton("🚫 忽略")
        self.ignore_btn.setEnabled(False)
        
        signal_btn_layout.addWidget(self.execute_btn)
        signal_btn_layout.addWidget(self.ignore_btn)
        signal_layout.addLayout(signal_btn_layout)
        
        signal_group.setLayout(signal_layout)
        layout.addWidget(signal_group)
        
        self.setLayout(layout)
    
    def start_trading(self):
        self.trading_active = True
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.connection_label.setText("MT5 连接: 🟢 已连接 (自动交易中)")
    
    def pause_trading(self):
        self.trading_active = False
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.connection_label.setText("MT5 连接: 🟡 已连接 (已暂停)")
    
    def close_all_positions(self):
        self.positions_table.setRowCount(0)
        
    def update_account_info(self):
        if self.trading_active:
            self.balance_label.setText("账户余额: $10,234.56")
            self.margin_label.setText("已用保证金: $856.23")
            self.free_margin_label.setText("可用保证金: $9,378.33")
