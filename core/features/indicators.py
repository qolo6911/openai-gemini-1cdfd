import pandas as pd
import numpy as np


def calculate_ema(series: pd.Series, period: int = 21) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_bollinger_bands(series: pd.Series, period: int = 20, std: float = 2.0):
    ma = series.rolling(window=period).mean()
    std_dev = series.rolling(window=period).std()
    
    upper = ma + (std_dev * std)
    lower = ma - (std_dev * std)
    
    return upper, ma, lower
