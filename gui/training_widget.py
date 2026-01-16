from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QProgressBar, QSpinBox, QDoubleSpinBox,
                             QGroupBox, QDateEdit, QRadioButton, QTextEdit)
from PyQt5.QtCore import QThread, pyqtSignal, QDate, Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class TrainingThread(QThread):
    progress = pyqtSignal(int, int, float, float)
    loss_update = pyqtSignal(list)
    finished_signal = pyqtSignal(str)
    
    def __init__(self, epochs, batch_size, lr):
        super().__init__()
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.losses = []
        self.running = True
    
    def run(self):
        from core.training.trainer import Trainer, TrainingConfig
        
        config = TrainingConfig(
            epochs=self.epochs,
            batch_size=self.batch_size,
            learning_rate=self.lr
        )
        
        def callback(metrics):
            if not self.running:
                return
            self.losses.append(metrics['train_loss'])
            self.progress.emit(
                metrics['epoch'],
                metrics['epochs'],
                metrics['train_loss'],
                metrics['val_acc']
            )
            self.loss_update.emit(self.losses)
        
        trainer = Trainer(config, progress_callback=callback)
        
        for metrics in trainer.train():
            if not self.running:
                break
            self.msleep(50)
        
        if self.running:
            trainer.save_model('models/best_model.pth')
            self.finished_signal.emit("训练完成！模型已保存至 models/best_model.pth")
        else:
            self.finished_signal.emit("训练已停止")
    
    def stop(self):
        self.running = False


class TrainingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.training_thread = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        data_group = QGroupBox("数据设置")
        data_layout = QVBoxLayout()
        
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("开始日期:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addYears(-5))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("结束日期:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)
        data_layout.addLayout(date_layout)
        
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("数据来源:"))
        self.mt5_radio = QRadioButton("MT5")
        self.mt5_radio.setChecked(True)
        self.csv_radio = QRadioButton("CSV文件")
        source_layout.addWidget(self.mt5_radio)
        source_layout.addWidget(self.csv_radio)
        source_layout.addStretch()
        data_layout.addLayout(source_layout)
        
        self.download_btn = QPushButton("📥 从 MT5 下载数据")
        self.download_btn.clicked.connect(self.download_data)
        data_layout.addWidget(self.download_btn)
        
        self.data_status_label = QLabel("状态: 未下载数据")
        data_layout.addWidget(self.data_status_label)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        train_group = QGroupBox("训练设置")
        train_layout = QVBoxLayout()
        
        param_grid = QHBoxLayout()
        
        epochs_layout = QVBoxLayout()
        epochs_layout.addWidget(QLabel("Epochs:"))
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(10, 500)
        self.epochs_spin.setValue(100)
        epochs_layout.addWidget(self.epochs_spin)
        param_grid.addLayout(epochs_layout)
        
        batch_layout = QVBoxLayout()
        batch_layout.addWidget(QLabel("Batch Size:"))
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(16, 256)
        self.batch_spin.setValue(64)
        batch_layout.addWidget(self.batch_spin)
        param_grid.addLayout(batch_layout)
        
        lr_layout = QVBoxLayout()
        lr_layout.addWidget(QLabel("Learning Rate:"))
        self.lr_spin = QDoubleSpinBox()
        self.lr_spin.setRange(0.0001, 0.01)
        self.lr_spin.setValue(0.001)
        self.lr_spin.setDecimals(4)
        lr_layout.addWidget(self.lr_spin)
        param_grid.addLayout(lr_layout)
        
        train_layout.addLayout(param_grid)
        
        self.gpu_label = QLabel("GPU 加速: ✅ 已启用 (检测中...)")
        train_layout.addWidget(self.gpu_label)
        self.check_gpu()
        
        train_group.setLayout(train_layout)
        layout.addWidget(train_group)
        
        btn_layout = QHBoxLayout()
        self.train_btn = QPushButton("▶️ 开始训练")
        self.train_btn.clicked.connect(self.start_training)
        self.stop_btn = QPushButton("⏸️ 停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_training)
        self.save_btn = QPushButton("💾 保存模型")
        self.save_btn.setEnabled(False)
        
        btn_layout.addWidget(self.train_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)
        
        progress_group = QGroupBox("训练进度")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("状态: 未开始")
        progress_layout.addWidget(self.status_label)
        
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.ax.set_xlabel('Epoch')
        self.ax.set_ylabel('Loss')
        self.ax.set_title('Training Loss Curve')
        self.ax.grid(True)
        progress_layout.addWidget(self.canvas)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        self.setLayout(layout)
    
    def check_gpu(self):
        try:
            import torch
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                self.gpu_label.setText(f"GPU 加速: ✅ 已启用 ({device_name})")
            else:
                self.gpu_label.setText("GPU 加速: ⚠️ 未检测到 CUDA (将使用 CPU)")
        except ImportError:
            self.gpu_label.setText("GPU 加速: ⚠️ PyTorch 未安装")
    
    def download_data(self):
        self.data_status_label.setText("状态: 正在下载数据...")
        self.download_btn.setEnabled(False)
        
        from core.data.mt5_connector import MT5DataConnector
        connector = MT5DataConnector()
        
        try:
            df_m15 = connector.fetch_data('M15', 10000)
            df_h1 = connector.fetch_data('H1', 5000)
            df_h4 = connector.fetch_data('H4', 2000)
            
            self.data_status_label.setText(
                f"状态: ✅ 数据已准备 (M15: {len(df_m15)}, H1: {len(df_h1)}, H4: {len(df_h4)})"
            )
        except Exception as e:
            self.data_status_label.setText(f"状态: ❌ 下载失败 - {str(e)}")
        finally:
            self.download_btn.setEnabled(True)
    
    def start_training(self):
        self.train_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("状态: 训练中...")
        
        self.training_thread = TrainingThread(
            epochs=self.epochs_spin.value(),
            batch_size=self.batch_spin.value(),
            lr=self.lr_spin.value()
        )
        self.training_thread.progress.connect(self.update_progress)
        self.training_thread.loss_update.connect(self.update_loss_chart)
        self.training_thread.finished_signal.connect(self.on_training_finished)
        self.training_thread.start()
    
    def stop_training(self):
        if self.training_thread:
            self.training_thread.stop()
    
    def update_progress(self, epoch, total_epochs, train_loss, val_acc):
        progress = int((epoch / total_epochs) * 100)
        self.progress_bar.setValue(progress)
        self.status_label.setText(
            f"状态: Epoch {epoch}/{total_epochs} | "
            f"Loss: {train_loss:.4f} | Val Acc: {val_acc:.2%}"
        )
    
    def update_loss_chart(self, losses):
        self.ax.clear()
        self.ax.plot(losses, label='Training Loss', color='blue', linewidth=2)
        self.ax.set_xlabel('Epoch')
        self.ax.set_ylabel('Loss')
        self.ax.set_title('Training Loss Curve')
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()
    
    def on_training_finished(self, message):
        self.train_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_btn.setEnabled(True)
        self.status_label.setText(f"状态: {message}")
