# Setup Guide for XAUUSD AI Trading System

## Prerequisites

### 1. Python Environment
- Python 3.10 or higher
- Windows OS (for MT5 compatibility and .exe building)

### 2. MetaTrader 5
- Download and install MT5 from your broker
- Ensure you have valid trading account credentials
- Enable "Allow DLL imports" and "Allow automated trading" in MT5 settings

### 3. GPU Support (Optional but Recommended)
For faster model training:
- Install CUDA Toolkit 11.8 or 12.x
- Install cuDNN compatible with your CUDA version
- Install PyTorch with CUDA support:
  ```
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```

## Installation Steps

### Step 1: Clone or Extract the Project
```bash
cd xauusd-trading-software
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python main.py
```

## First-Time Configuration

### 1. Configure MT5 Connection
- Navigate to "⚙️ 配置" tab
- Enter your MT5 account login, password, and server
- Click "连接 MT5" to test connection
- Adjust strategy parameters (spread, lot size, EMA period, ATR settings)
- Click "保存配置"

### 2. Prepare Training Data
You can either:
- **Option A**: Load CSV file with historical OHLC data
- **Option B**: Use MT5 connector to fetch historical data programmatically

CSV format example:
```csv
time,open,high,low,close,tick_volume,spread,real_volume
2024-01-01 00:00:00,2050.50,2051.20,2049.80,2050.90,1234,0,0
2024-01-01 00:15:00,2050.90,2052.00,2050.50,2051.50,2345,0,0
...
```

### 3. Train the Model
- Navigate to "🎓 训练" tab
- Click "加载历史数据" and select your CSV file
- Click "开始训练" to start training
- Monitor training progress and loss curves in real-time
- Model will be saved to `~/.xauusd_trading/tcn_model.pth`

### 4. Run Backtest (Coming Soon)
- Navigate to "📈 回测" tab
- Run historical backtests to evaluate strategy performance

### 5. Start Live Trading
- Navigate to "🚀 实盘" tab
- Click "启动实盘" to start automated trading
- Monitor open positions in the table
- Click "停止实盘" to halt trading

### 6. Monitor Market
- Navigate to "📊 监控" tab
- Click "开始监控" to view real-time price chart with EMA overlay
- Chart updates every 10 seconds

### 7. View Logs
- Navigate to "🧾 日志" tab
- View application logs in real-time
- Logs are also saved to `~/.xauusd_trading/application.log`

## Building Windows Executable

### Requirements
- PyInstaller must be run on Windows
- All dependencies installed
- icon.ico file in project root

### Build Command
```bash
pyinstaller build_exe.spec
```

### Output
The executable and all dependencies will be in:
```
dist/XAUUSD_Trading_System/XAUUSD_Trading_System.exe
```

### Distribution
- Distribute the entire `dist/XAUUSD_Trading_System/` folder
- Users can run `XAUUSD_Trading_System.exe` directly
- No Python installation required on target machine

## Troubleshooting

### MT5 Connection Issues
- Verify MT5 is installed and running
- Check account credentials are correct
- Ensure MT5 allows API connections (Tools > Options > Expert Advisors)
- Check firewall/antivirus settings

### Training Failures
- Ensure CSV has required columns: time, open, high, low, close
- Check data has sufficient rows (minimum 500+ recommended)
- Verify GPU drivers if using CUDA

### Import Errors
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- Check Python version compatibility

### Performance Issues
- Reduce batch size in config
- Use CPU if GPU memory insufficient
- Close other resource-intensive applications

## Configuration Files

All user settings and trained models are stored in:
- Windows: `C:\Users\<username>\.xauusd_trading\`
- Contains:
  - `config.json` - User settings
  - `tcn_model.pth` - Trained model weights
  - `application.log` - Application logs

## Safety Recommendations

1. **Test on Demo Account First**
   - Always test strategies on demo accounts before live trading
   - Verify all parameters are correct

2. **Risk Management**
   - Start with small lot sizes (0.01 - 0.1)
   - Monitor positions regularly
   - Set appropriate stop-loss levels

3. **Regular Monitoring**
   - Check logs daily
   - Review trading performance
   - Adjust parameters based on market conditions

4. **Backup**
   - Backup configuration and model files regularly
   - Keep historical training data

## Support

For issues or questions:
1. Check logs in "🧾 日志" tab
2. Review `~/.xauusd_trading/application.log`
3. Verify MT5 connection status
4. Ensure all dependencies are installed correctly

## Version Information

- Version: 1.0.0
- Tested with: MT5 Build 3770+
- Python: 3.10+
- PyTorch: 2.0+
