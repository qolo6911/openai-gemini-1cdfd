from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods: int = 252) -> float:
    excess = returns - risk_free_rate / periods
    if excess.std() == 0:
        return 0.0
    return float(np.sqrt(periods) * excess.mean() / excess.std())


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    cummax = equity_curve.cummax()
    drawdown = (equity_curve - cummax) / cummax
    return float(drawdown.min())


def calculate_win_rate(pnl_series: pd.Series) -> float:
    trades = pnl_series[pnl_series != 0]
    if len(trades) == 0:
        return 0.0
    return float((trades > 0).sum() / len(trades))


def generate_performance_report(df: pd.DataFrame) -> dict:
    equity = df["equity"]
    returns = df["returns"]

    initial_balance = equity.iloc[0] if len(equity) > 0 else 0.0
    final_balance = equity.iloc[-1] if len(equity) > 0 else initial_balance

    total_return = (final_balance - initial_balance) / initial_balance if initial_balance != 0 else 0.0

    return {
        "initial_balance": float(initial_balance),
        "final_balance": float(final_balance),
        "total_return": float(total_return),
        "sharpe_ratio": calculate_sharpe_ratio(returns),
        "max_drawdown": calculate_max_drawdown(equity),
        "win_rate": calculate_win_rate(df.get("expected_profit", pd.Series([]))),
        "total_trades": int((df["position"] != 0).sum()),
    }
