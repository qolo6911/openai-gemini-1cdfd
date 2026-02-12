"""MetaTrader 5 connection and data retrieval."""
from __future__ import annotations

from typing import Literal

import MetaTrader5 as mt5
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


class MT5Connector:
    def __init__(self) -> None:
        self.connected = False

    def connect(self, login: int, password: str, server: str) -> bool:
        if not mt5.initialize():
            logger.error(f"MT5 initialization failed: {mt5.last_error()}")
            return False

        if not mt5.login(login=login, password=password, server=server):
            logger.error(f"MT5 login failed: {mt5.last_error()}")
            mt5.shutdown()
            return False

        account_info = mt5.account_info()
        if account_info is None:
            logger.error("Failed to retrieve account info")
            mt5.shutdown()
            return False

        logger.info(f"Connected to MT5 | Account: {account_info.login} | Balance: {account_info.balance}")
        self.connected = True
        return True

    def disconnect(self) -> None:
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")

    def fetch_data(
        self,
        symbol: str = "XAUUSD",
        timeframe: Literal["M15", "H1", "H4"] = "M15",
        bars: int = 1000,
    ) -> pd.DataFrame | None:
        if not self.connected:
            logger.error("Not connected to MT5")
            return None

        timeframe_map = {
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
        }

        rates = mt5.copy_rates_from_pos(symbol, timeframe_map[timeframe], 0, bars)
        if rates is None or len(rates) == 0:
            logger.error(f"Failed to fetch data: {mt5.last_error()}")
            return None

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df = df.set_index("time")
        logger.info(f"Fetched {len(df)} bars of {symbol} {timeframe} data")
        return df

    def get_current_price(self, symbol: str = "XAUUSD") -> dict | None:
        if not self.connected:
            logger.error("Not connected to MT5")
            return None

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"Failed to get tick for {symbol}")
            return None

        return {"bid": tick.bid, "ask": tick.ask, "spread": tick.ask - tick.bid}

    def place_order(
        self,
        symbol: str,
        order_type: Literal["buy", "sell"],
        volume: float,
        sl: float | None = None,
        tp: float | None = None,
    ) -> bool:
        if not self.connected:
            logger.error("Not connected to MT5")
            return False

        price_info = self.get_current_price(symbol)
        if price_info is None:
            return False

        price = price_info["ask"] if order_type == "buy" else price_info["bid"]
        mt5_order_type = mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": price,
            "deviation": 10,
            "magic": 234000,
            "comment": "XAUUSD AI Trading",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: {result.retcode} - {result.comment}")
            return False

        logger.info(f"Order placed: {order_type.upper()} {volume} {symbol} @ {price}")
        return True

    def get_positions(self, symbol: str = "XAUUSD") -> list[dict]:
        if not self.connected:
            return []

        positions = mt5.positions_get(symbol=symbol)
        if positions is None or len(positions) == 0:
            return []

        return [
            {
                "ticket": pos.ticket,
                "type": "buy" if pos.type == mt5.ORDER_TYPE_BUY else "sell",
                "volume": pos.volume,
                "price_open": pos.price_open,
                "price_current": pos.price_current,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit,
            }
            for pos in positions
        ]
