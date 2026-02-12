# Architecture Documentation

## Overview

The XAUUSD AI Trading System is a desktop application built with PyQt5 that integrates machine learning models (TCN) with live trading through MetaTrader 5. The architecture follows a modular design with clear separation between GUI, core trading logic, and utilities.

## Project Structure

```
xauusd-trading-software/
│
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── build_exe.spec             # PyInstaller configuration
├── icon.ico                   # Application icon
│
├── gui/                       # PyQt5 User Interface
│   ├── main_window.py         # Main window with tab navigation
│   ├── config_tab.py          # MT5 connection & strategy settings
│   ├── training_tab.py        # Model training UI with progress
│   ├── backtest_tab.py        # Historical backtest UI
│   ├── live_tab.py            # Live trading control & monitoring
│   ├── monitor_tab.py         # Real-time chart visualization
│   ├── log_tab.py             # Log viewer
│   └── styles.qss             # Dark theme stylesheet
│
├── core/                      # Core Trading Logic
│   ├── data/
│   │   └── mt5_connector.py   # MT5 API wrapper
│   ├── features/
│   │   └── indicators.py      # Technical indicators (EMA, ATR)
│   ├── labeling/
│   │   └── triple_barrier.py  # Label generation for ML
│   ├── models/
│   │   └── tcn.py             # Temporal Convolution Network
│   ├── training/
│   │   └── trainer.py         # Model training loop
│   └── live/
│       └── executor.py        # Trade execution logic
│
└── utils/                     # Utilities
    ├── config_manager.py      # Persistent configuration
    └── logger.py              # Centralized logging
```

## Core Components

### 1. GUI Layer (`gui/`)

#### Main Window (`main_window.py`)
- Hosts QTabWidget for navigation
- Manages 6 tabs: Config, Training, Backtest, Live, Monitor, Logs

#### Config Tab (`config_tab.py`)
- MT5 connection form (login, password, server)
- Strategy parameters (spread, lot size, EMA/ATR periods, risk multipliers)
- Configuration persistence via ConfigManager

#### Training Tab (`training_tab.py`)
- CSV data loader with validation
- Background training thread (QThread)
- Real-time progress bar and loss chart (Matplotlib)
- Model saved to `~/.xauusd_trading/tcn_model.pth`

#### Live Tab (`live_tab.py`)
- Start/stop live trading
- Position monitoring table
- Transaction log viewer
- 5-second refresh cycle

#### Monitor Tab (`monitor_tab.py`)
- Real-time candlestick chart
- EMA overlay
- 10-second auto-refresh

#### Log Tab (`log_tab.py`)
- Real-time log viewer
- 3-second auto-refresh

### 2. Core Layer (`core/`)

#### MT5 Connector (`core/data/mt5_connector.py`)
- Wraps MetaTrader5 SDK
- Connection management (initialize, login, shutdown)
- Data fetching (M15, H1, H4 timeframes)
- Order placement with SL/TP
- Position retrieval

**Key Methods:**
```python
connect(login, password, server) -> bool
fetch_data(symbol, timeframe, bars) -> pd.DataFrame
place_order(symbol, order_type, volume, sl, tp) -> bool
get_positions(symbol) -> list[dict]
```

#### Indicators (`core/features/indicators.py`)
- EMA calculation (ta library)
- ATR calculation (ta library)
- Regime detection (trend vs. oscillation)
- Feature engineering for ML (returns, volatility, momentum)

**Functions:**
```python
add_ema(df, period) -> pd.DataFrame
add_atr(df, period) -> pd.DataFrame
compute_regime(df, ema_period) -> pd.Series
prepare_features(df, ema_period, atr_period) -> pd.DataFrame
```

#### Triple-Barrier Labeling (`core/labeling/triple_barrier.py`)
- Generates labels for supervised learning
- Labels: 0 (short), 1 (hold), 2 (long)
- Uses profit target and stop loss thresholds

**Function:**
```python
apply_triple_barrier(df, profit_target, stop_loss, forward_window) -> pd.Series
```

#### TCN Model (`core/models/tcn.py`)
- Temporal Convolution Network for time-series classification
- Depthwise separable convolutions
- Residual connections
- Global average pooling
- 3-class output (short, hold, long)

**Architecture:**
```
Input (batch, seq_len, features)
  ↓
Conv1d projection (features -> hidden_channels)
  ↓
5x ResidualBlock (TCN layers with dilation)
  ↓
Global Average Pooling
  ↓
Fully Connected (hidden_channels -> 3 classes)
```

#### Trainer (`core/training/trainer.py`)
- Manages training loop
- Data preparation (sequence windowing, train/val split)
- PyTorch DataLoader integration
- Progress callbacks for GUI updates
- Model checkpointing

**Key Methods:**
```python
prepare_data(df, feature_columns, sequence_length, batch_size) -> (train_loader, val_loader)
train(train_loader, val_loader, epochs, progress_callback)
save_model(path)
load_model(path)
```

#### Live Executor (`core/live/executor.py`)
- Signal evaluation based on EMA
- ATR-based risk management
- Trade execution via MT5Connector
- Spread cost consideration

**Trade Logic:**
```python
if price > EMA: signal = long
if price < EMA: signal = short
SL = entry ± (ATR × sl_multiplier)
TP = entry ± (ATR × tp_multiplier)
```

### 3. Utilities (`utils/`)

#### Config Manager (`utils/config_manager.py`)
- Singleton pattern
- JSON-based persistence
- Nested key access (`"mt5.login"`)
- Default configuration generation
- Stored in `~/.xauusd_trading/config.json`

**Schema:**
```json
{
  "mt5": {"login": 0, "password": "", "server": ""},
  "strategy": {
    "spread_points": 16,
    "lot_size": 0.1,
    "ema_period": 21,
    "atr_period": 14,
    "atr_sl_multiplier": 2.0,
    "atr_tp_multiplier": 3.0
  },
  "model": {
    "input_features": 20,
    "hidden_channels": 256,
    "num_classes": 3,
    "learning_rate": 0.001,
    "batch_size": 64,
    "epochs": 100
  }
}
```

#### Logger (`utils/logger.py`)
- Centralized logging setup
- Rotating file handler (2 MB max, 3 backups)
- Console output
- Stored in `~/.xauusd_trading/application.log`
- Format: `YYYY-MM-DD HH:MM:SS | LEVEL | MODULE | MESSAGE`

## Data Flow

### Training Pipeline
```
CSV File
  ↓
load & validate (training_tab.py)
  ↓
add indicators (indicators.py)
  ↓
label data (triple_barrier.py)
  ↓
sequence windowing (trainer.py)
  ↓
train TCN model (tcn.py)
  ↓
save checkpoint (~/.xauusd_trading/tcn_model.pth)
```

### Live Trading Pipeline
```
MT5 connection (live_tab.py)
  ↓
fetch M15 data (mt5_connector.py)
  ↓
add indicators (indicators.py)
  ↓
evaluate signal (executor.py)
  ↓
calculate SL/TP (executor.py)
  ↓
place order (mt5_connector.py)
  ↓
monitor position (live_tab.py)
```

## Technology Stack

### Frontend
- **PyQt5**: GUI framework
- **Matplotlib**: Chart rendering
- **QSS**: Custom dark theme styling

### Backend
- **PyTorch**: Deep learning framework
- **MetaTrader5**: Trading API
- **pandas**: Data manipulation
- **ta (Technical Analysis)**: Indicator library
- **scikit-learn**: Data splitting

### Packaging
- **PyInstaller**: Windows .exe bundling

## Design Patterns

### 1. Singleton Pattern
- `ConfigManager`: Single instance across application

### 2. Observer Pattern
- Qt Signals/Slots: UI updates from background threads
- `TrainingThread.progress` → `TrainingTab._on_progress`

### 3. Thread Separation
- `TrainingThread`: Runs model training off main thread
- `QTimer`: Periodic refreshes (monitoring, logs)

### 4. Dependency Injection
- `LiveExecutor` accepts `MT5Connector` instance
- Enables testing with mock connectors

## Threading Model

### Main Thread (GUI)
- PyQt5 event loop
- UI rendering
- User interactions

### Worker Threads
- `TrainingThread`: Model training (CPU/GPU intensive)

### Timers (Main Thread)
- Monitor refresh: 10s
- Live position refresh: 5s
- Log refresh: 3s

## Error Handling

### Connection Failures
- MT5 initialization errors → logged + user notification
- Retry mechanism: User must manually reconnect

### Data Validation
- CSV column checks
- Minimum data size requirements
- Empty DataFrame handling

### Training Errors
- Exception caught in `TrainingThread`
- Emitted via `failed` signal
- Displayed in QMessageBox

### Order Failures
- MT5 error codes logged
- User notified via status updates

## Configuration Management

### Persistence
- JSON file: `~/.xauusd_trading/config.json`
- Auto-created on first run
- Updated on "Save" button

### Scope
- User-level (not system-wide)
- Portable across sessions

## Logging Strategy

### Levels
- INFO: Normal operations (connections, trades, refreshes)
- ERROR: Failures (connection errors, order rejections)
- EXCEPTION: Unhandled errors (with traceback)

### Destinations
- File: `~/.xauusd_trading/application.log` (persistent)
- Console: stdout (development)
- GUI: Log tab (real-time viewer)

## Security Considerations

### Password Storage
- Plain text in config.json (⚠️ consider encryption for production)

### API Keys
- MT5 credentials required
- Stored locally (not transmitted externally)

### Network
- MT5 API communication only
- No external data egress

## Performance Optimization

### GPU Acceleration
- PyTorch auto-detects CUDA
- Fallback to CPU if unavailable

### Data Caching
- Config loaded once, cached in singleton
- MT5 data fetched on-demand

### UI Responsiveness
- Training runs in QThread
- Chart updates throttled (10s intervals)

## Future Enhancements

### Backtest Module
- Historical simulation
- Performance metrics (Sharpe ratio, max drawdown)
- Equity curve visualization

### Model Serving
- Load trained model for signal generation
- Real-time prediction integration

### Risk Management
- Position sizing based on account balance
- Maximum drawdown limits
- Daily loss limits

### Multi-Symbol Support
- Trading pairs beyond XAUUSD
- Correlation analysis

### Cloud Deployment
- VPS integration for 24/7 operation
- Remote monitoring dashboard

## Testing Strategy

### Unit Tests
- `core/` modules: indicator calculations, labeling logic
- Mock MT5 connector for order tests

### Integration Tests
- End-to-end training pipeline
- GUI workflow tests (PyQt5 test framework)

### Manual Testing
- Demo account validation
- UI/UX flow verification

## Packaging & Distribution

### PyInstaller Configuration
- `build_exe.spec`: Single-folder bundle
- Includes data files (styles.qss, icon.ico)
- Hidden imports explicitly listed
- Console disabled for production

### Build Process
```bash
pyinstaller build_exe.spec
```

### Output
- `dist/XAUUSD_Trading_System/` folder
- `XAUUSD_Trading_System.exe` entry point
- Supporting DLLs and libraries

### Distribution
- Zip the `dist/XAUUSD_Trading_System/` folder
- Users extract and run .exe
- No Python installation required on target machine

## System Requirements

### Minimum
- Windows 10 (64-bit)
- 4 GB RAM
- 2 GB free disk space
- MT5 terminal installed

### Recommended
- Windows 10/11 (64-bit)
- 8 GB RAM
- NVIDIA GPU with CUDA support
- SSD storage
- Stable internet connection

## Deployment Checklist

- [ ] Test on clean Windows machine
- [ ] Verify MT5 connectivity
- [ ] Train model with sample data
- [ ] Run demo account trades
- [ ] Check log output
- [ ] Measure .exe size (< 300 MB)
- [ ] Document user manual
- [ ] Prepare support materials

## Maintenance

### Logs Rotation
- Automatic via RotatingFileHandler
- 2 MB per file, 3 backups

### Model Retraining
- Recommended: Monthly or after major market shifts
- User-initiated via Training tab

### Dependency Updates
- Monitor security advisories
- Test thoroughly before updating PyTorch/PyQt5

## Known Limitations

1. **Windows Only**: MT5 SDK requires Windows
2. **Single Symbol**: Currently XAUUSD only
3. **No Multi-Threading**: Live execution is single-threaded
4. **Password Security**: Plain text storage
5. **Limited Backtesting**: Module under development

## Conclusion

The architecture prioritizes modularity, maintainability, and user experience. The clear separation between GUI, core logic, and utilities enables independent testing and future enhancements. The PyInstaller packaging simplifies distribution for non-technical users.
