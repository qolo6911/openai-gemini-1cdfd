# Quick Start Guide

This guide will help you quickly set up and run the XAUUSD Deep Learning Trading Strategy system.

## Prerequisites

- Python 3.9 or higher
- MetaTrader5 terminal installed (for data fetching)
- GPU with CUDA support (optional, but recommended)

## Installation

1. **Navigate to the project directory**:
   ```bash
   cd xauusd-strategy
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or if you prefer using a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Configuration

1. **Edit `config.yaml`** to set your parameters:
   - Update `start_date` and `end_date` for data range
   - Configure MT5 credentials if using authentication
   - Adjust hyperparameters if needed

   ```yaml
   data:
     start_date: '2020-01-01'
     end_date: '2024-01-01'
     mt5:
       login: null  # Set your MT5 login
       password: null
       server: null
   ```

## Training the Model

### Basic Training

Run the training script:

```bash
python scripts/train.py
```

This will:
1. Connect to MT5 and fetch XAUUSD data
2. Calculate multi-timeframe features
3. Generate labels using triple barrier method
4. Train a TCN model
5. Save the best model to `artifacts/best_model.pth`

Expected output:
```
============================================================
1. Connecting to MT5 and fetching data...
============================================================
M15 data shape: (...)
...
============================================================
8. Starting training...
============================================================
Epoch 1/100
Train Loss: 0.9234, Val Accuracy: 0.6123
...
Training complete!
Final model saved to: artifacts/final_model.pth
```

### Hyperparameter Optimization

To find optimal parameters:

```bash
python scripts/optimize.py
```

This runs Optuna optimization for 50 trials and saves results to `optuna_best_params.yaml`.

## Understanding the Output

### Training Artifacts

After training, you'll find:
- `artifacts/best_model.pth` - Best model checkpoint
- `artifacts/final_model.pth` - Final trained model
- `artifacts/feature_scaler.joblib` - Feature scaler for inference

### Key Metrics

- **Validation Accuracy**: Target >60% (baseline)
- **Class Distribution**: Check for imbalance (adjust if 100% "flat")
- **Confusion Matrix**: Shows prediction patterns

## Common Issues

### Issue: MT5 Connection Failed

**Solution**: Ensure MT5 terminal is running and accessible.

```python
# Test connection manually:
import MetaTrader5 as mt5
if not mt5.initialize():
    print(f"Error: {mt5.last_error()}")
```

### Issue: Out of Memory (GPU)

**Solution**: Reduce batch size or model size in `config.yaml`:

```yaml
training:
  batch_size: 32  # Reduce from 64

model:
  num_channels: [32, 64, 128]  # Reduce from [64, 128, 256]
```

### Issue: Low Accuracy (<40%)

**Possible causes**:
- Insufficient training data (expand date range)
- Poor hyperparameters (run optimization)
- All labels are "flat" (check regime detection)

**Solution**: Check label distribution:
```python
import pandas as pd
# After labeling step in train.py
print(df['label'].value_counts())
# Should see mix of long/short/flat, not 100% flat
```

## Testing Without MT5

If you want to test the code without MT5 connection (using mock data):

1. Create a mock data script:
   ```python
   # mock_data.py
   import pandas as pd
   import numpy as np
   
   def generate_mock_data(n=10000):
       dates = pd.date_range('2020-01-01', periods=n, freq='15min')
       close = 1800 + np.cumsum(np.random.randn(n) * 0.5)
       
       df = pd.DataFrame({
           'open': close + np.random.randn(n) * 0.1,
           'high': close + np.abs(np.random.randn(n) * 0.2),
           'low': close - np.abs(np.random.randn(n) * 0.2),
           'close': close,
           'tick_volume': np.random.randint(100, 1000, n)
       }, index=dates)
       return df
   ```

2. Modify `scripts/train.py` to use mock data instead of MT5 fetching.

## Next Steps

1. **Backtesting**: Implement the backtest engine to evaluate performance
2. **Ensemble**: Train multiple models with different seeds
3. **Live Trading**: Integrate real-time MT5 execution (use with caution!)
4. **Monitoring**: Set up logging and performance tracking

## Resources

- [README.md](README.md) - Full documentation
- [config.yaml](config.yaml) - Configuration reference
- [Triple Barrier Method](https://mlfinlab.readthedocs.io/) - Labeling methodology

## Support

For issues or questions:
1. Check the troubleshooting section in README.md
2. Review error messages carefully
3. Validate your MT5 connection and data availability
4. Ensure all dependencies are installed correctly

## Safety Notice

⚠️ **This is a research/educational system. Do not use in live trading without:**
- Extensive backtesting
- Risk management review
- Paper trading validation
- Professional financial advice

Trading involves significant risk of loss. Use at your own risk.
