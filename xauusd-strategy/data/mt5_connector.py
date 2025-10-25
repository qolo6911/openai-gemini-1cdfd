from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd

try:  # pragma: no cover - MetaTrader5 might be unavailable in CI
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - allow importing without MT5 installed
    mt5 = None


@dataclass
class MT5Credentials:
    login: Optional[int] = None
    password: Optional[str] = None
    server: Optional[str] = None


class MT5DataConnector:
    """Wrapper around MetaTrader5 that exposes convenience helpers for OHLCV data."""

    def __init__(self, symbol: str = "XAUUSD") -> None:
        self.symbol = symbol

    def connect(self, credentials: Optional[MT5Credentials] = None) -> None:
        """Initialise the MT5 terminal connection."""

        if mt5 is None:
            raise RuntimeError(
                "MetaTrader5 package is not available. Install it or run inside an MT5-enabled environment."
            )

        if not mt5.initialize():
            raise RuntimeError(f"MT5 initialization failed: {mt5.last_error()}")

        if credentials:
            if not mt5.login(credentials.login, credentials.password, credentials.server):
                raise RuntimeError(f"Login failed: {mt5.last_error()}")

    def shutdown(self) -> None:
        """Shutdown the MT5 connection."""

        if mt5 is not None:
            mt5.shutdown()

    def fetch_data(self, timeframe: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch OHLCV data from MT5 for the given timeframe."""

        if mt5 is None:
            raise RuntimeError(
                "MetaTrader5 package is not available. Install it or run inside an MT5-enabled environment."
            )

        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }

        if timeframe not in tf_map:
            raise ValueError(f"Unsupported timeframe '{timeframe}'. Supported: {list(tf_map)}")

        rates = mt5.copy_rates_range(self.symbol, tf_map[timeframe], start_date, end_date)
        if rates is None:
            raise RuntimeError(f"Failed to fetch data: {mt5.last_error()}")

        df = pd.DataFrame(rates)
        if df.empty:
            raise RuntimeError("No MT5 data returned for the requested parameters.")

        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)
        return df[["open", "high", "low", "close", "tick_volume"]]

    def get_symbol_info(self) -> dict:
        if mt5 is None:
            raise RuntimeError(
                "MetaTrader5 package is not available. Install it or run inside an MT5-enabled environment."
            )

        info = mt5.symbol_info(self.symbol)
        if info is None:
            raise RuntimeError(f"Failed to fetch symbol info: {mt5.last_error()}")

        return {
            "point": info.point,
            "digits": info.digits,
            "trade_contract_size": info.trade_contract_size,
            "volume_min": info.volume_min,
            "volume_step": info.volume_step,
        }
