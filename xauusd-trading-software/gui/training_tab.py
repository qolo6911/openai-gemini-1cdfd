"""Training tab UI with background training thread and live loss chart."""
from __future__ import annotations

import pathlib
from typing import Optional

import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QProgressBar,
    QLabel,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
)

from core.data.mt5_connector import MT5Connector
from core.features.indicators import prepare_features
from core.labeling.triple_barrier import apply_triple_barrier
from core.models.tcn import TCNModel
from core.training.trainer import Trainer
from utils.config_manager import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


class TrainingThread(QThread):
    progress = pyqtSignal(int, float, float, float)
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        data: pd.DataFrame,
        model_path: pathlib.Path,
        config: ConfigManager,
    ) -> None:
        super().__init__()
        self.data = data
        self.model_path = model_path
        self.config = config
        self.history = {"train_loss": [], "val_loss": [], "val_acc": []}

    def run(self) -> None:
        try:
            self.history = {"train_loss": [], "val_loss": [], "val_acc": []}
            strategy_cfg = self.config.get("strategy")
            model_cfg = self.config.get("model")

            df = prepare_features(
                self.data.copy(),
                ema_period=strategy_cfg["ema_period"],
                atr_period=strategy_cfg["atr_period"],
            )
            df["label"] = apply_triple_barrier(df)
            df = df.dropna()
            if len(df) < 200:
                raise ValueError("训练数据不足，请提供更多历史数据")

            feature_columns = [
                "open",
                "high",
                "low",
                "close",
                "tick_volume",
                f"ema_{strategy_cfg['ema_period']}",
                f"atr_{strategy_cfg['atr_period']}",
                "regime",
                "returns",
                "volatility",
                "spread",
                "momentum",
                "rolling_mean",
                "rolling_std",
            ]

            model = TCNModel(
                num_inputs=len(feature_columns),
                hidden_channels=model_cfg["hidden_channels"],
                num_classes=model_cfg["num_classes"],
            )

            trainer = Trainer(model, learning_rate=model_cfg["learning_rate"])
            train_loader, val_loader = trainer.prepare_data(
                df,
                feature_columns=feature_columns,
                sequence_length=50,
                batch_size=model_cfg["batch_size"],
            )

            def progress_callback(epoch: int, train_loss: float, val_loss: float, val_acc: float) -> None:
                self.history["train_loss"].append(train_loss)
                self.history["val_loss"].append(val_loss)
                self.history["val_acc"].append(val_acc)
                self.progress.emit(epoch, train_loss, val_loss, val_acc)

            trainer.train(
                train_loader,
                val_loader,
                epochs=model_cfg["epochs"],
                progress_callback=progress_callback,
            )

            trainer.save_model(self.model_path)
            self.finished.emit("训练完成，模型已保存")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Training failed")
            self.failed.emit(str(exc))


class TrainingTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigManager()
        self.connector = MT5Connector()
        self.training_thread: Optional[TrainingThread] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        self.data_status = QLabel("未加载数据")
        self.load_data_btn = QPushButton("加载历史数据")
        self.load_data_btn.clicked.connect(self._load_data)

        self.start_btn = QPushButton("开始训练")
        self.start_btn.clicked.connect(self._start_training)
        self.start_btn.setEnabled(False)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.metrics_label = QLabel("")

        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("训练损失曲线")
        self.ax.set_xlabel("Epoch")
        self.ax.set_ylabel("Loss")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.load_data_btn)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addStretch()

        layout.addWidget(self.data_status)
        layout.addLayout(btn_layout)
        layout.addWidget(self.progress)
        layout.addWidget(self.metrics_label)
        layout.addWidget(self.canvas)
        layout.addStretch()
        self.setLayout(layout)

        self.data: Optional[pd.DataFrame] = None

    def _load_data(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择历史数据 CSV",
            "",
            "CSV Files (*.csv)",
        )
        if not file_path:
            return

        df = pd.read_csv(file_path)
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
        required_cols = {"open", "high", "low", "close"}
        if not required_cols.issubset(df.columns):
            QMessageBox.critical(self, "错误", "CSV 缺少必要列：open/high/low/close")
            return

        if "tick_volume" not in df.columns:
            df["tick_volume"] = 0

        if "time" in df.columns:
            df = df.sort_values("time")
            df = df.set_index("time", drop=False)

        self.data = df
        self.data_status.setText(f"✅ 已加载数据: {file_path}")
        self.start_btn.setEnabled(True)

    def _start_training(self) -> None:
        if self.data is None:
            QMessageBox.warning(self, "提示", "请先加载历史数据")
            return

        model_dir = pathlib.Path.home() / ".xauusd_trading"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / "tcn_model.pth"

        self.training_thread = TrainingThread(self.data, model_path, self.config)
        self.training_thread.progress.connect(self._on_progress)
        self.training_thread.finished.connect(self._on_finished)
        self.training_thread.failed.connect(self._on_failed)

        self.progress.setValue(0)
        self.metrics_label.setText("训练中...")
        self.start_btn.setEnabled(False)
        self.training_thread.start()

    def _on_progress(self, epoch: int, train_loss: float, val_loss: float, val_acc: float) -> None:
        epochs = self.config.get("model.epochs", 100)
        completion = int(epoch / epochs * 100)
        self.progress.setValue(completion)
        self.metrics_label.setText(
            f"Epoch {epoch} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}"
        )
        self.ax.clear()
        self.ax.plot(range(1, epoch + 1), self.training_thread.history["train_loss"], label="Train Loss")
        self.ax.plot(range(1, epoch + 1), self.training_thread.history["val_loss"], label="Val Loss")
        self.ax.legend()
        self.ax.set_xlabel("Epoch")
        self.ax.set_ylabel("Loss")
        self.canvas.draw()

    def _on_finished(self, message: str) -> None:
        self.progress.setValue(100)
        self.metrics_label.setText(message)
        self.start_btn.setEnabled(True)

    def _on_failed(self, error: str) -> None:
        QMessageBox.critical(self, "训练失败", error)
        self.metrics_label.setText("训练失败")
        self.start_btn.setEnabled(True)
