import pandas as pd
import numpy as np


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    
    for col in ['open', 'high', 'low', 'close']:
        if col in normalized.columns:
            normalized[col] = (normalized[col] - normalized[col].mean()) / normalized[col].std()
    
    return normalized


def create_sequences(data: np.ndarray, window_size: int = 128) -> np.ndarray:
    sequences = []
    
    for i in range(len(data) - window_size + 1):
        sequences.append(data[i:i+window_size])
    
    return np.array(sequences)
