from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd
import ta


@dataclass
class FeatureConfig:
    ema_periods: Sequence[int]
    atr_window: int = 14
    rsi_window: int = 14
    ema_slope_window: int = 5


class MultiTimeframeFeatures:
    def __init__(self, config: FeatureConfig | None = None) -> None:
        self.config = config or FeatureConfig(ema_periods=(21, 50, 100))

    def calculate_indicators(self, df: pd.DataFrame, timeframe_label: str) -> pd.DataFrame:
        df = df.copy()

        for period in self.config.ema_periods:
            df[f"ema_{period}_{timeframe_label}"] = ta.trend.ema_indicator(df["close"], window=period)

        df[f"atr_{timeframe_label}"] = ta.volatility.average_true_range(
            df["high"], df["low"], df["close"], window=self.config.atr_window
        )

        if 21 in self.config.ema_periods:
            df[f"ema21_dev_{timeframe_label}"] = (
                (df["close"] - df[f"ema_{21}_{timeframe_label}"])
                / df[f"atr_{timeframe_label}"]
            )
            df[f"ema21_slope_{timeframe_label}"] = (
                df[f"ema_{21}_{timeframe_label}"].pct_change(self.config.ema_slope_window)
            )
            df[f"above_ema21_{timeframe_label}"] = (
                (df["close"] > df[f"ema_{21}_{timeframe_label}"]).astype(int)
            )

        df[f"rsi_{timeframe_label}"] = ta.momentum.rsi(df["close"], window=self.config.rsi_window)

        return df

    def align_to_m15(self, m15_df: pd.DataFrame, h1_df: pd.DataFrame, h4_df: pd.DataFrame) -> pd.DataFrame:
        h1_reindexed = h1_df.reindex(m15_df.index, method="ffill")
        h4_reindexed = h4_df.reindex(m15_df.index, method="ffill")

        result = m15_df.copy()
        result = result.join(h1_reindexed, rsuffix="_h1")
        result = result.join(h4_reindexed, rsuffix="_h4")

        return result

    def detect_regime(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        h1_above = df["above_ema21_h1"] == 1
        h4_above = df["above_ema21_h4"] == 1

        df["regime"] = "consolidation"
        df.loc[h1_above & h4_above, "regime"] = "bullish"
        df.loc[~h1_above & ~h4_above, "regime"] = "bearish"

        return df
