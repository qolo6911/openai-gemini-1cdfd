from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGroupBox
from PyQt5.QtCore import QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from core.data.mt5_connector import MT5DataConnector
from core.features.indicators import calculate_ema


class MonitorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.connector = MT5DataConnector()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(3000)
        
        self.update_chart()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        status_group = QGroupBox("多周期状态")
        status_layout = QHBoxLayout()
        
        self.h4_label = QLabel("H4: -")
        self.h1_label = QLabel("H1: -")
        self.m15_label = QLabel("M15: -")
        self.regime_label = QLabel("Regime: -")
        
        status_layout.addWidget(self.h4_label)
        status_layout.addWidget(self.h1_label)
        status_layout.addWidget(self.m15_label)
        status_layout.addWidget(self.regime_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        self.setLayout(layout)
    
    def update_chart(self):
        df = self.connector.fetch_latest_data('M15', 200)
        
        df['ema21'] = calculate_ema(df['close'], 21)
        
        self.ax.clear()
        self.ax.plot(df.index, df['close'], label='Close', color='black')
        self.ax.plot(df.index, df['ema21'], label='EMA21', color='blue')
        self.ax.set_title('M15 价格走势')
        self.ax.legend()
        self.ax.grid(True)
        self.figure.autofmt_xdate()
        self.canvas.draw()
        
        latest_price = df['close'].iloc[-1]
        latest_ema = df['ema21'].iloc[-1]
        regime = '📈 Bullish Trend' if latest_price > latest_ema else '📉 Bearish Trend'
        
        self.h4_label.setText("H4: 🟢 Bullish")
        self.h1_label.setText("H1: 🟢 Bullish")
        self.m15_label.setText(f"M15: Price={latest_price:.2f} | EMA21={latest_ema:.2f}")
        self.regime_label.setText(f"Regime: {regime}")
