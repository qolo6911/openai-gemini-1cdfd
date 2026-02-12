"""Application-wide logging helpers."""
from __future__ import annotations

import logging
import pathlib
from logging.handlers import RotatingFileHandler

_LOGGER_NAME = "xauusd_trading"
_LOG_DIR = pathlib.Path.home() / ".xauusd_trading"
_LOG_FILE = _LOG_DIR / "application.log"


def configure_logging(level: int = logging.INFO) -> None:
    if logging.getLogger(_LOGGER_NAME).handlers:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(_LOG_FILE, maxBytes=2_000_000, backupCount=3)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger(_LOGGER_NAME)
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{_LOGGER_NAME}.{name}")
