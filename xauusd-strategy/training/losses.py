from __future__ import annotations

from typing import Iterable, Optional

import torch
import torch.nn as nn


def create_cross_entropy_loss(class_weights: Optional[Iterable[float]] = None) -> nn.Module:
    if class_weights is not None:
        weight_tensor = torch.tensor(class_weights, dtype=torch.float32)
    else:
        weight_tensor = None
    return nn.CrossEntropyLoss(weight=weight_tensor)
