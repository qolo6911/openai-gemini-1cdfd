#!/usr/bin/env node
import { BollingerRangeStrategyV2 } from './bollingerStrategyV2.mjs';
import { Backtester } from './backtester.mjs';
import { loadFromCSV } from './dataFetcher.mjs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function testConfig(config, name) {
  const dataFile = join(__dirname, 'data', 'XAUUSDm_H1.csv');
  const candles = await loadFromCSV(dataFile);
  
  const strategy = new BollingerRangeStrategyV2(config);
  const backtester = new Backtester(strategy, 10000, 1.0);
  backtester.verbose = false;
  
  const result = backtester.run(candles, false);
  
  console.log(`\n${name}:`);
  console.log(`  收益率: ${result.returnPercent.toFixed(2)}%`);
  console.log(`  盈亏比: ${result.stats.profitFactor}`);
  console.log(`  胜率: ${result.stats.winRate}`);
  console.log(`  交易数: ${result.stats.totalTrades}`);
  console.log(`  最大回撤: ${result.stats.maxDrawdownPercent}`);
  
  return result;
}

async function main() {
  console.log('测试3种激进配置...\n');
  
  // 配置1: 极度激进 - 止损1.0x, 止盈5.0x
  await testConfig({
    atrStopLossMultiplier: 1.0,
    atrTakeProfitMultiplier: 5.0,
    adxThreshold: 20,
    maTrendThreshold: 0.01
  }, '配置1 (止损1.0x, 止盈5.0x)');
  
  // 配置2: 激进 - 止损1.5x, 止盈5.0x
  await testConfig({
    atrStopLossMultiplier: 1.5,
    atrTakeProfitMultiplier: 5.0,
    adxThreshold: 20,
    maTrendThreshold: 0.01
  }, '配置2 (止损1.5x, 止盈5.0x)');
  
  // 配置3: 平衡激进 - 止损1.2x, 止盈6.0x
  await testConfig({
    atrStopLossMultiplier: 1.2,
    atrTakeProfitMultiplier: 6.0,
    adxThreshold: 20,
    maTrendThreshold: 0.01
  }, '配置3 (止损1.2x, 止盈6.0x)');
}

main().catch(console.error);
