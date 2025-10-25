import pandas as pd

from core.features.indicators import calculate_ema, calculate_atr, calculate_rsi


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    features = df.copy()
    
    features['ema_21'] = calculate_ema(features['close'], 21)
    features['ema_50'] = calculate_ema(features['close'], 50)
    features['atr_14'] = calculate_atr(features, 14)
    features['rsi_14'] = calculate_rsi(features['close'], 14)
    
    features['returns'] = features['close'].pct_change()
    features['log_returns'] = pd.Series(index=features.index, dtype=float)
    
    features = features.bfill()
    
    return features
