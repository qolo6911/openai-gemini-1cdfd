"""Backtest tab enabling historical performance evaluation."""
from __future__ import annotations

import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
)

from core.features.indicators import prepare_features
from utils.config_manager import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


class BacktestTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigManager()
        self.data: pd.DataFrame | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        header = QLabel("历史数据回测")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")

        controls = QHBoxLayout()
        self.load_btn = QPushButton("加载历史数据")
        self.load_btn.clicked.connect(self._load_data)
        self.run_btn = QPushButton("运行回测")
        self.run_btn.clicked.connect(self._run_backtest)
        self.run_btn.setEnabled(False)
        controls.addWidget(self.load_btn)
        controls.addWidget(self.run_btn)
        controls.addStretch()

        self.status_label = QLabel("未加载数据")

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlainText("请先加载历史数据，然后运行回测。")

        layout.addWidget(header)
        layout.addLayout(controls)
        layout.addWidget(self.status_label)
        layout.addWidget(self.results_text)
        layout.addStretch()
        self.setLayout(layout)

    def _load_data(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择历史数据 CSV",
            "",
            "CSV Files (*.csv)",
        )
        if not file_path:
            return

        try:
            df = pd.read_csv(file_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to read CSV")
            QMessageBox.critical(self, "错误", f"无法读取 CSV: {exc}")
            return

        required_cols = {"open", "high", "low", "close"}
        if not required_cols.issubset(df.columns):
            QMessageBox.critical(self, "错误", "CSV 缺少必要列：open/high/low/close")
            return

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
            df = df.sort_values("time")
            df = df.set_index("time", drop=False)

        if "tick_volume" not in df.columns:
            df["tick_volume"] = 0

        self.data = df
        self.status_label.setText(f"✅ 已加载数据: {file_path}")
        self.run_btn.setEnabled(True)
        self.results_text.setPlainText("数据已加载，点击 \"运行回测\" 开始评估。")

    def _run_backtest(self) -> None:
        if self.data is None:
            QMessageBox.warning(self, "提示", "请先加载历史数据")
            return

        strategy_cfg = self.config.get("strategy")
        ema_period = strategy_cfg["ema_period"]
        atr_period = strategy_cfg["atr_period"]
        spread_points = strategy_cfg["spread_points"]
        threshold = strategy_cfg.get("oscillation_threshold", 0.3)

        df = prepare_features(
            self.data.copy(),
            ema_period=ema_period,
            atr_period=atr_period,
        )

        if len(df) < 200:
            QMessageBox.warning(self, "提示", "历史数据不足，无法进行回测")
            return

        results = self._simulate_strategy(df, ema_period, spread_points, threshold)
        self._display_results(results)

    def _simulate_strategy(
        self,
        df: pd.DataFrame,
        ema_period: int,
        spread_points: int,
        threshold: float,
    ) -> dict:
        df = df.copy()
        df["deviation"] = (df["close"] - df[f"ema_{ema_period}"]) / df[f"ema_{ema_period}"]
        df["signal"] = 0
        df.loc[df["deviation"] <= -threshold, "signal"] = 1
        df.loc[df["deviation"] >= threshold, "signal"] = -1

        position = 0
        positions = []
        trade_returns = []
        equity_curve = [1.0]

        spread_cost = spread_points * 0.1 / 1000

        for idx, row in df.iterrows():
            signal = row["signal"]

            if signal != position:
                if position != 0:
                    positions[-1]["exit_time"] = idx
                    positions[-1]["exit_price"] = row["close"]
                    positions[-1]["pnl"] = np.log(row["close"] / positions[-1]["entry_price"]) * position - spread_cost
                    trade_returns.append(positions[-1]["pnl"])
                if signal != 0:
                    positions.append(
                        {
                            "entry_time": idx,
                            "entry_price": row["close"],
                            "direction": "多头" if signal == 1 else "空头",
                        }
                    )
                position = signal

            ret = row["returns"] * position
            equity_curve.append(equity_curve[-1] * np.exp(ret))

        equity_curve = np.array(equity_curve)
        daily_returns = np.diff(np.log(equity_curve))

        total_return = equity_curve[-1] - 1
        annualized_return = (equity_curve[-1]) ** (252 / len(df)) - 1 if len(df) > 0 else 0
        volatility = np.std(daily_returns) * np.sqrt(252)
        sharpe = annualized_return / volatility if volatility > 0 else 0
        max_drawdown = self._calculate_max_drawdown(equity_curve)

        wins = [ret for ret in trade_returns if ret > 0]
        win_rate = len(wins) / len(trade_returns) if trade_returns else 0

        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "volatility": volatility,
            "sharpe": sharpe,
            "max_drawdown": max_drawdown,
            "trade_count": len(trade_returns),
            "win_rate": win_rate,
            "trades": positions,
        }

    def _calculate_max_drawdown(self, equity_curve: np.ndarray) -> float:
        peak = equity_curve[0]
        max_dd = 0.0

        for value in equity_curve:
            peak = max(peak, value)
            drawdown = (peak - value) / peak
            max_dd = max(max_dd, drawdown)
        return max_dd

    def _display_results(self, results: dict) -> None:
        text = [
            "回测结果",
            "=========================",
            f"总收益: {results['total_return'] * 100:.2f}%",
            f"年化收益: {results['annualized_return'] * 100:.2f}%",
            f"波动率: {results['volatility'] * 100:.2f}%",
            f"夏普比率: {results['sharpe']:.2f}",
            f"最大回撤: {results['max_drawdown'] * 100:.2f}%",
            f"交易次数: {results['trade_count']}",
            f"胜率: {results['win_rate'] * 100:.2f}%",
            "",
        ]

        if results["trades"]:
            text.append("交易明细（最近10笔）：")
            for trade in results["trades"][-10:]:
                trade_text = (
                    f"- {trade['direction']} | 入场: {trade['entry_time']} @ {trade['entry_price']:.2f}"
                )
                if "exit_time" in trade:
                    trade_text += f" | 离场: {trade['exit_time']} @ {trade['exit_price']:.2f} | 收益: {trade.get('pnl', 0) * 100:.2f}%"
                text.append(trade_text)
        else:
            text.append("未触发任何交易。请调整阈值或使用更长的数据样本。")

        self.results_text.setPlainText("\n".join(text))
