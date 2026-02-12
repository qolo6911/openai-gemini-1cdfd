"""Configuration manager for storing and retrieving user settings."""
from __future__ import annotations

import json
import pathlib
from typing import Any


class ConfigManager:
    _instance = None
    _config_path = pathlib.Path.home() / ".xauusd_trading" / "config.json"

    def __new__(cls) -> ConfigManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = {}
        return cls._instance

    def ensure_initialized(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        if self._config_path.exists():
            self.load()
        else:
            self._config = self._default_config()
            self.save()

    def _default_config(self) -> dict[str, Any]:
        return {
            "mt5": {
                "login": 0,
                "password": "",
                "server": "",
            },
            "strategy": {
                "spread_points": 16,
                "lot_size": 0.1,
                "ema_period": 21,
                "atr_period": 14,
                "atr_sl_multiplier": 2.0,
                "atr_tp_multiplier": 3.0,
                "oscillation_threshold": 0.3,
            },
            "model": {
                "input_features": 20,
                "hidden_channels": 256,
                "num_classes": 3,
                "learning_rate": 0.001,
                "batch_size": 64,
                "epochs": 100,
            },
        }

    def load(self) -> None:
        with open(self._config_path, "r", encoding="utf-8") as handle:
            self._config = json.load(handle)

    def save(self) -> None:
        with open(self._config_path, "w", encoding="utf-8") as handle:
            json.dump(self._config, handle, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        keys = key.split(".")
        target = self._config
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value
        self.save()
