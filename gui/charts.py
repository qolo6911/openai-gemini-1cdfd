from typing import List
import matplotlib.pyplot as plt


def plot_equity_curve(equity: List[float]):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(equity, color='green', linewidth=2)
    ax.set_title('Equity Curve')
    ax.set_xlabel('Trade')
    ax.set_ylabel('Account Value')
    ax.grid(True)
    return fig
