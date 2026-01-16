from __future__ import annotations

import pandas as pd


class CostAdjustedLabeler:
    """Post-processing for labels that incorporates transaction costs."""

    def __init__(self, min_profit_threshold: float = 0.0) -> None:
        self.min_profit_threshold = min_profit_threshold

    def filter_unprofitable(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        mask = (df["expected_profit"] <= self.min_profit_threshold) & (df["label"] != "flat")
        df.loc[mask, "label"] = "flat"
        df.loc[mask, "expected_profit"] = 0.0

        return df
