# XAUUSD布林带震荡策略 (Bollinger Bands Range Trading Strategy)

基于布林带的XAUUSD（黄金/美元）震荡交易策略，使用真实历史数据进行回测。

## 策略概述

### 核心参数
- **布林带周期**: 14
- **均线类型**: SMA (简单移动平均)
- **标准差**: 2
- **震荡判断**: 中轨角度 < 30度

### 交易规则
1. **震荡判断**: 当布林带中轨趋平（角度 < 30度）时，判定为震荡行情
2. **做多信号**: 价格触及下轨时开多仓
3. **做空信号**: 价格触及上轨时开空仓
4. **中轨规则**: 价格在中轨附近不开仓
5. **止损止盈**:
   - 止损: 2%
   - 止盈: 3%
   - 价格回到中轨时平仓

## 文件结构

```
strategy/
├── README.md                   # 本文件
├── indicators.mjs              # 技术指标计算（布林带、SMA、斜率等）
├── bollingerStrategy.mjs       # 策略核心逻辑
├── dataFetcher.mjs            # 历史数据获取
├── backtester.mjs             # 回测引擎
├── runBacktest.mjs            # 回测运行脚本
├── data/                      # 数据目录（自动创建）
│   ├── xauusd_mock.csv       # 模拟数据
│   └── xauusd_yahoo.csv      # Yahoo Finance数据（缓存）
└── results/                   # 回测结果（自动创建）
    ├── backtest_YYYY-MM-DD.json
    ├── report_YYYY-MM-DD.txt
    └── equity_YYYY-MM-DD.csv
```

## 快速开始

### 1. 使用模拟数据运行（默认）

```bash
# 从项目根目录运行
node strategy/runBacktest.mjs
```

这将使用生成的模拟数据（365天）进行回测。

### 2. 使用真实数据运行

#### Yahoo Finance数据（推荐）

```bash
USE_REAL_DATA=true DATA_SOURCE=yahoo node strategy/runBacktest.mjs
```

这将从Yahoo Finance获取黄金期货(GC=F)的真实历史数据（最近2年日线）。

#### 使用本地CSV文件

```bash
DATA_SOURCE=csv CSV_FILE=./strategy/data/my_data.csv node strategy/runBacktest.mjs
```

CSV文件格式:
```
Date,Open,High,Low,Close,Volume
2024-01-01,2000.50,2010.30,1995.20,2005.80,10000
...
```

## 数据源说明

### 1. 模拟数据（Mock Data）
- **优点**: 无需API，即时可用
- **缺点**: 非真实市场数据
- **用途**: 快速测试、演示

### 2. Yahoo Finance
- **优点**: 免费、真实数据、无API密钥
- **缺点**: 使用黄金期货(GC=F)替代现货XAUUSD
- **数据**: 最近2年日线数据
- **缓存**: 24小时有效

### 3. 本地CSV
- **优点**: 完全自定义
- **用途**: 使用其他来源的数据

## 回测结果

运行回测后，将生成以下文件：

### 1. JSON结果 (`backtest_YYYY-MM-DD.json`)
包含完整的回测数据：
- 所有交易记录
- 详细统计指标
- 权益曲线数据

### 2. 文本报告 (`report_YYYY-MM-DD.txt`)
格式化的回测报告，包括：
- 总体表现（收益率、净利润）
- 交易统计（胜率、平均盈亏）
- 风险指标（夏普比率、最大回撤）
- 最近交易记录

### 3. 权益曲线 (`equity_YYYY-MM-DD.csv`)
可用于Excel或其他工具绘制权益曲线图。

## 示例输出

```
================================================================================
XAUUSD布林带震荡策略回测报告
================================================================================

总体表现 (Overall Performance):
--------------------------------------------------------------------------------
初始资金 (Initial Balance):        $10000.00
最终资金 (Final Balance):          $12500.00
净利润 (Net Profit):               $2500.00
收益率 (Return):                   +25.00%

交易统计 (Trade Statistics):
--------------------------------------------------------------------------------
总交易次数 (Total Trades):         45
盈利交易 (Winning Trades):         28
亏损交易 (Losing Trades):          17
胜率 (Win Rate):                   62.22%
平均盈利 (Avg Win):                $150.00
平均亏损 (Avg Loss):               $-80.00

风险指标 (Risk Metrics):
--------------------------------------------------------------------------------
盈亏比 (Profit Factor):            1.85
夏普比率 (Sharpe Ratio):           1.23
最大回撤 (Max Drawdown):           $350.00 (3.50%)
```

## 策略参数调整

可以在 `runBacktest.mjs` 中修改策略参数：

```javascript
const strategy = new BollingerRangeStrategy({
  bollingerPeriod: 14,        // 布林带周期
  bollingerStdDev: 2,         // 标准差倍数
  angleThreshold: 30,         // 震荡判断角度阈值（度）
  slopeLookback: 3,           // 斜率计算回看周期
  stopLossPercent: 2,         // 止损百分比
  takeProfitPercent: 3        // 止盈百分比
});
```

## 高级用法

### 参数优化

可以编写脚本测试不同参数组合：

```javascript
const periods = [10, 14, 20];
const stdDevs = [1.5, 2, 2.5];
const angles = [20, 30, 40];

for (const period of periods) {
  for (const stdDev of stdDevs) {
    for (const angle of angles) {
      // 运行回测并记录结果
    }
  }
}
```

### 多时间周期回测

修改 `dataFetcher.mjs` 中的时间间隔参数。

## 注意事项

1. **数据质量**: 真实交易需要高质量的XAUUSD现货数据
2. **滑点成本**: 回测未考虑滑点和交易成本
3. **过拟合**: 避免过度优化参数
4. **市场环境**: 震荡策略在趋势市场中表现较差
5. **风险管理**: 实盘需要严格的仓位和风险控制

## 技术指标说明

### 布林带 (Bollinger Bands)
- **中轨**: 14周期SMA
- **上轨**: 中轨 + 2倍标准差
- **下轨**: 中轨 - 2倍标准差

### 震荡判断
通过计算中轨的斜率并转换为角度：
- 角度 < 30度 → 震荡行情
- 角度 >= 30度 → 趋势行情

## 许可证

MIT License

## 贡献

欢迎提交问题和改进建议！
