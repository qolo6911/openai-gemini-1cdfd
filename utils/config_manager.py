import json
import os
from dataclasses import dataclass, asdict, field
from typing import Any, Dict

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')
CONFIG_PATH = os.path.abspath(CONFIG_PATH)


@dataclass
class MT5Config:
    server: str = ""
    login: str = ""
    password: str = ""
    symbol: str = "XAUUSD"


@dataclass
class StrategyConfig:
    ema_period: int = 21
    atr_period: int = 14
    tp_multiplier: float = 1.5
    sl_multiplier: float = 1.0
    spread: float = 16.0
    holding_period: int = 24


@dataclass
class RiskConfig:
    risk_per_trade: float = 0.5
    max_daily_loss: float = 2.0
    max_positions: int = 3


@dataclass
class ModelConfig:
    window_size: int = 128
    threshold: float = 0.6
    model_type: str = "TCN"


@dataclass
class AppConfig:
    mt5: MT5Config = field(default_factory=MT5Config)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    model: ModelConfig = field(default_factory=ModelConfig)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'mt5': asdict(self.mt5),
            'strategy': asdict(self.strategy),
            'risk': asdict(self.risk),
            'model': asdict(self.model),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        return cls(
            mt5=MT5Config(**data.get('mt5', {})),
            strategy=StrategyConfig(**data.get('strategy', {})),
            risk=RiskConfig(**data.get('risk', {})),
            model=ModelConfig(**data.get('model', {}))
        )


def load_config() -> AppConfig:
    if not os.path.exists(CONFIG_PATH):
        return AppConfig()
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return AppConfig.from_dict(data)


def save_config(config: AppConfig) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
