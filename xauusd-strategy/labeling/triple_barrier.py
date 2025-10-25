from __future__ import annotations

import numpy as np
import pandas as pd


class TripleBarrierLabeler:
    def __init__(
        self,
        k1_tp: float = 1.5,
        k2_sl: float = 1.0,
        holding_period: int = 24,
        spread_points: int = 16,
        point_value: float = 0.01,
        slippage: float = 0.0,
    ) -> None:
        self.k1_tp = k1_tp
        self.k2_sl = k2_sl
        self.holding_period = holding_period
        self.spread_cost = spread_points * point_value + slippage

    def label_sample(self, df: pd.DataFrame, idx: int) -> tuple[str, float]:
        if idx + self.holding_period >= len(df):
            return "flat", 0.0

        current_price = df.iloc[idx]["close"]
        current_atr = df.iloc[idx]["atr_m15"]
        regime = df.iloc[idx]["regime"]

        tp_long = current_price + self.k1_tp * current_atr
        sl_long = current_price - self.k2_sl * current_atr
        tp_short = current_price - self.k1_tp * current_atr
        sl_short = current_price + self.k2_sl * current_atr

        future_prices = df.iloc[idx + 1 : idx + 1 + self.holding_period]["close"].values

        long_profit = None
        for price in future_prices:
            if price >= tp_long:
                long_profit = self.k1_tp * current_atr - self.spread_cost
                break
            if price <= sl_long:
                long_profit = -self.k2_sl * current_atr - self.spread_cost
                break
        if long_profit is None:
            long_profit = future_prices[-1] - current_price - self.spread_cost

        short_profit = None
        for price in future_prices:
            if price <= tp_short:
                short_profit = self.k1_tp * current_atr - self.spread_cost
                break
            if price >= sl_short:
                short_profit = -self.k2_sl * current_atr - self.spread_cost
                break
        if short_profit is None:
            short_profit = current_price - future_prices[-1] - self.spread_cost

        if regime == "bullish":
            if long_profit > 0:
                return "long", float(long_profit)
            return "flat", 0.0
        if regime == "bearish":
            if short_profit > 0:
                return "short", float(short_profit)
            return "flat", 0.0

        if regime == "consolidation":
            if long_profit > short_profit and long_profit > 0:
                return "long", float(long_profit)
            if short_profit > 0:
                return "short", float(short_profit)

        return "flat", 0.0

    def label_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        labels = []
        profits = []

        for idx in range(len(df) - self.holding_period):
            label, profit = self.label_sample(df, idx)
            labels.append(label)
            profits.append(profit)

        labels.extend(["flat"] * self.holding_period)
        profits.extend([0.0] * self.holding_period)

        df = df.copy()
        df["label"] = labels
        df["expected_profit"] = profits

        return df
