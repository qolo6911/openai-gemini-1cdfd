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

  // 优化配置：更小止损，更大止盈
  const strategy = new BollingerRangeStrategyV2({
    bollingerPeriod: 20,
    bollingerStdDev: 2.5,
    angleThreshold: 20,
    atrStopLossMultiplier: 1.5,    // 从2.0降到1.5（更小止损）
    atrTakeProfitMultiplier: 4.0,  // 从3.0升到4.0（更大止盈）
    adxThreshold: 20,              // 从25降到20（更严格）
    maTrendThreshold: 0.01         // 从0.02降到0.01（更敏感）
  });
  
  const backtester = new Backtester(strategy, 10000, 1.0);
  
  console.log('配置: 止损1.5x ATR, 止盈4.0x ATR, ADX<20, MA阈值1%\n');
  const result = backtester.run(candles);
  
  console.log('\n' + '='.repeat(80));
  console.log('回测结果 - 策略V2优化版 (调整止盈止损比例)');
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
