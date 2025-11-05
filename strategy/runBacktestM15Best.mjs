#!/usr/bin/env node
/**
 * M15周期最优配置回测
 * 使用H1验证过的最优参数在M15上测试
 */

import { BollingerRangeStrategyV2 } from './bollingerStrategyV2.mjs';
import { Backtester } from './backtester.mjs';
import { loadFromCSV } from './dataFetcher.mjs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function main() {
  const dataFile = join(__dirname, 'data', 'XAUUSDm_M15.csv');
  
  console.log('='.repeat(80));
  console.log('M15周期最优配置回测');
  console.log('='.repeat(80));
  console.log('');
  
  console.log('加载M15数据...');
  const candles = await loadFromCSV(dataFile);
  console.log(`成功加载 ${candles.length} 条M15数据`);
  console.log(`时间范围: ${candles[0].time.toISOString().split('T')[0]} 至 ${candles[candles.length-1].time.toISOString().split('T')[0]}`);
  console.log('');

  // 使用H1验证的最优配置
  const config = {
    bollingerPeriod: 20,
    bollingerStdDev: 2.5,
    angleThreshold: 20,
    
    // 最优止盈止损
    atrStopLossMultiplier: 1.2,
    atrTakeProfitMultiplier: 6.0,
    
    // 过滤器
    useATR: true,
    useMAFilter: true,
    useADXFilter: true,
    
    adxThreshold: 20,
    maTrendThreshold: 0.01,
    
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
  backtester.verbose = false;
  
  console.log('开始回测...\n');
  const result = backtester.run(candles, false);
  
  console.log('='.repeat(80));
  console.log('回测结果 - M15周期最优配置');
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
  console.log('='.repeat(80));
  console.log('');
  
  // 与H1对比
  console.log('📊 与H1周期对比:');
  console.log('  H1周期: 收益率 16.03%, 盈亏比 1.10, 胜率 57.28%, 交易数 728');
  console.log(`  M15周期: 收益率 ${result.returnPercent.toFixed(2)}%, 盈亏比 ${result.stats.profitFactor}, 胜率 ${result.stats.winRate}, 交易数 ${result.stats.totalTrades}`);
  console.log('');
  
  if (parseFloat(result.returnPercent) < 0) {
    console.log('⚠️  警告: M15周期收益为负，不推荐使用');
    console.log('💡 建议: 使用H1周期策略 (收益率 16.03%)');
  } else if (parseFloat(result.returnPercent) < 10) {
    console.log('⚠️  M15周期收益率较低');
    console.log('💡 建议: H1周期表现更优 (收益率 16.03%)');
  } else {
    console.log('✅ M15周期表现良好');
  }
  console.log('');
}

main().catch(error => {
  console.error('回测失败:', error);
  process.exit(1);
});
