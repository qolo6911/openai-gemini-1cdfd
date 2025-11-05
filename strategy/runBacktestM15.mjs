#!/usr/bin/env node
import { BollingerRangeStrategyV2 } from './bollingerStrategyV2.mjs';
import { Backtester } from './backtester.mjs';
import { loadFromCSV } from './dataFetcher.mjs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function main() {
  const dataFile = join(__dirname, 'data', 'XAUUSDm_M15.csv');
  
  console.log('加载M15数据...');
  const candles = await loadFromCSV(dataFile);
  console.log(`成功加载 ${candles.length} 条M15数据\n`);

  // 优化配置
  const strategy = new BollingerRangeStrategyV2({
    atrStopLossMultiplier: 1.5,
    atrTakeProfitMultiplier: 4.0,
    adxThreshold: 20,
    maTrendThreshold: 0.01
  });
  
  const backtester = new Backtester(strategy, 10000, 1.0);
  backtester.verbose = false; // 静默模式
  
  console.log('M15周期回测中...\n');
  const result = backtester.run(candles, false);
  
  console.log('='.repeat(80));
  console.log('M15回测结果 - 优化配置');
  console.log('='.repeat(80));
  console.log(`收益率: ${result.returnPercent.toFixed(2)}%`);
  console.log(`总交易: ${result.stats.totalTrades}`);
  console.log(`胜率: ${result.stats.winRate}`);
  console.log(`盈亏比: ${result.stats.profitFactor}`);
  console.log(`夏普比率: ${result.stats.sharpeRatio}`);
  console.log(`最大回撤: ${result.stats.maxDrawdownPercent}`);
  console.log('='.repeat(80));
}

main().catch(console.error);
