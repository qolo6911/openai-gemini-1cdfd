#!/usr/bin/env node
/**
 * H1周期最优配置回测
 * 配置: 止损1.2x ATR, 止盈6.0x ATR
 * 验证结果: 收益率16.03%, 盈亏比1.10, 胜率57.28%
 */

import { BollingerRangeStrategyV2 } from './bollingerStrategyV2.mjs';
import { Backtester } from './backtester.mjs';
import { loadFromCSV } from './dataFetcher.mjs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function main() {
  const dataFile = join(__dirname, 'data', 'XAUUSDm_H1.csv');
  
  console.log('='.repeat(80));
  console.log('H1周期最优配置回测');
  console.log('='.repeat(80));
  console.log('');
  
  console.log('加载H1数据...');
  const candles = await loadFromCSV(dataFile);
  console.log(`成功加载 ${candles.length} 条H1数据`);
  console.log(`时间范围: ${candles[0].time.toISOString().split('T')[0]} 至 ${candles[candles.length-1].time.toISOString().split('T')[0]}`);
  console.log('');

  // H1最优配置
  const config = {
    bollingerPeriod: 20,
    bollingerStdDev: 2.5,
    angleThreshold: 20,
    
    // 最优止盈止损
    atrStopLossMultiplier: 1.2,    // 止损 1.2x ATR
    atrTakeProfitMultiplier: 6.0,  // 止盈 6.0x ATR
    
    // 过滤器
    useATR: true,
    useMAFilter: true,
    useADXFilter: true,
    
    adxThreshold: 20,              // ADX < 20 才交易（震荡市场）
    maTrendThreshold: 0.01,        // MA趋势阈值 1%
    
    maShortPeriod: 50,
    maLongPeriod: 200
  };
  
  console.log('策略配置:');
  console.log(`  布林带: 周期${config.bollingerPeriod}, 标准差${config.bollingerStdDev}`);
  console.log(`  止损: ${config.atrStopLossMultiplier}x ATR`);
  console.log(`  止盈: ${config.atrTakeProfitMultiplier}x ATR`);
  console.log(`  ADX阈值: < ${config.adxThreshold}`);
  console.log(`  MA趋势阈值: ${(config.maTrendThreshold * 100).toFixed(1)}%`);
  console.log('');
  
  const strategy = new BollingerRangeStrategyV2(config);
  const backtester = new Backtester(strategy, 10000, 1.0);
  
  const result = backtester.run(candles);
  
  console.log('\n' + '='.repeat(80));
  console.log('回测结果 - H1周期最优配置');
  console.log('='.repeat(80));
  console.log(`初始资金: $${result.initialBalance.toFixed(2)}`);
  console.log(`最终资金: $${result.finalBalance.toFixed(2)}`);
  console.log(`净收益: $${result.netProfit.toFixed(2)}`);
  console.log(`收益率: ${result.returnPercent.toFixed(2)}%`);
  console.log('');
  console.log('交易统计:');
  console.log(`  总交易: ${result.stats.totalTrades}`);
  console.log(`  盈利交易: ${result.stats.winningTrades}`);
  console.log(`  亏损交易: ${result.stats.losingTrades}`);
  console.log(`  胜率: ${result.stats.winRate}`);
  console.log('');
  console.log('性能指标:');
  console.log(`  盈亏比: ${result.stats.profitFactor}`);
  console.log(`  夏普比率: ${result.stats.sharpeRatio}`);
  console.log(`  最大回撤: ${result.stats.maxDrawdownPercent}`);
  console.log(`  平均盈利: $${result.stats.avgWin}`);
  console.log(`  平均亏损: $${result.stats.avgLoss}`);
  console.log(`  最大盈利: $${result.stats.largestWin}`);
  console.log(`  最大亏损: $${result.stats.largestLoss}`);
  console.log('='.repeat(80));
  console.log('');
  console.log('💡 使用建议:');
  console.log('  - 适用周期: H1 (1小时)');
  console.log('  - 市场类型: 震荡市场 (ADX < 20)');
  console.log('  - 风险水平: 中等 (最大回撤 ~13%)');
  console.log('  - 交易频率: 中等 (~700笔/3年)');
  console.log('');
}

main().catch(error => {
  console.error('回测失败:', error);
  process.exit(1);
});
