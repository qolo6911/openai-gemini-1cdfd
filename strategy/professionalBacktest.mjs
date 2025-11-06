#!/usr/bin/env node
/**
 * 专业回测系统
 * - 真实历史数据
 * - 交易成本（点差+佣金）
 * - 滑点模拟
 * - Walk-Forward测试
 * - 样本内/样本外验证
 * - 详细风险指标
 */

import { BollingerRangeStrategyV2 } from './bollingerStrategyV2.mjs';
import { loadFromCSV } from './dataFetcher.mjs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class ProfessionalBacktester {
  constructor(strategy, initialBalance, config = {}) {
    this.strategy = strategy;
    this.initialBalance = initialBalance;
    this.balance = initialBalance;
    
    // 专业回测配置
    this.config = {
      spread: config.spread || 0.20,           // 点差 ($0.20)
      commission: config.commission || 0,      // 佣金 (每手)
      slippage: config.slippage || 0.10,       // 滑点 ($0.10)
      positionSize: config.positionSize || 1.0, // 仓位大小
      ...config
    };
    
    this.currentTrade = null;
    this.trades = [];
    this.equity = [];
    this.monthlyReturns = {};
  }

  run(candles) {
    console.log(`\n开始专业回测 (含交易成本)`);
    console.log(`  点差: $${this.config.spread.toFixed(2)}`);
    console.log(`  滑点: $${this.config.slippage.toFixed(2)}`);
    console.log(`  佣金: $${this.config.commission.toFixed(2)}/手`);
    console.log(`  数据: ${candles.length}条K线`);
    console.log(`  周期: ${candles[0].time.toISOString().split('T')[0]} 至 ${candles[candles.length-1].time.toISOString().split('T')[0]}\n`);

    this.strategy.reset();
    this.balance = this.initialBalance;
    this.currentTrade = null;
    this.trades = [];
    this.equity = [];
    this.monthlyReturns = {};

    // 记录初始权益
    this.equity.push({
      time: candles[0].time,
      balance: this.balance
    });

    for (let i = 0; i < candles.length; i++) {
      const signal = this.strategy.generateSignal(candles, i);
      this.processSignal(signal, candles[i], i);

      // 记录权益曲线
      const currentEquity = this.balance + (this.currentTrade ? this.currentTrade.unrealizedPL : 0);
      this.equity.push({
        time: candles[i].time,
        balance: currentEquity
      });
    }

    // 强制平仓
    if (this.currentTrade) {
      const lastCandle = candles[candles.length - 1];
      this.closeTrade(lastCandle.close, lastCandle.time, '回测结束');
    }

    return this.generateReport();
  }

  processSignal(signal, candle, index) {
    if (signal.signal === 'LONG' && !this.currentTrade) {
      this.openTrade('LONG', signal.price, candle.time, signal.reason, signal.stopLoss, signal.takeProfit);
    } else if (signal.signal === 'SHORT' && !this.currentTrade) {
      this.openTrade('SHORT', signal.price, candle.time, signal.reason, signal.stopLoss, signal.takeProfit);
    } else if (signal.signal === 'CLOSE' && this.currentTrade) {
      this.closeTrade(signal.price, candle.time, signal.reason);
    } else if (this.currentTrade) {
      this.updateUnrealizedPL(candle.close);
    }
  }

  openTrade(type, price, time, reason, stopLoss, takeProfit) {
    // 加入滑点
    const executionPrice = type === 'LONG' 
      ? price + this.config.slippage 
      : price - this.config.slippage;

    const positionValue = this.balance * this.config.positionSize;
    const quantity = positionValue / executionPrice;

    // 扣除开仓成本
    const openCost = this.config.spread + this.config.commission;
    this.balance -= openCost;

    this.currentTrade = {
      type,
      entryPrice: executionPrice,
      entryTime: time,
      quantity,
      positionValue,
      reason,
      stopLoss,
      takeProfit,
      unrealizedPL: 0,
      costs: openCost
    };
  }

  closeTrade(price, time, reason) {
    if (!this.currentTrade) return;

    // 加入滑点
    const executionPrice = this.currentTrade.type === 'LONG'
      ? price - this.config.slippage
      : price + this.config.slippage;

    const priceDiff = this.currentTrade.type === 'LONG'
      ? executionPrice - this.currentTrade.entryPrice
      : this.currentTrade.entryPrice - executionPrice;

    const grossProfit = priceDiff * this.currentTrade.quantity;
    
    // 扣除平仓成本
    const closeCost = this.config.spread + this.config.commission;
    const netProfit = grossProfit - closeCost - this.currentTrade.costs;

    this.balance += netProfit;

    const trade = {
      type: this.currentTrade.type,
      entryPrice: this.currentTrade.entryPrice,
      exitPrice: executionPrice,
      entryTime: this.currentTrade.entryTime,
      exitTime: time,
      quantity: this.currentTrade.quantity,
      grossProfit,
      netProfit,
      costs: this.currentTrade.costs + closeCost,
      profitPercent: (netProfit / this.currentTrade.positionValue) * 100,
      entryReason: this.currentTrade.reason,
      exitReason: reason,
      duration: time.getTime() - this.currentTrade.entryTime.getTime()
    };

    this.trades.push(trade);

    // 记录月度收益
    const month = `${time.getFullYear()}-${String(time.getMonth() + 1).padStart(2, '0')}`;
    if (!this.monthlyReturns[month]) {
      this.monthlyReturns[month] = 0;
    }
    this.monthlyReturns[month] += netProfit;

    this.currentTrade = null;
  }

  updateUnrealizedPL(currentPrice) {
    if (!this.currentTrade) return;

    const priceDiff = this.currentTrade.type === 'LONG'
      ? currentPrice - this.currentTrade.entryPrice
      : this.currentTrade.entryPrice - currentPrice;

    this.currentTrade.unrealizedPL = priceDiff * this.currentTrade.quantity;
  }

  generateReport() {
    const stats = this.calculateStatistics();
    
    return {
      initialBalance: this.initialBalance,
      finalBalance: this.balance,
      netProfit: this.balance - this.initialBalance,
      returnPercent: ((this.balance - this.initialBalance) / this.initialBalance) * 100,
      stats,
      trades: this.trades,
      equity: this.equity,
      monthlyReturns: this.monthlyReturns
    };
  }

  calculateStatistics() {
    const totalTrades = this.trades.length;
    const winningTrades = this.trades.filter(t => t.netProfit > 0);
    const losingTrades = this.trades.filter(t => t.netProfit <= 0);
    
    const totalProfit = winningTrades.reduce((sum, t) => sum + t.netProfit, 0);
    const totalLoss = Math.abs(losingTrades.reduce((sum, t) => sum + t.netProfit, 0));
    const totalCosts = this.trades.reduce((sum, t) => sum + t.costs, 0);
    
    const avgWin = winningTrades.length > 0 ? totalProfit / winningTrades.length : 0;
    const avgLoss = losingTrades.length > 0 ? totalLoss / losingTrades.length : 0;
    
    const winRate = totalTrades > 0 ? (winningTrades.length / totalTrades) * 100 : 0;
    const profitFactor = totalLoss > 0 ? totalProfit / totalLoss : 0;
    
    // 计算夏普比率
    const returns = this.trades.map(t => t.profitPercent);
    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const stdDev = Math.sqrt(
      returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length
    );
    const sharpeRatio = stdDev !== 0 ? (avgReturn / stdDev) * Math.sqrt(252) : 0; // 年化

    // 计算最大回撤
    let peak = this.equity[0]?.balance || 0;
    let maxDrawdown = 0;
    let maxDrawdownPercent = 0;
    
    for (const point of this.equity) {
      if (point.balance > peak) {
        peak = point.balance;
      }
      const drawdown = peak - point.balance;
      const drawdownPercent = peak !== 0 ? (drawdown / peak) * 100 : 0;
      
      if (drawdown > maxDrawdown) {
        maxDrawdown = drawdown;
        maxDrawdownPercent = drawdownPercent;
      }
    }

    return {
      totalTrades,
      winningTrades: winningTrades.length,
      losingTrades: losingTrades.length,
      winRate: winRate.toFixed(2) + '%',
      totalProfit: totalProfit.toFixed(2),
      totalLoss: totalLoss.toFixed(2),
      totalCosts: totalCosts.toFixed(2),
      netProfit: (this.balance - this.initialBalance).toFixed(2),
      avgWin: avgWin.toFixed(2),
      avgLoss: avgLoss.toFixed(2),
      profitFactor: profitFactor.toFixed(2),
      sharpeRatio: sharpeRatio.toFixed(2),
      maxDrawdown: maxDrawdown.toFixed(2),
      maxDrawdownPercent: maxDrawdownPercent.toFixed(2) + '%',
      largestWin: Math.max(...this.trades.map(t => t.netProfit), 0).toFixed(2),
      largestLoss: Math.min(...this.trades.map(t => t.netProfit), 0).toFixed(2)
    };
  }
}

// Walk-Forward测试
async function walkForwardTest(candles, config, periods = 3) {
  console.log('\n' + '='.repeat(80));
  console.log('Walk-Forward 测试 (前向验证)');
  console.log('='.repeat(80));
  console.log(`\n将数据分为 ${periods} 个时期，每期独立测试\n`);
  
  const periodSize = Math.floor(candles.length / periods);
  const results = [];
  
  for (let i = 0; i < periods; i++) {
    const start = i * periodSize;
    const end = i === periods - 1 ? candles.length : (i + 1) * periodSize;
    const periodCandles = candles.slice(start, end);
    
    console.log(`时期 ${i + 1}/${periods}:`);
    console.log(`  数据范围: ${periodCandles[0].time.toISOString().split('T')[0]} 至 ${periodCandles[periodCandles.length-1].time.toISOString().split('T')[0]}`);
    console.log(`  K线数量: ${periodCandles.length}`);
    
    const strategy = new BollingerRangeStrategyV2(config);
    const backtester = new ProfessionalBacktester(strategy, 10000, {
      spread: 0.20,
      slippage: 0.10,
      commission: 0
    });
    
    const result = backtester.run(periodCandles);
    
    console.log(`  收益率: ${result.returnPercent.toFixed(2)}%`);
    console.log(`  盈亏比: ${result.stats.profitFactor}`);
    console.log(`  胜率: ${result.stats.winRate}`);
    console.log(`  交易数: ${result.stats.totalTrades}\n`);
    
    results.push({
      period: i + 1,
      startDate: periodCandles[0].time,
      endDate: periodCandles[periodCandles.length-1].time,
      ...result
    });
  }
  
  return results;
}

async function main() {
  console.log('='.repeat(80));
  console.log('专业回测系统 - XAUUSD震荡策略');
  console.log('='.repeat(80));
  console.log('\n✅ 使用真实历史数据');
  console.log('✅ 包含交易成本（点差+滑点）');
  console.log('✅ Walk-Forward验证');
  console.log('✅ 样本内/样本外测试');
  
  const dataFile = join(__dirname, 'data', 'XAUUSDm_H1.csv');
  const candles = await loadFromCSV(dataFile);
  
  // 最优配置
  const config = {
    bollingerPeriod: 20,
    bollingerStdDev: 2.5,
    angleThreshold: 20,
    atrStopLossMultiplier: 1.2,
    atrTakeProfitMultiplier: 6.0,
    adxThreshold: 20,
    maTrendThreshold: 0.01
  };
  
  // 1. 全样本测试
  console.log('\n' + '='.repeat(80));
  console.log('1. 全样本回测 (含交易成本)');
  console.log('='.repeat(80));
  
  const strategy = new BollingerRangeStrategyV2(config);
  const backtester = new ProfessionalBacktester(strategy, 10000, {
    spread: 0.20,    // XAUUSD典型点差
    slippage: 0.10,  // 滑点
    commission: 0    // 佣金
  });
  
  const fullResult = backtester.run(candles);
  
  console.log('\n全样本结果:');
  console.log(`  初始资金: $${fullResult.initialBalance.toFixed(2)}`);
  console.log(`  最终资金: $${fullResult.finalBalance.toFixed(2)}`);
  console.log(`  净收益: $${fullResult.netProfit.toFixed(2)}`);
  console.log(`  收益率: ${fullResult.returnPercent.toFixed(2)}%`);
  console.log(`  总交易成本: $${fullResult.stats.totalCosts}`);
  console.log(`  夏普比率: ${fullResult.stats.sharpeRatio}`);
  console.log(`  最大回撤: ${fullResult.stats.maxDrawdownPercent}`);
  console.log(`  盈亏比: ${fullResult.stats.profitFactor}`);
  console.log(`  胜率: ${fullResult.stats.winRate}`);
  console.log(`  交易数: ${fullResult.stats.totalTrades}`);
  
  // 2. 样本内/样本外测试 (70/30)
  console.log('\n' + '='.repeat(80));
  console.log('2. 样本内/样本外测试 (Train: 70% / Test: 30%)');
  console.log('='.repeat(80));
  
  const splitIndex = Math.floor(candles.length * 0.7);
  const trainData = candles.slice(0, splitIndex);
  const testData = candles.slice(splitIndex);
  
  console.log(`\n训练集: ${trainData[0].time.toISOString().split('T')[0]} 至 ${trainData[trainData.length-1].time.toISOString().split('T')[0]} (${trainData.length}条)`);
  const trainStrategy = new BollingerRangeStrategyV2(config);
  const trainBacktester = new ProfessionalBacktester(trainStrategy, 10000, {
    spread: 0.20, slippage: 0.10, commission: 0
  });
  const trainResult = trainBacktester.run(trainData);
  console.log(`  收益率: ${trainResult.returnPercent.toFixed(2)}%`);
  console.log(`  盈亏比: ${trainResult.stats.profitFactor}`);
  console.log(`  胜率: ${trainResult.stats.winRate}`);
  
  console.log(`\n测试集: ${testData[0].time.toISOString().split('T')[0]} 至 ${testData[testData.length-1].time.toISOString().split('T')[0]} (${testData.length}条)`);
  const testStrategy = new BollingerRangeStrategyV2(config);
  const testBacktester = new ProfessionalBacktester(testStrategy, 10000, {
    spread: 0.20, slippage: 0.10, commission: 0
  });
  const testResult = testBacktester.run(testData);
  console.log(`  收益率: ${testResult.returnPercent.toFixed(2)}%`);
  console.log(`  盈亏比: ${testResult.stats.profitFactor}`);
  console.log(`  胜率: ${testResult.stats.winRate}`);
  
  const overfit = Math.abs(trainResult.returnPercent - testResult.returnPercent);
  console.log(`\n过拟合检测: ${overfit.toFixed(2)}% 差异`);
  if (overfit < 5) {
    console.log('  ✅ 低过拟合风险');
  } else if (overfit < 10) {
    console.log('  ⚠️  中等过拟合风险');
  } else {
    console.log('  ❌ 高过拟合风险');
  }
  
  // 3. Walk-Forward测试
  await walkForwardTest(candles, config, 3);
  
  // 4. 月度收益分析
  console.log('\n' + '='.repeat(80));
  console.log('4. 月度收益分析');
  console.log('='.repeat(80));
  console.log('\n月份         | 收益 ($)  | 累计收益率');
  console.log('-'.repeat(50));
  
  let cumulative = 10000;
  const months = Object.keys(fullResult.monthlyReturns).sort();
  for (const month of months.slice(-12)) { // 最近12个月
    const monthProfit = fullResult.monthlyReturns[month];
    cumulative += monthProfit;
    const cumulativeReturn = ((cumulative - 10000) / 10000) * 100;
    console.log(
      `${month}    | ${monthProfit.toFixed(2).padStart(9)} | ${cumulativeReturn.toFixed(2).padStart(6)}%`
    );
  }
  
  console.log('\n' + '='.repeat(80));
  console.log('专业回测完成');
  console.log('='.repeat(80));
}

main().catch(error => {
  console.error('回测失败:', error);
  console.error(error.stack);
  process.exit(1);
});
