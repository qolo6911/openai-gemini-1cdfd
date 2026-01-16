from __future__ import annotations

import pandas as pd
from sklearn.preprocessing import StandardScaler


class DataPreprocessor:
    """Data cleaning and preprocessing pipeline."""

    def __init__(self) -> None:
        self.scaler = StandardScaler()

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicates, handle missing values."""

        df = df.copy()
        df = df[~df.index.duplicated(keep="first")]
        df = df.sort_index()

        initial_len = len(df)
        df = df.dropna()
        dropped = initial_len - len(df)
        if dropped > 0:
            print(f"Dropped {dropped} rows with missing values.")

        return df

    def normalize_features(self, df: pd.DataFrame, feature_cols: list[str], fit: bool = True) -> pd.DataFrame:
        """Normalize feature columns using StandardScaler."""

        df = df.copy()
        if fit:
            df[feature_cols] = self.scaler.fit_transform(df[feature_cols])
        else:
            df[feature_cols] = self.scaler.transform(df[feature_cols])

        return df
