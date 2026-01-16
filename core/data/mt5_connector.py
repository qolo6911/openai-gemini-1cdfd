from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - MetaTrader5 only available on Windows
    mt5 = None


def _generate_dummy_data(timeframe: str, bars: int = 500) -> pd.DataFrame:
    now = datetime.now()
    if timeframe == 'M15':
        delta = timedelta(minutes=15)
    elif timeframe == 'H1':
        delta = timedelta(hours=1)
    else:
        delta = timedelta(hours=4)
    
    times = [now - i * delta for i in range(bars)][::-1]
    prices = pd.Series(range(bars), dtype=float).rolling(window=5, min_periods=1).mean()
    base = 2000 + prices
    
    df = pd.DataFrame({
        'time': times,
        'open': base + pd.Series(range(bars)) * 0.1,
        'high': base + 1.0,
        'low': base - 1.0,
        'close': base + pd.Series(range(bars)) * 0.05,
        'tick_volume': 100,
    })
    df.set_index('time', inplace=True)
    return df


@dataclass
class MT5ConnectionSettings:
    server: str
    login: str
    password: str
    symbol: str = 'XAUUSD'


class MT5DataConnector:
    def __init__(self, settings: Optional[MT5ConnectionSettings] = None):
        self.settings = settings
    
    def initialize(self) -> bool:
        if mt5 is None:
            return False
        
        if self.settings:
            return mt5.initialize(
                server=self.settings.server,
                login=int(self.settings.login) if self.settings.login else None,
                password=self.settings.password
            )
        return mt5.initialize()
    
    def shutdown(self):
        if mt5:
            mt5.shutdown()
    
    def fetch_data(self, timeframe: str = 'M15', bars: int = 500) -> pd.DataFrame:
        if mt5 is None:
            return _generate_dummy_data(timeframe, bars)
        
        timeframe_map = {
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
        }
        tf = timeframe_map.get(timeframe, mt5.TIMEFRAME_M15)
        
        rates = mt5.copy_rates_from_pos(
            self.settings.symbol if self.settings else 'XAUUSD',
            tf,
            0,
            bars
        )
        
        if rates is None:
            return _generate_dummy_data(timeframe, bars)
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df
    
    def fetch_latest_data(self, timeframe: str = 'M15', bars: int = 100) -> pd.DataFrame:
        return self.fetch_data(timeframe, bars)
