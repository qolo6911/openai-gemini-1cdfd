from __future__ import annotations

from typing import Iterable

import pandas as pd
import ta


def add_ema_features(df: pd.DataFrame, periods: Iterable[int], price_col: str = "close", prefix: str = "ema") -> pd.DataFrame:
    df = df.copy()
    for period in periods:
        df[f"{prefix}_{period}"] = ta.trend.ema_indicator(close=df[price_col], window=period)
    return df


def add_atr(df: pd.DataFrame, window: int = 14, high: str = "high", low: str = "low", close: str = "close", prefix: str = "atr") -> pd.DataFrame:
    df = df.copy()
    df[f"{prefix}_{window}"] = ta.volatility.average_true_range(high=df[high], low=df[low], close=df[close], window=window)
    return df


def add_rsi(df: pd.DataFrame, window: int = 14, price_col: str = "close", prefix: str = "rsi") -> pd.DataFrame:
    df = df.copy()
    df[f"{prefix}_{window}"] = ta.momentum.rsi(close=df[price_col], window=window)
    return df


def add_pct_change(df: pd.DataFrame, column: str, periods: int, new_col: str) -> pd.DataFrame:
    df = df.copy()
    df[new_col] = df[column].pct_change(periods)
    return df
