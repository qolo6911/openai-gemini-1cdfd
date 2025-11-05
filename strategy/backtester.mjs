/**
 * 回测引擎
 * Backtesting Engine
 */

import { SignalType } from './bollingerStrategy.mjs';

/**
 * 回测结果统计
 */
class BacktestStats {
  constructor() {
    this.totalTrades = 0;
    this.winningTrades = 0;
    this.losingTrades = 0;
    this.totalProfit = 0;
    this.totalLoss = 0;
    this.maxDrawdown = 0;
    this.maxDrawdownPercent = 0;
    this.sharpeRatio = 0;
    this.profitFactor = 0;
    this.winRate = 0;
    this.avgWin = 0;
    this.avgLoss = 0;
    this.largestWin = 0;
    this.largestLoss = 0;
    this.trades = [];
    this.equity = [];
  }

  calculate() {
    if (this.totalTrades === 0) return;

    this.winRate = (this.winningTrades / this.totalTrades) * 100;
    this.avgWin = this.winningTrades > 0 ? this.totalProfit / this.winningTrades : 0;
    this.avgLoss = this.losingTrades > 0 ? this.totalLoss / this.losingTrades : 0;
    this.profitFactor = this.totalLoss !== 0 ? this.totalProfit / Math.abs(this.totalLoss) : 0;

    // 计算夏普比率（简化版）
    if (this.trades.length > 0) {
      const returns = this.trades.map(t => t.profitPercent);
      const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
      const stdDev = Math.sqrt(
        returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length
      );
      this.sharpeRatio = stdDev !== 0 ? avgReturn / stdDev : 0;
    }

    // 计算最大回撤
    let peak = this.equity[0]?.balance || 0;
    for (const point of this.equity) {
      if (point.balance > peak) {
        peak = point.balance;
      }
      const drawdown = peak - point.balance;
      const drawdownPercent = peak !== 0 ? (drawdown / peak) * 100 : 0;

      if (drawdown > this.maxDrawdown) {
        this.maxDrawdown = drawdown;
        this.maxDrawdownPercent = drawdownPercent;
      }
    }
  }

  toJSON() {
    return {
      totalTrades: this.totalTrades,
      winningTrades: this.winningTrades,
      losingTrades: this.losingTrades,
      winRate: this.winRate.toFixed(2) + '%',
      totalProfit: this.totalProfit.toFixed(2),
      totalLoss: this.totalLoss.toFixed(2),
      netProfit: (this.totalProfit + this.totalLoss).toFixed(2),
      avgWin: this.avgWin.toFixed(2),
      avgLoss: this.avgLoss.toFixed(2),
      largestWin: this.largestWin.toFixed(2),
      largestLoss: this.largestLoss.toFixed(2),
      profitFactor: this.profitFactor.toFixed(2),
      sharpeRatio: this.sharpeRatio.toFixed(2),
      maxDrawdown: this.maxDrawdown.toFixed(2),
      maxDrawdownPercent: this.maxDrawdownPercent.toFixed(2) + '%'
    };
  }
}

/**
 * 回测引擎类
 */
export class Backtester {
  constructor(strategy, initialBalance = 10000, positionSize = 1.0) {
    this.strategy = strategy;
    this.initialBalance = initialBalance;
    this.balance = initialBalance;
    this.positionSize = positionSize; // 每次交易的仓位大小（手数或比例）
    this.currentTrade = null;
    this.stats = new BacktestStats();
  }

  /**
   * 运行回测
   * @param {Object[]} candles - K线数据
   * @returns {Object} 回测结果
   */
  run(candles) {
    console.log(`开始回测，初始资金: $${this.initialBalance}`);
    console.log(`数据周期: ${candles[0].time.toISOString().split('T')[0]} 至 ${candles[candles.length - 1].time.toISOString().split('T')[0]}`);
    console.log(`K线数量: ${candles.length}\n`);

    this.strategy.reset();
    this.balance = this.initialBalance;
    this.currentTrade = null;
    this.stats = new BacktestStats();

    // 记录初始权益
    this.stats.equity.push({
      time: candles[0].time,
      balance: this.balance
    });

    for (let i = 0; i < candles.length; i++) {
      const signal = this.strategy.generateSignal(candles, i);
      this.processSignal(signal, candles[i], i);

      // 记录权益曲线
      this.stats.equity.push({
        time: candles[i].time,
        balance: this.balance + (this.currentTrade ? this.currentTrade.unrealizedPL : 0)
      });
    }

    // 如果回测结束时还有持仓，强制平仓
    if (this.currentTrade) {
      const lastCandle = candles[candles.length - 1];
      this.closeTrade(lastCandle.close, lastCandle.time, '回测结束，强制平仓');
    }

    this.stats.calculate();

    return {
      initialBalance: this.initialBalance,
      finalBalance: this.balance,
      netProfit: this.balance - this.initialBalance,
      returnPercent: ((this.balance - this.initialBalance) / this.initialBalance) * 100,
      stats: this.stats.toJSON(),
      trades: this.stats.trades,
      equity: this.stats.equity
    };
  }

  /**
   * 处理交易信号
   * @param {Object} signal - 交易信号
   * @param {Object} candle - 当前K线
   * @param {number} index - K线索引
   */
  processSignal(signal, candle, index) {
    if (signal.signal === SignalType.LONG && !this.currentTrade) {
      this.openTrade(SignalType.LONG, signal.price, candle.time, signal.reason, index);
    } else if (signal.signal === SignalType.SHORT && !this.currentTrade) {
      this.openTrade(SignalType.SHORT, signal.price, candle.time, signal.reason, index);
    } else if (signal.signal === SignalType.CLOSE && this.currentTrade) {
      this.closeTrade(signal.price, candle.time, signal.reason);
    } else if (this.currentTrade) {
      // 更新未实现盈亏
      this.updateUnrealizedPL(candle.close);
    }
  }

  /**
   * 开仓
   * @param {string} type - 交易类型 (LONG/SHORT)
   * @param {number} price - 开仓价格
   * @param {Date} time - 开仓时间
   * @param {string} reason - 开仓原因
   * @param {number} index - K线索引
   */
  openTrade(type, price, time, reason, index) {
    // 计算实际仓位大小（基于当前余额）
    const positionValue = this.balance * this.positionSize;
    const quantity = positionValue / price; // 简化：假设1手=价格*数量

    this.currentTrade = {
      type,
      entryPrice: price,
      entryTime: time,
      entryIndex: index,
      quantity,
      positionValue,
      reason,
      unrealizedPL: 0
    };

    console.log(`[${time.toISOString().split('T')[0]}] 开仓 ${type} @ $${price.toFixed(2)} | ${reason}`);
  }

  /**
   * 平仓
   * @param {number} price - 平仓价格
   * @param {Date} time - 平仓时间
   * @param {string} reason - 平仓原因
   */
  closeTrade(price, time, reason) {
    if (!this.currentTrade) return;

    const priceDiff = this.currentTrade.type === SignalType.LONG
      ? price - this.currentTrade.entryPrice
      : this.currentTrade.entryPrice - price;

    const profit = priceDiff * this.currentTrade.quantity;
    const profitPercent = (priceDiff / this.currentTrade.entryPrice) * 100;

    this.balance += profit;

    const trade = {
      type: this.currentTrade.type,
      entryPrice: this.currentTrade.entryPrice,
      exitPrice: price,
      entryTime: this.currentTrade.entryTime,
      exitTime: time,
      quantity: this.currentTrade.quantity,
      profit: profit,
      profitPercent: profitPercent,
      entryReason: this.currentTrade.reason,
      exitReason: reason,
      duration: time.getTime() - this.currentTrade.entryTime.getTime()
    };

    this.stats.trades.push(trade);
    this.stats.totalTrades++;

    if (profit > 0) {
      this.stats.winningTrades++;
      this.stats.totalProfit += profit;
      if (profit > this.stats.largestWin) {
        this.stats.largestWin = profit;
      }
    } else {
      this.stats.losingTrades++;
      this.stats.totalLoss += profit;
      if (profit < this.stats.largestLoss) {
        this.stats.largestLoss = profit;
      }
    }

    console.log(
      `[${time.toISOString().split('T')[0]}] 平仓 ${this.currentTrade.type} @ $${price.toFixed(2)} | ` +
      `盈亏: $${profit.toFixed(2)} (${profitPercent > 0 ? '+' : ''}${profitPercent.toFixed(2)}%) | ` +
      `余额: $${this.balance.toFixed(2)} | ${reason}`
    );

    this.currentTrade = null;
  }

  /**
   * 更新未实现盈亏
   * @param {number} currentPrice - 当前价格
   */
  updateUnrealizedPL(currentPrice) {
    if (!this.currentTrade) return;

    const priceDiff = this.currentTrade.type === SignalType.LONG
      ? currentPrice - this.currentTrade.entryPrice
      : this.currentTrade.entryPrice - currentPrice;

    this.currentTrade.unrealizedPL = priceDiff * this.currentTrade.quantity;
  }
}

/**
 * 生成回测报告
 * @param {Object} result - 回测结果
 * @returns {string} 格式化的报告
 */
export function generateReport(result) {
  const lines = [];

  lines.push('='.repeat(80));
  lines.push('XAUUSD布林带震荡策略回测报告');
  lines.push('XAUUSD Bollinger Bands Range Strategy Backtest Report');
  lines.push('='.repeat(80));
  lines.push('');

  lines.push('总体表现 (Overall Performance):');
  lines.push('-'.repeat(80));
  lines.push(`初始资金 (Initial Balance):        $${result.initialBalance.toFixed(2)}`);
  lines.push(`最终资金 (Final Balance):          $${result.finalBalance.toFixed(2)}`);
  lines.push(`净利润 (Net Profit):               $${result.netProfit.toFixed(2)}`);
  lines.push(`收益率 (Return):                   ${result.returnPercent > 0 ? '+' : ''}${result.returnPercent.toFixed(2)}%`);
  lines.push('');

  lines.push('交易统计 (Trade Statistics):');
  lines.push('-'.repeat(80));
  lines.push(`总交易次数 (Total Trades):         ${result.stats.totalTrades}`);
  lines.push(`盈利交易 (Winning Trades):         ${result.stats.winningTrades}`);
  lines.push(`亏损交易 (Losing Trades):          ${result.stats.losingTrades}`);
  lines.push(`胜率 (Win Rate):                   ${result.stats.winRate}`);
  lines.push(`平均盈利 (Avg Win):                $${result.stats.avgWin}`);
  lines.push(`平均亏损 (Avg Loss):               $${result.stats.avgLoss}`);
  lines.push(`最大盈利 (Largest Win):            $${result.stats.largestWin}`);
  lines.push(`最大亏损 (Largest Loss):           $${result.stats.largestLoss}`);
  lines.push('');

  lines.push('风险指标 (Risk Metrics):');
  lines.push('-'.repeat(80));
  lines.push(`盈亏比 (Profit Factor):            ${result.stats.profitFactor}`);
  lines.push(`夏普比率 (Sharpe Ratio):           ${result.stats.sharpeRatio}`);
  lines.push(`最大回撤 (Max Drawdown):           $${result.stats.maxDrawdown} (${result.stats.maxDrawdownPercent})`);
  lines.push('');

  lines.push('='.repeat(80));

  // 添加最近的10笔交易
  if (result.trades.length > 0) {
    lines.push('');
    lines.push('最近交易记录 (Recent Trades):');
    lines.push('-'.repeat(80));

    const recentTrades = result.trades.slice(-10);
    for (const trade of recentTrades) {
      const entryDate = trade.entryTime.toISOString().split('T')[0];
      const exitDate = trade.exitTime.toISOString().split('T')[0];
      const profitStr = trade.profit > 0 ? `+$${trade.profit.toFixed(2)}` : `-$${Math.abs(trade.profit).toFixed(2)}`;
      const percentStr = trade.profitPercent > 0 ? `+${trade.profitPercent.toFixed(2)}%` : `${trade.profitPercent.toFixed(2)}%`;

      lines.push(
        `${trade.type.padEnd(5)} | ` +
        `入场: ${entryDate} @ $${trade.entryPrice.toFixed(2)} | ` +
        `出场: ${exitDate} @ $${trade.exitPrice.toFixed(2)} | ` +
        `${profitStr.padStart(10)} (${percentStr.padStart(8)})`
      );
    }
    lines.push('='.repeat(80));
  }

  return lines.join('\n');
}
