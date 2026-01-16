import torch.nn as nn


class CostAdjustedCrossEntropy(nn.Module):
    def __init__(self, cost_matrix=None):
        super().__init__()
        self.ce = nn.CrossEntropyLoss()
        self.cost_matrix = cost_matrix
    
    def forward(self, inputs, targets):
        return self.ce(inputs, targets)
