#!/usr/bin/env node
import { BollingerRangeStrategyV2 } from './bollingerStrategyV2.mjs';
import { Backtester } from './backtester.mjs';
import { loadFromCSV } from './dataFetcher.mjs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function main() {
  const dataFile = join(__dirname, 'data', 'XAUUSDm_H1.csv');
  
  console.log('加载数据...');
  const candles = await loadFromCSV(dataFile);
  console.log(`成功加载 ${candles.length} 条H1数据\n`);

  const strategy = new BollingerRangeStrategyV2();
  const backtester = new Backtester(strategy, 10000, 1.0);
  
  const result = backtester.run(candles);
  
  console.log('\n' + '='.repeat(80));
  console.log('回测结果 - 策略V2 (ATR+MA+ADX优化版)');
  console.log('='.repeat(80));
  console.log(`初始资金: $${result.initialBalance}`);
  console.log(`最终资金: $${result.finalBalance.toFixed(2)}`);
  console.log(`净收益: $${result.netProfit.toFixed(2)}`);
  console.log(`收益率: ${result.returnPercent.toFixed(2)}%`);
  console.log('');
  console.log('统计数据:');
  console.log(`  总交易: ${result.stats.totalTrades}`);
  console.log(`  胜率: ${result.stats.winRate}`);
  console.log(`  盈亏比: ${result.stats.profitFactor}`);
  console.log(`  夏普比率: ${result.stats.sharpeRatio}`);
  console.log(`  最大回撤: ${result.stats.maxDrawdownPercent}`);
  console.log('='.repeat(80));
}

main().catch(console.error);
