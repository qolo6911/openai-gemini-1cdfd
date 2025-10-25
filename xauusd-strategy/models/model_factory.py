from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

import torch.nn as nn

from .tcn import TCNModel

ModelType = Literal["tcn"]


@dataclass
class ModelConfig:
    type: ModelType = "tcn"
    num_channels: Sequence[int] = (64, 128, 256)
    kernel_size: int = 3
    dropout: float = 0.2
    num_classes: int = 3


def create_model(num_inputs: int, config: ModelConfig) -> nn.Module:
    if config.type == "tcn":
        return TCNModel(
            num_inputs=num_inputs,
            num_channels=config.num_channels,
            num_classes=config.num_classes,
            kernel_size=config.kernel_size,
            dropout=config.dropout,
        )

    raise ValueError(f"Unsupported model type: {config.type}")
