import pandas as pd
import numpy as np


def apply_triple_barrier(df: pd.DataFrame, tp_multiplier: float = 1.5, 
                        sl_multiplier: float = 1.0, holding_period: int = 24) -> pd.Series:
    labels = pd.Series(index=df.index, dtype=int)
    
    for i in range(len(df) - holding_period):
        future_returns = df['close'].iloc[i+1:i+1+holding_period] - df['close'].iloc[i]
        
        if len(future_returns) == 0:
            labels.iloc[i] = 2
            continue
        
        max_return = future_returns.max()
        min_return = future_returns.min()
        
        threshold = df.get('atr', pd.Series([1.0]*len(df))).iloc[i]
        tp_threshold = tp_multiplier * threshold
        sl_threshold = -sl_multiplier * threshold
        
        if max_return >= tp_threshold:
            labels.iloc[i] = 0
        elif min_return <= sl_threshold:
            labels.iloc[i] = 1
        else:
            labels.iloc[i] = 2
    
    return labels
