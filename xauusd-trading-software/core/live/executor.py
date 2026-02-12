"""Live trading execution logic with ATR-based risk management."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from core.data.mt5_connector import MT5Connector
from core.features.indicators import add_atr
from utils.config_manager import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TradeSignal:
    direction: str  # "long" or "short"
    confidence: float
    entry_price: float
    atr: float


class LiveExecutor:
    def __init__(self, connector: MT5Connector | None = None) -> None:
        self.connector = connector or MT5Connector()
        self.config = ConfigManager()

    def evaluate_signal(self, df: pd.DataFrame) -> Optional[TradeSignal]:
        if df.empty:
            return None

        df = add_atr(df[-100:].copy())
        latest = df.iloc[-1]
        atr = latest.get("atr_14", 0.0)

        ema = self.config.get("strategy.ema_period", 21)
        price = latest["close"]
        ema_value = latest.get(f"ema_{ema}")
        spread_points = self.config.get("strategy.spread_points", 16)

        if ema_value is None:
            return None

        if price > ema_value:
            return TradeSignal("long", confidence=0.6, entry_price=price + spread_points * 0.1, atr=atr)
        if price < ema_value:
            return TradeSignal("short", confidence=0.6, entry_price=price - spread_points * 0.1, atr=atr)
        return None

    def execute(self, signal: TradeSignal) -> bool:
        lot_size = self.config.get("strategy.lot_size", 0.1)
        sl_multiplier = self.config.get("strategy.atr_sl_multiplier", 2.0)
        tp_multiplier = self.config.get("strategy.atr_tp_multiplier", 3.0)

        if signal.direction == "long":
            sl = signal.entry_price - sl_multiplier * signal.atr
            tp = signal.entry_price + tp_multiplier * signal.atr
            result = self.connector.place_order("XAUUSD", "buy", lot_size, sl=sl, tp=tp)
        else:
            sl = signal.entry_price + sl_multiplier * signal.atr
            tp = signal.entry_price - tp_multiplier * signal.atr
            result = self.connector.place_order("XAUUSD", "sell", lot_size, sl=sl, tp=tp)

        if result:
            logger.info(
                f"Executed {signal.direction} trade | Entry: {signal.entry_price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}"
            )
        return result
