# XAUUSD AI Trading System

## 项目概述

XAUUSD AI Trading System 是一个完整的 Windows 桌面交易软件，集成 XAUUSD 深度学习策略、图形界面、MT5 连接，最终打包成可双击运行的 .exe 可执行文件。

## 特性

- ✅ **PyQt5 现代化图形界面** - 6 个功能模块（配置、训练、回测、实盘、监控、日志）
- ✅ **MT5 连接** - 实时数据获取和交易执行
- ✅ **深度学习模型** - TCN 和 Transformer 模型支持
- ✅ **实时监控** - 多周期价格走势和指标显示
- ✅ **回测系统** - 完整的策略回测和报告生成
- ✅ **风险管理** - ATR 动态止损/止盈，仓位管理
- ✅ **可执行文件** - PyInstaller 打包成单文件 .exe

## 系统要求

- Windows 10/11
- Python 3.9+ (开发环境)
- MetaTrader 5 终端
- 8GB+ RAM
- GPU (可选，用于模型训练加速)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python main.py
```

### 3. 配置 MT5 连接

1. 打开"配置"标签页
2. 输入您的 MT5 服务器信息
3. 输入账户登录信息
4. 点击"测试连接"验证

### 4. 训练模型

1. 切换到"训练"标签页
2. 点击"从 MT5 下载数据"
3. 设置训练参数（Epochs, Batch Size, Learning Rate）
4. 点击"开始训练"

### 5. 回测策略

1. 切换到"回测"标签页
2. 选择测试时间段
3. 选择训练好的模型文件
4. 点击"运行回测"查看结果

### 6. 启动实盘交易

1. 切换到"实盘"标签页
2. 确认 MT5 连接状态
3. 点击"启动自动交易"

## 项目结构

```
xauusd-trading-software/
├── main.py                      # 应用程序入口
├── requirements.txt             # Python 依赖
├── build_exe.spec              # PyInstaller 打包配置
│
├── gui/                        # GUI 模块
│   ├── main_window.py         # 主窗口
│   ├── config_widget.py       # 配置页面
│   ├── training_widget.py     # 训练页面
│   ├── backtest_widget.py     # 回测页面
│   ├── live_widget.py         # 实盘交易页面
│   ├── monitor_widget.py      # 监控页面
│   └── log_widget.py          # 日志页面
│
├── core/                       # 核心交易逻辑
│   ├── data/
│   │   ├── mt5_connector.py
│   │   └── dataset.py
│   ├── features/
│   │   ├── indicators.py
│   │   └── regime_detector.py
│   ├── models/
│   │   ├── tcn.py
│   │   └── model_factory.py
│   └── training/
│       ├── trainer.py
│       ├── losses.py
│       └── metrics.py
│
└── utils/                      # 工具模块
    ├── config_manager.py      # 配置文件管理
    ├── logger.py              # 日志系统
    └── helpers.py
```

## 打包成 .exe

### 使用 PyInstaller 打包

```bash
pyinstaller build_exe.spec
```

生成的可执行文件位于 `dist/XAUUSD_Trading_System.exe`

### 文件大小

- 单文件可执行程序: ~150-250MB
- 包含所有依赖（PyQt5, PyTorch, matplotlib, pandas 等）

## 功能说明

### 配置页面 (⚙️ 配置)

- MT5 连接设置（服务器、账户、密码）
- 策略参数配置（EMA、ATR、TP/SL 倍数）
- 风控设置（风险百分比、最大亏损）
- 模型参数（窗口大小、阈值）

### 训练页面 (🎓 训练)

- 数据下载（从 MT5 或 CSV）
- 训练参数设置（Epochs, Batch Size, Learning Rate）
- 实时训练进度显示
- 损失曲线可视化

### 回测页面 (📊 回测)

- 时间段选择
- 模型文件选择
- 关键指标展示（收益、回撤、Sharpe 比率、胜率）
- 权益曲线和回撤图表

### 实盘交易页面 (🚀 实盘)

- 账户信息实时显示
- 当前持仓管理
- 交易信号展示
- 自动交易控制

### 监控页面 (📈 监控)

- 实时价格走势图
- EMA21 指标显示
- 多周期状态（H4/H1/M15）
- Regime 检测

### 日志页面 (📝 日志)

- 系统日志记录
- 交易日志
- 日志导出功能

## 策略说明

### Regime 检测

- 使用 H1/H4 EMA21 判断趋势/震荡
- 震荡期：均值回归策略
- 趋势期：趋势跟随策略

### 深度学习模型

- TCN (Temporal Convolutional Network)
- Transformer 模型
- 三分类输出：Long/Short/Flat

### 风险管理

- ATR 动态止损/止盈
- 点差 16
- 仓位管理（默认 0.5% 风险）
- 最大日亏损限制

## 注意事项

⚠️ **风险警告**: 本软件仅供学习和研究使用。实盘交易存在风险，请谨慎使用。

- 在实盘使用前，请充分测试
- 建议先在模拟账户上运行
- 设置合理的风险参数
- 定期监控系统运行状态

## 技术支持

如有问题或建议，请提交 Issue。

## 许可证

MIT License

## 版本历史

- v1.0.0 - 初始版本
  - 完整 GUI 界面
  - MT5 集成
  - TCN 和 Transformer 模型
  - 回测和实盘交易功能
