import torch
import torch.nn as nn

from core.models.tcn import TCN


class SimpleTransformerClassifier(nn.Module):
    def __init__(self, input_size: int, sequence_length: int, num_classes: int = 3,
                 num_heads: int = 4, num_layers: int = 2):
        super().__init__()
        self.input_proj = nn.Linear(input_size, 64)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=64,
            nhead=num_heads,
            dim_feedforward=128,
            dropout=0.1,
            batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.classifier = nn.Linear(64, num_classes)
    
    def forward(self, x):
        x = x.transpose(1, 2)
        x = self.input_proj(x)
        x = self.encoder(x)
        x = x.transpose(1, 2)
        x = self.pool(x).squeeze(-1)
        return self.classifier(x)


def create_model(model_type: str, input_size: int, sequence_length: int, num_classes: int = 3,
                 **kwargs) -> nn.Module:
    model_type = model_type.lower()
    
    if model_type == 'tcn':
        channels = kwargs.get('channels', [32, 64, 128])
        return TCN(input_size, channels, kernel_size=kwargs.get('kernel_size', 3),
                   dropout=kwargs.get('dropout', 0.2), num_classes=num_classes)
    elif model_type == 'transformer':
        return SimpleTransformerClassifier(input_size, sequence_length, num_classes,
                                           num_heads=kwargs.get('num_heads', 4),
                                           num_layers=kwargs.get('num_layers', 2))
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
