from dataclasses import dataclass
from typing import Dict
from datetime import datetime

import numpy as np


@dataclass
class TradingSignal:
    timestamp: datetime
    regime: str
    action: str
    probability: float
    entry: float
    stop_loss: float
    take_profit: float


class SignalGenerator:
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
    
    def generate_signal(self, predictions: np.ndarray, price: float, atr: float) -> TradingSignal:
        proba = predictions / predictions.sum()
        classes = ['LONG', 'SHORT', 'FLAT']
        idx = np.argmax(proba)
        action = classes[idx]
        
        if proba[idx] < self.threshold:
            action = 'FLAT'
        
        entry = price
        stop_loss = price - atr * 1.5 if action == 'LONG' else price + atr * 1.5
        take_profit = price + atr * 2.5 if action == 'LONG' else price - atr * 2.5
        
        return TradingSignal(
            timestamp=datetime.now(),
            regime='Bullish Trend' if action == 'LONG' else 'Bearish Trend',
            action=action,
            probability=float(proba[idx]),
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
