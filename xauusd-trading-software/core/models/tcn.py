"""Temporal Convolution Network model for multivariate time-series classification."""
from __future__ import annotations

import torch
from torch import nn


class DepthwiseSeparableConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int, dilation: int):
        super().__init__()
        padding = (kernel_size - 1) * dilation
        self.depthwise = nn.Conv1d(
            in_channels,
            in_channels,
            kernel_size,
            padding=padding,
            dilation=dilation,
            groups=in_channels,
        )
        self.pointwise = nn.Conv1d(in_channels, out_channels, kernel_size=1)
        self.init_weights()

    def init_weights(self) -> None:
        nn.init.kaiming_normal_(self.depthwise.weight, nonlinearity="relu")
        nn.init.constant_(self.depthwise.bias, 0)
        nn.init.kaiming_normal_(self.pointwise.weight, nonlinearity="relu")
        nn.init.constant_(self.pointwise.bias, 0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.depthwise(x)
        out = self.pointwise(out)
        return out[..., :-self.depthwise.padding[0]]


class ResidualBlock(nn.Module):
    def __init__(self, channels: int, kernel_size: int, dilation: int, dropout: float = 0.1):
        super().__init__()
        self.conv = DepthwiseSeparableConv(channels, channels, kernel_size, dilation)
        self.norm = nn.BatchNorm1d(channels)
        self.activation = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        out = self.conv(x)
        out = self.norm(out)
        out = self.activation(out)
        out = self.dropout(out)
        out += residual[..., -out.shape[-1] :]
        return out


class TCNModel(nn.Module):
    def __init__(
        self,
        num_inputs: int,
        hidden_channels: int = 256,
        num_layers: int = 5,
        kernel_size: int = 3,
        num_classes: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.input_projection = nn.Conv1d(num_inputs, hidden_channels, kernel_size=1)
        layers = []
        for i in range(num_layers):
            dilation = 2**i
            layers.append(ResidualBlock(hidden_channels, kernel_size, dilation, dropout))
        self.network = nn.Sequential(*layers)
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Linear(hidden_channels, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, features)
        x = x.transpose(1, 2)
        x = self.input_projection(x)
        x = self.network(x)
        x = self.global_pool(x).squeeze(-1)
        return self.fc(x)
