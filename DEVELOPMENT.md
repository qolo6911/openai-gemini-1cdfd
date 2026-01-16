# XAUUSD Trading System - Developer Documentation

## Development Setup

### Prerequisites

- Python 3.9+
- Windows 10/11 (for MT5 support)
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd xauusd-trading-software
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac (for development without MT5)
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

```bash
python main.py
```

### Running Tests

```bash
python test_basic.py
```

## Project Architecture

### GUI Layer (`gui/`)

The graphical user interface is built with PyQt5 and consists of:

- **MainWindow**: The main application window with tab-based navigation
- **ConfigWidget**: Configuration management (MT5, strategy parameters, risk settings)
- **TrainingWidget**: Model training interface with progress tracking
- **BacktestWidget**: Strategy backtesting with result visualization
- **LiveWidget**: Real-time trading control and monitoring
- **MonitorWidget**: Live price charts and multi-timeframe status
- **LogWidget**: System and trading log viewer

### Core Layer (`core/`)

Business logic organized into modules:

#### Data Module (`core/data/`)
- **mt5_connector.py**: MetaTrader 5 integration for data fetching
- **dataset.py**: PyTorch Dataset classes for training
- **preprocessor.py**: Data preprocessing and normalization

#### Features Module (`core/features/`)
- **indicators.py**: Technical indicators (EMA, ATR, RSI, Bollinger Bands)
- **regime_detector.py**: Market regime classification
- **feature_engineering.py**: Feature creation pipeline

#### Models Module (`core/models/`)
- **tcn.py**: Temporal Convolutional Network implementation
- **model_factory.py**: Factory for creating different model architectures

#### Training Module (`core/training/`)
- **trainer.py**: Training loop and model management
- **losses.py**: Custom loss functions
- **metrics.py**: Evaluation metrics

#### Labeling Module (`core/labeling/`)
- **triple_barrier.py**: Triple barrier labeling method
- **cost_adjusted_labels.py**: Cost-aware label adjustment

#### Backtest Module (`core/backtest/`)
- **engine.py**: Backtesting engine
- **reporting.py**: Result reporting and visualization

#### Live Module (`core/live/`)
- **executor.py**: Order execution via MT5
- **signal_generator.py**: Trading signal generation
- **risk_manager.py**: Position sizing and risk management

### Utilities (`utils/`)

- **config_manager.py**: Configuration file handling
- **logger.py**: Logging system setup
- **helpers.py**: Miscellaneous utilities

## Configuration

Configuration is stored in JSON format at the project root:

```json
{
  "mt5": {
    "server": "BrokerServer",
    "login": "12345678",
    "password": "password",
    "symbol": "XAUUSD"
  },
  "strategy": {
    "ema_period": 21,
    "atr_period": 14,
    "tp_multiplier": 1.5,
    "sl_multiplier": 1.0,
    "spread": 16.0,
    "holding_period": 24
  },
  "risk": {
    "risk_per_trade": 0.5,
    "max_daily_loss": 2.0,
    "max_positions": 3
  },
  "model": {
    "window_size": 128,
    "threshold": 0.6,
    "model_type": "TCN"
  }
}
```

## Deep Learning Model

### TCN Architecture

The Temporal Convolutional Network (TCN) consists of:

- Multiple dilated causal convolution layers
- Residual connections
- Dropout for regularization
- Final classification layer (3 classes: Long/Short/Flat)

### Training Process

1. Data preparation (fetch from MT5 or load from CSV)
2. Feature engineering (indicators, regime detection)
3. Label generation (triple barrier method)
4. Model training with progress callbacks
5. Model evaluation and saving

### Inference

1. Fetch latest market data
2. Preprocess and extract features
3. Model prediction
4. Signal generation with threshold filtering
5. Risk management and position sizing

## Building the Executable

### Using PyInstaller

```bash
python build.py --build
```

This will:
1. Check all dependencies
2. Run PyInstaller with the spec file
3. Generate the executable in `dist/`

### Manual Build

```bash
pyinstaller build_exe.spec
```

### Build Configuration

The `build_exe.spec` file contains:

- Entry point: `main.py`
- Data files to include (gui/, core/, utils/, resources/)
- Hidden imports (PyTorch, PyQt5, etc.)
- Output settings (console=False for windowed app)

## Creating the Installer

Using Inno Setup (Windows only):

1. Install Inno Setup
2. Open `installer/setup.iss`
3. Compile the script
4. Output: `installer/output/XAUUSD_Trading_Setup.exe`

## Trading Strategy

### Regime Detection

Market regime is determined using EMA21 on H1 and H4 timeframes:

- **Bullish Trend**: Price > EMA21 * 1.002
- **Bearish Trend**: Price < EMA21 * 0.998
- **Consolidation**: Otherwise

### Signal Generation

1. Detect current regime
2. Apply deep learning model on M15 timeframe
3. Generate prediction probabilities
4. Filter by threshold (default: 0.6)
5. Calculate entry, SL, and TP based on ATR

### Risk Management

- Position size based on account balance and SL distance
- Maximum risk per trade: 0.5% (configurable)
- Maximum daily loss: 2.0% (configurable)
- Maximum concurrent positions: 3 (configurable)

## Testing

### Unit Tests

```bash
pytest tests/
```

### Integration Tests

Test with demo MT5 account before live trading.

### Performance Metrics

- Training accuracy
- Validation loss
- Backtest Sharpe ratio
- Win rate
- Maximum drawdown

## Deployment

### Local Deployment

Simply run the .exe file on Windows with MT5 installed.

### Configuration Steps

1. Launch the application
2. Go to "配置" tab
3. Enter MT5 credentials
4. Test connection
5. Adjust strategy and risk parameters
6. Save configuration

### Running in Production

1. Ensure stable internet connection
2. Keep MT5 terminal running
3. Monitor the "监控" tab for system status
4. Check "日志" tab for trading activity
5. Set up alerts for errors or unexpected behavior

## Troubleshooting

### MT5 Connection Issues

- Verify MT5 is running
- Check server address and credentials
- Ensure symbol "XAUUSD" is available
- Check firewall settings

### Model Training Issues

- Insufficient data: Download more historical data
- GPU not detected: Install CUDA toolkit
- Out of memory: Reduce batch size or window size

### Application Crashes

- Check logs in `logs/` directory
- Ensure all dependencies are installed
- Verify Python version compatibility

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
