# XAUUSD AI Trading System - User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [First Launch](#first-launch)
4. [Configuration](#configuration)
5. [Training Your Model](#training-your-model)
6. [Live Trading](#live-trading)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)
9. [FAQs](#faqs)

## Introduction

The XAUUSD AI Trading System is a desktop application designed for automated gold (XAUUSD) trading on MetaTrader 5. It combines:

- **Technical Analysis**: EMA21 trend detection, ATR-based risk management
- **Deep Learning**: TCN (Temporal Convolution Network) for pattern recognition
- **Automated Execution**: Direct MT5 integration for order placement
- **Real-Time Monitoring**: Live charts and position tracking

### Key Features
✅ Oscillation trading with mean reversion  
✅ Dynamic stop-loss and take-profit based on ATR  
✅ 16-point spread cost handling  
✅ GPU-accelerated training  
✅ Real-time K-line charts with EMA overlay  
✅ Automated position management  

## Installation

### Option 1: Run from Executable (Windows)

1. Extract the `XAUUSD_Trading_System.zip` file
2. Navigate to the folder
3. Double-click `XAUUSD_Trading_System.exe`
4. No Python installation required!

### Option 2: Run from Source

1. Install Python 3.10+ from [python.org](https://www.python.org)
2. Extract the source code
3. Open Command Prompt in the project folder
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the application:
   ```bash
   python main.py
   ```

## First Launch

When you launch the application for the first time:

1. The main window opens with 6 tabs:
   - ⚙️ **配置** (Configuration)
   - 🎓 **训练** (Training)
   - 📈 **回测** (Backtest)
   - 🚀 **实盘** (Live Trading)
   - 📊 **监控** (Monitoring)
   - 🧾 **日志** (Logs)

2. A configuration file is created at:
   - Windows: `C:\Users\<your-username>\.xauusd_trading\config.json`

3. Logs will be written to:
   - Windows: `C:\Users\<your-username>\.xauusd_trading\application.log`

## Configuration

### Step 1: MT5 Connection

Navigate to the **⚙️ 配置** tab:

1. **账号 (Account)**: Enter your MT5 login number
2. **密码 (Password)**: Enter your MT5 password
3. **服务器 (Server)**: Enter your broker's server name (e.g., "ICMarkets-Demo")
4. Click **连接 MT5** to test the connection

✅ **Success**: Status shows "✅ 已连接" in green  
❌ **Failure**: Status shows "❌ 连接失败" in red - check your credentials

### Step 2: Strategy Parameters

Configure trading strategy settings:

| Parameter | Description | Default | Recommended Range |
|-----------|-------------|---------|-------------------|
| 点差 (Spread) | Spread in points | 16 | 10-30 |
| 手数 (Lot Size) | Trade volume | 0.1 | 0.01-1.0 |
| EMA 周期 (EMA Period) | Trend indicator period | 21 | 20-50 |
| ATR 周期 (ATR Period) | Volatility period | 14 | 10-20 |
| ATR 止损倍数 (SL Multiplier) | Stop-loss ATR multiple | 2.0 | 1.5-3.0 |
| ATR 止盈倍数 (TP Multiplier) | Take-profit ATR multiple | 3.0 | 2.0-5.0 |

### Step 3: Save Configuration

Click **保存配置** to save your settings. These will persist across sessions.

## Training Your Model

### Step 1: Prepare Training Data

You need historical OHLC (Open, High, Low, Close) data in CSV format:

```csv
time,open,high,low,close,tick_volume
2024-01-01 00:00:00,2050.50,2051.20,2049.80,2050.90,1234
2024-01-01 00:15:00,2050.90,2052.00,2050.50,2051.50,2345
...
```

**Required Columns:**
- `time`: Timestamp (YYYY-MM-DD HH:MM:SS)
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price
- `close`: Closing price
- `tick_volume` (optional): Will be set to 0 if missing

**Data Requirements:**
- Minimum 500 rows recommended (more is better)
- M15 timeframe (15-minute candles)
- Sorted chronologically

### Step 2: Load Data

Navigate to the **🎓 训练** tab:

1. Click **加载历史数据**
2. Select your CSV file
3. Status will show "✅ 已加载数据: /path/to/file.csv"

### Step 3: Start Training

1. Click **开始训练**
2. Monitor progress:
   - **Progress Bar**: Shows epoch completion (0-100%)
   - **Metrics**: Displays Train Loss, Val Loss, Val Acc
   - **Loss Chart**: Real-time visualization of training progress

3. Training duration depends on:
   - Data size (more data = longer training)
   - Epochs (default: 100)
   - GPU availability (faster with CUDA-enabled GPU)

4. When complete:
   - Status shows "训练完成，模型已保存"
   - Model saved to `~/.xauusd_trading/tcn_model.pth`

### Training Tips

✅ **Use GPU**: Install CUDA-enabled PyTorch for 10-20x speedup  
✅ **More Data**: 2000+ samples improve model quality  
✅ **Monitor Loss**: Both Train and Val loss should decrease  
✅ **Avoid Overfitting**: Val loss should not increase while Train loss decreases  

## Live Trading

⚠️ **Warning**: Always test on a demo account first!

### Step 1: Ensure MT5 Connection

1. Navigate to **⚙️ 配置** tab
2. Verify connection status is "✅ 已连接"
3. If not connected, enter credentials and click **连接 MT5**

### Step 2: Start Live Trading

Navigate to the **🚀 实盘** tab:

1. Click **启动实盘**
2. Status changes to "✅ 实盘运行中"
3. The system will:
   - Fetch M15 data every 5 seconds
   - Calculate EMA and ATR indicators
   - Evaluate trading signals
   - Place orders when conditions are met

### Step 3: Monitor Positions

The positions table shows:
- **订单号**: Order ticket number
- **方向**: Direction (buy/sell)
- **手数**: Volume (lot size)
- **开仓价**: Entry price
- **当前价**: Current price
- **收益**: Profit/loss in account currency

### Step 4: Stop Trading

Click **停止实盘** to halt automated trading. Existing positions remain open.

### Trading Logic

The strategy follows this logic:

1. **Fetch Data**: Get last 100 M15 candles
2. **Calculate Indicators**: EMA21, ATR14
3. **Signal Generation**:
   - If `price > EMA`: Consider LONG
   - If `price < EMA`: Consider SHORT
4. **Risk Management**:
   - Stop Loss: `entry ± (ATR × sl_multiplier)`
   - Take Profit: `entry ± (ATR × tp_multiplier)`
5. **Execution**: Place market order via MT5

### Live Trading Tips

✅ **Start Small**: Use 0.01-0.1 lot size initially  
✅ **Monitor Regularly**: Check positions every few hours  
✅ **Demo First**: Test on demo account for 1-2 weeks  
✅ **Set Realistic Expectations**: Not all trades will be profitable  
⚠️ **Risk Only What You Can Afford to Lose**  

## Monitoring

### Real-Time Chart

Navigate to the **📊 监控** tab:

1. Click **开始监控**
2. Chart displays:
   - **Blue Line**: XAUUSD close price
   - **Orange Dashed Line**: EMA21
   - Updates every 10 seconds

3. Click **停止监控** to halt chart updates

### Viewing Logs

Navigate to the **🧾 日志** tab:

- View real-time application logs
- Logs include:
  - Connection events
  - Trade executions
  - Errors and warnings
- Click **刷新日志** to reload

### Log File Location

Full logs are saved to:
- `C:\Users\<username>\.xauusd_trading\application.log`

Open with any text editor for detailed history.

## Troubleshooting

### Connection Issues

**Problem**: "❌ MT5 连接失败"

**Solutions**:
1. Verify MT5 is running
2. Check login/password/server are correct
3. In MT5, go to Tools > Options > Expert Advisors:
   - Enable "Allow automated trading"
   - Enable "Allow DLL imports"
4. Restart MT5 and try again
5. Check firewall/antivirus settings

### Training Failures

**Problem**: "训练失败" or error dialog

**Solutions**:
1. Check CSV has required columns (time, open, high, low, close)
2. Ensure at least 500 rows of data
3. Verify data is sorted by time
4. Check for NaN or missing values
5. View logs for detailed error message

### GPU Not Detected

**Problem**: Training uses CPU instead of GPU

**Solutions**:
1. Install CUDA Toolkit (11.8 or 12.x)
2. Install cuDNN
3. Reinstall PyTorch with CUDA:
   ```bash
   pip uninstall torch
   pip install torch --index-url https://download.pytorch.org/whl/cu118
   ```
4. Restart application

### Application Won't Start

**Problem**: Double-clicking .exe does nothing

**Solutions**:
1. Check Windows Defender/antivirus hasn't blocked it
2. Run as Administrator
3. Check `application.log` for error details
4. Ensure MT5 is installed
5. Try running from source code (see Installation)

### No Trades Executed

**Problem**: Live trading running but no orders placed

**Possible Reasons**:
1. **No Signal**: Price not crossing EMA
2. **Existing Position**: Already have open position
3. **Insufficient Margin**: Not enough balance for trade
4. **Symbol Not Available**: XAUUSD not available on account

**Check**:
- View logs for signal evaluation messages
- Verify XAUUSD is in MT5 Market Watch
- Check account balance and free margin

## FAQs

### Q: What is the minimum deposit required?

**A**: Depends on your broker's requirements. For 0.01 lot size on XAUUSD, typically $100-$500 is sufficient for demo/small testing.

### Q: Can I trade other symbols besides XAUUSD?

**A**: Currently, the system is optimized for XAUUSD. Code modifications would be needed for other symbols.

### Q: Do I need to keep the application running 24/7?

**A**: For live trading, yes. Consider running on a VPS (Virtual Private Server) for uninterrupted operation.

### Q: How often should I retrain the model?

**A**: Retrain monthly or after significant market regime changes (e.g., major economic events).

### Q: Can I use this on Mac or Linux?

**A**: MT5 API requires Windows. You can run Windows in a VM on Mac/Linux, but native support is not available.

### Q: Is the strategy profitable?

**A**: Past performance does not guarantee future results. Always backtest thoroughly and start with demo accounts.

### Q: How do I get historical data?

**A**: Options include:
1. Export from MT5 (Tools > History Center)
2. Download from broker's website
3. Use MT5 API to fetch programmatically
4. Third-party data providers (e.g., Dukascopy, AlphaVantage)

### Q: What if I want to change the strategy logic?

**A**: The code is open-source. Modify `core/live/executor.py` for execution logic and retrain the model.

### Q: Can I use multiple accounts simultaneously?

**A**: Current version supports one MT5 connection at a time. Multiple instances would require code modifications.

### Q: How do I uninstall?

**A**: 
1. Delete the application folder
2. Delete `C:\Users\<username>\.xauusd_trading\` to remove configs/logs
3. No registry changes are made

## Support

For additional help:

1. **Check Logs**: `🧾 日志` tab or `.xauusd_trading\application.log`
2. **Review Documentation**:
   - README.md: Overview
   - SETUP.md: Installation guide
   - ARCHITECTURE.md: Technical details
3. **Common Issues**: See Troubleshooting section above

## Disclaimer

This software is provided for educational and research purposes. Trading forex and CFDs involves significant risk. You should:

- Only trade with funds you can afford to lose
- Test thoroughly on demo accounts
- Understand the risks involved
- Comply with local regulations
- Seek professional financial advice if needed

The developers are not responsible for any financial losses incurred through use of this software.

---

**Version**: 1.0.0  
**Last Updated**: 2024-01  
**License**: See LICENSE file
