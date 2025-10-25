from dataclasses import dataclass
from typing import Dict

import pandas as pd

from core.features.indicators import calculate_ema


@dataclass
class RegimeResult:
    timeframe: str
    regime: str
    ema: float
    price: float


class RegimeDetector:
    def __init__(self, ema_period: int = 21):
        self.ema_period = ema_period
    
    def detect(self, df: pd.DataFrame) -> Dict[str, RegimeResult]:
        ema = calculate_ema(df['close'], self.ema_period)
        latest_price = df['close'].iloc[-1]
        latest_ema = ema.iloc[-1]
        
        if latest_price > latest_ema * 1.002:
            regime = 'Bullish Trend'
        elif latest_price < latest_ema * 0.998:
            regime = 'Bearish Trend'
        else:
            regime = 'Consolidation'
        
        return {
            'regime': RegimeResult(
                timeframe='M15',
                regime=regime,
                ema=latest_ema,
                price=latest_price
            )
        }
