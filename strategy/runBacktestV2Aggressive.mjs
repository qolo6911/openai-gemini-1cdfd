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
  
  console.log('测试激进配置：更大止盈/止损比...\n');
  const candles = await loadFromCSV(dataFile);

  // 配置1: 止损1.5x, 止盈5.0x (提高盈亏比)
  console.log('=== 配置1: 止损1.5x ATR, 止盈5.0x ATR ===');
  const strategy1 = new BollingerRangeStrategyV2({
    atrStopLossMultiplier: 1.5,
    atrTakeProfitMultiplier: 5.0,  // 从4.0提高到5.0
    adxThreshold: 20,
    maTrendThreshold: 0.01
  });
  const backtester1 = new Backtester(strategy1, 10000, 1.0);
  backtester1.verbose = false;
  const result1 = backtester1.run(candles, false);
  
  console.log(`收益率: ${result1.returnPercent.toFixed(2)}%`);
  console.log(`盈亏比: ${result1.stats.profitFactor}`);
  console.log(`胜率: ${result1.stats.winRate}`);
  console.log(`最大回撤: ${result1.stats.maxDrawdownPercent}\n`);

  // 配置2: 止损1.2x, 止盈4.5x (更紧止损+大止盈)
  console.log('=== 配置2: 止损1.2x ATR, 止盈4.5x ATR ===');
  const strategy2 = new BollingerRangeStrategyV2({
    atrStopLossMultiplier: 1.2,  // 更紧
    atrTakeProfitMultiplier: 4.5,
    adxThreshold: 20,
    maTrendThreshold: 0.01
  });
  const backtester2 = new Backtester(strategy2, 10000, 1.0);
  backtester2.verbose = false;
  const result2 = backtester2.run(candles, false);
  
  console.log(`收益率: ${result2.returnPercent.toFixed(2)}%`);
  console.log(`盈亏比: ${result2.stats.profitFactor}`);
  console.log(`胜率: ${result2.stats.winRate}`);
  console.log(`最大回撤: ${result2.stats.maxDrawdownPercent}\n`);

  // 配置3: 止损1.0x, 止盈4.0x (最紧止损)
  console.log('=== 配置3: 止损1.0x ATR, 止盈4.0x ATR ===');
  const strategy3 = new BollingerRangeStrategyV2({
    atrStopLossMultiplier: 1.0,  // 最紧
    atrTakeProfitMultiplier: 4.0,
    adxThreshold: 20,
    maTrendThreshold: 0.01
  });
  const backtester3 = new Backtester(strategy3, 10000, 1.0);
  backtester3.verbose = false;
  const result3 = backtester3.run(candles, false);
  
  console.log(`收益率: ${result3.returnPercent.toFixed(2)}%`);
  console.log(`盈亏比: ${result3.stats.profitFactor}`);
  console.log(`胜率: ${result3.stats.winRate}`);
  console.log(`最大回撤: ${result3.stats.maxDrawdownPercent}\n`);

  console.log('='.repeat(80));
  console.log('推荐: 选择盈亏比>1.2且收益率最高的配置');
  console.log('='.repeat(80));
}

main().catch(console.error);
