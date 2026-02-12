"""Indicator calculations used by the strategy and training pipeline."""
from __future__ import annotations

import numpy as np
import pandas as pd
from ta.volatility import AverageTrueRange
from ta.trend import EMAIndicator


def add_ema(df: pd.DataFrame, period: int = 21) -> pd.DataFrame:
    ema = EMAIndicator(close=df["close"], window=period).ema_indicator()
    df[f"ema_{period}"] = ema
    return df


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    atr_indicator = AverageTrueRange(
        high=df["high"], low=df["low"], close=df["close"], window=period
    )
    df[f"atr_{period}"] = atr_indicator.average_true_range()
    return df


def compute_regime(df: pd.DataFrame, ema_period: int = 21) -> pd.Series:
    price = df["close"]
    ema = df[f"ema_{ema_period}"]
    regime = np.where(price > ema * 1.001, 1, np.where(price < ema * 0.999, -1, 0))
    return pd.Series(regime, index=df.index, name="regime")


def compute_returns(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change().fillna(0.0)


def prepare_features(
    df: pd.DataFrame, ema_period: int = 21, atr_period: int = 14
) -> pd.DataFrame:
    df = add_ema(df, ema_period)
    df = add_atr(df, atr_period)
    df["regime"] = compute_regime(df, ema_period)
    df["returns"] = compute_returns(df)

    df["volatility"] = df["returns"].rolling(window=atr_period).std().fillna(0.0)
    df["spread"] = df["high"] - df["low"]
    df["momentum"] = df["close"].diff().fillna(0.0)
    df["rolling_mean"] = df["close"].rolling(window=ema_period).mean().fillna(method="bfill")
    df["rolling_std"] = df["close"].rolling(window=ema_period).std().fillna(method="bfill")
    return df.dropna()
