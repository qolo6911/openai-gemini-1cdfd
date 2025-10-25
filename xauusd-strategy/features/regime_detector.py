from __future__ import annotations

from typing import Literal

import pandas as pd

REGIME_TYPE = Literal["bullish", "bearish", "consolidation"]


class RegimeDetector:
    """Detect market regime based on H1 and H4 EMA21 alignment."""

    def __init__(self, h1_ema_col: str = "ema_21_h1", h4_ema_col: str = "ema_21_h4", price_col: str = "close") -> None:
        self.h1_ema_col = h1_ema_col
        self.h4_ema_col = h4_ema_col
        self.price_col = price_col

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Regime rules:
        - Bullish: close > EMA21(H1) AND close > EMA21(H4)
        - Bearish: close < EMA21(H1) AND close < EMA21(H4)
        - Consolidation: mixed EMA signals
        """

        df = df.copy()

        h1_above = df[self.price_col] > df[self.h1_ema_col]
        h4_above = df[self.price_col] > df[self.h4_ema_col]

        df["regime"] = "consolidation"
        df.loc[h1_above & h4_above, "regime"] = "bullish"
        df.loc[~h1_above & ~h4_above, "regime"] = "bearish"

        return df
