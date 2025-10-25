from typing import Tuple

import numpy as np
import torch
from torch.utils.data import Dataset


class TradingDataset(Dataset):
    def __init__(self, length: int = 1000, sequence_length: int = 128, features: int = 10):
        super().__init__()
        self.sequence_length = sequence_length
        self.features = features
        self.length = length
        
        self.data = np.random.randn(length, features, sequence_length)
        self.targets = np.random.randint(0, 3, size=(length,))
    
    def __len__(self) -> int:
        return self.length
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        x = torch.tensor(self.data[idx], dtype=torch.float32)
        y = torch.tensor(self.targets[idx], dtype=torch.long)
        return x, y
