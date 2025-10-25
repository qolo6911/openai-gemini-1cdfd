import torch


def compute_accuracy(outputs: torch.Tensor, targets: torch.Tensor) -> float:
    _, predicted = torch.max(outputs, 1)
    correct = (predicted == targets).sum().item()
    total = targets.size(0)
    return correct / total if total > 0 else 0.0


def compute_sharpe_ratio(returns, risk_free_rate=0.0):
    import numpy as np
    excess_returns = returns - risk_free_rate
    if len(excess_returns) == 0 or np.std(excess_returns) == 0:
        return 0.0
    return np.mean(excess_returns) / np.std(excess_returns)
