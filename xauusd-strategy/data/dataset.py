from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

LABEL_MAP = {"flat": 0, "long": 1, "short": 2}


@dataclass
class SequenceConfig:
    lookback: int = 128


class TimeSeriesDataset(Dataset):
    """Create sliding window sequences suitable for convolutional models."""

    def __init__(self, df: pd.DataFrame, feature_cols: list[str], label_col: str, config: SequenceConfig) -> None:
        if df.index.is_monotonic_increasing is False:
            df = df.sort_index()

        self.df = df
        self.feature_cols = feature_cols
        self.label_col = label_col
        self.lookback = config.lookback

        self._build_arrays()

    def _build_arrays(self) -> None:
        sequences = []
        labels = []

        data = self.df[self.feature_cols].values
        label_series = self.df[self.label_col].map(LABEL_MAP).values

        for idx in range(self.lookback, len(self.df)):
            window = data[idx - self.lookback : idx]
            sequences.append(window)
            labels.append(label_series[idx])

        X = np.stack(sequences) if sequences else np.empty((0, self.lookback, len(self.feature_cols)))
        y = np.array(labels, dtype=np.int64)

        # Reshape to (batch, features, seq_len)
        X = np.transpose(X, (0, 2, 1))

        self.X = torch.FloatTensor(X)
        self.y = torch.LongTensor(y)

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]
