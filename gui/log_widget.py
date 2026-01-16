from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QCheckBox
from PyQt5.QtCore import Qt
from datetime import datetime


class LogWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.clear_btn = QPushButton("🗑️ 清空日志")
        self.clear_btn.clicked.connect(self.clear_logs)
        self.export_btn = QPushButton("📤 导出日志")
        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.auto_scroll_check)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
        
        self.add_log("INFO", "系统启动成功")
        self.add_log("INFO", "等待配置...")
    
    def add_log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        level_colors = {
            "INFO": "blue",
            "SUCCESS": "green",
            "WARNING": "orange",
            "ERROR": "red",
            "TRADE": "purple"
        }
        
        color = level_colors.get(level, "black")
        
        html = f'<span style="color: gray;">[{timestamp}]</span> '
        html += f'<span style="color: {color}; font-weight: bold;">[{level}]</span> '
        html += f'<span>{message}</span><br>'
        
        self.log_text.append(html)
        
        if self.auto_scroll_check.isChecked():
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        self.log_text.clear()
        self.add_log("INFO", "日志已清空")
