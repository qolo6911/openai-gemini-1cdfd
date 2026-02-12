"""Triple-barrier labeling method for supervised training."""
from __future__ import annotations

import numpy as np
import pandas as pd


def apply_triple_barrier(
    df: pd.DataFrame,
    profit_target: float = 0.005,
    stop_loss: float = 0.003,
    forward_window: int = 50,
) -> pd.Series:
    close_prices = df["close"].values
    labels = []

    for i in range(len(close_prices) - forward_window):
        entry_price = close_prices[i]
        future_prices = close_prices[i + 1 : i + 1 + forward_window]

        upper_barrier = entry_price * (1 + profit_target)
        lower_barrier = entry_price * (1 - stop_loss)

        label = 1

        for price in future_prices:
            if price >= upper_barrier:
                label = 2
                break
            elif price <= lower_barrier:
                label = 0
                break

        labels.append(label)

    labels += [1] * forward_window
    return pd.Series(labels, index=df.index, name="label")
