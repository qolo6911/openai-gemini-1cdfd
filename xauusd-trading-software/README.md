# XAUUSD AI Trading System

A desktop trading assistant for XAUUSD (Gold) featuring strategy configuration, deep-learning powered modelling, historical backtests, live execution, and real-time monitoring through a PyQt5 graphical interface.

> **Note**: The provided codebase and build scripts allow you to prepare the Windows `.exe` application using PyInstaller on a Windows machine with the required dependencies installed. The binary itself is not distributed in the repository.

## Features

- **Trend & Range Detection**: EMA21-based regime detection across H1 and H4.
- **Execution**: Mean-reversion trading on M15 with ATR-based dynamic SL/TP.
- **Model Training**: Temporal Convolution Network (TCN) with GPU acceleration (when available) and a live training progress chart.
- **Backtesting**: (Under development) placeholder ready for integration with historical performance evaluation.
- **Live Trading**: MT5 execution panel, live position monitoring, and configurable risk parameters.
- **Monitoring**: Real-time candlestick chart of XAUUSD with EMA overlay.
- **Logging**: Centralised log viewer within the GUI plus rotating application logs written to `~/.xauusd_trading/application.log`.

## Project Structure

```
xauusd-trading-software/
├── main.py
├── requirements.txt
├── build_exe.spec
├── icon.ico
├── gui/
│   ├── main_window.py
│   ├── config_tab.py
│   ├── training_tab.py
│   ├── backtest_tab.py
│   ├── live_tab.py
│   ├── monitor_tab.py
│   ├── log_tab.py
│   └── styles.qss
├── core/
│   ├── data/
│   │   └── mt5_connector.py
│   ├── features/
│   │   └── indicators.py
│   ├── labeling/
│   │   └── triple_barrier.py
│   ├── models/
│   │   └── tcn.py
│   ├── training/
│   │   └── trainer.py
│   └── live/
│       └── executor.py
└── utils/
    ├── config_manager.py
    └── logger.py
```

## Requirements

Install the Python dependencies (Python 3.10+ recommended):

```
pip install -r requirements.txt
```

Key packages:
- PyQt5
- torch (with GPU support when available)
- MetaTrader5 SDK
- pandas, numpy
- matplotlib, ta
- pyinstaller

Ensure the MetaTrader5 terminal is installed on the machine, and a valid trading account is accessible.

## Running the Application

1. Configure the MT5 credentials and strategy parameters in the GUI.
2. Load historical data (CSV) for training, or connect directly to MT5 for live monitoring/execution.
3. Use the corresponding tabs for training, backtesting, live trading control, monitoring, and log review.

```
python main.py
```

Configuration files and trained models are stored in the user's home directory under `~/.xauusd_trading/`.

## Building the Windows Executable

> PyInstaller must be run on Windows to produce a Windows executable. Running on other operating systems is not supported.

```
# 1. Install dependencies
pip install -r requirements.txt

# 2. Build executable
pyinstaller build_exe.spec

# 3. Output will be available at
#    dist/XAUUSD_Trading_System/XAUUSD_Trading_System.exe
```

Confirm the resulting `.exe` file size is below 300 MB before distribution.

## Icon

Replace `icon.ico` with your preferred application icon before packaging. The placeholder icon should be a valid `.ico` file.

## Logging

Runtime logs are written to `~/.xauusd_trading/application.log`. Use the "🧾 日志" tab inside the GUI for quick access.

## Disclaimer

This software provides tooling for strategy research and automated execution. Ensure you comply with local regulations and thoroughly test strategies with demo accounts before trading live capital.
