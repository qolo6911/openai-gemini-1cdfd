"""Application entry point for the XAUUSD AI Trading System GUI."""
from __future__ import annotations

import os
import pathlib
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from gui.main_window import MainWindow
from utils.config_manager import ConfigManager
from utils.logger import configure_logging, get_logger


def resolve_resource_path(name: str) -> str:
    """Resolve icon and stylesheet paths when running from PyInstaller bundle."""
    base_path = getattr(sys, "_MEIPASS", pathlib.Path(__file__).resolve().parent)
    return str(pathlib.Path(base_path) / name)


def apply_stylesheet(app: QApplication) -> None:
    qss_path = resolve_resource_path("gui/styles.qss")
    if not os.path.exists(qss_path):
        return
    with open(qss_path, "r", encoding="utf-8") as handle:
        app.setStyleSheet(handle.read())


def main() -> int:
    ConfigManager().ensure_initialized()
    configure_logging()
    logger = get_logger(__name__)
    logger.info("Starting XAUUSD AI Trading System GUI")

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resolve_resource_path("icon.ico")))
    apply_stylesheet(app)

    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
