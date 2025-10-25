from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd


@dataclass
class RiskParameters:
    atr_tp: float
    atr_sl: float
    risk_per_trade: float
    contract_size: float = 100.0


class BacktestEngine:
    """Simple event-driven backtester for labelled signals."""

    def __init__(self, risk: RiskParameters) -> None:
        self.risk = risk

    def _position_size(self, atr: float, balance: float) -> float:
        dollar_risk = balance * self.risk.risk_per_trade
        pip_risk = self.risk.atr_sl * atr
        if pip_risk == 0:
            return 0.0
        return max(dollar_risk / pip_risk, 0.0)

    def run(self, df: pd.DataFrame, initial_balance: float = 100_000.0) -> pd.DataFrame:
        balance = initial_balance
        equity_curve: List[float] = []
        positions: List[int] = []

        for _idx, row in df.iterrows():
            atr = row.get("atr_m15", 0.0)
            signal = row.get("signal", "flat")
            expected_profit = row.get("expected_profit", 0.0)

            position = 0
            if signal == "long":
                position = 1
            elif signal == "short":
                position = -1

            size = self._position_size(atr, balance)
            pnl = size * expected_profit

            balance += pnl

            equity_curve.append(balance)
            positions.append(position)

        result = df.copy()
        result["equity"] = equity_curve
        result["position"] = positions
        result["returns"] = pd.Series(result["equity"]).pct_change().fillna(0.0)
        return result
