#!/usr/bin/env node
/**
 * 双周期策略回测
 * H4判断趋势 + H1执行交易
 */

import { DualTimeframeStrategy } from './dualTimeframeStrategy.mjs';
import { Backtester } from './backtester.mjs';
import { loadFromCSV } from './dataFetcher.mjs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function main() {
  console.log('='.repeat(80));
  console.log('双周期策略回测 (H4趋势 + H1执行)');
  console.log('='.repeat(80));
  console.log('');
  
  const dataFile = join(__dirname, 'data', 'XAUUSDm_H1.csv');
  
  console.log('加载H1数据...');
  const candles = await loadFromCSV(dataFile);
  console.log(`成功加载 ${candles.length} 条H1数据`);
  console.log(`时间范围: ${candles[0].time.toISOString().split('T')[0]} 至 ${candles[candles.length-1].time.toISOString().split('T')[0]}`);
  console.log('');

  // 测试3种配置
  const configs = [
    {
      name: '配置1: H4震荡过滤',
      config: {
        requireH4Oscillation: true,
        requireH4Align: false
      }
    },
    {
      name: '配置2: H4趋势对齐',
      config: {
        requireH4Oscillation: false,
        requireH4Align: true
      }
    },
    {
      name: '配置3: H4震荡+趋势对齐',
      config: {
        requireH4Oscillation: true,
        requireH4Align: true
      }
    }
  ];

  const results = [];

  for (const { name, config } of configs) {
    console.log(`\n测试 ${name}...`);
    
    const strategy = new DualTimeframeStrategy(config);
    const backtester = new Backtester(strategy, 10000, 1.0);
    backtester.verbose = false;
    
    const result = backtester.run(candles, false);
    
    results.push({ name, result });
    
    console.log(`  收益率: ${result.returnPercent.toFixed(2)}%`);
    console.log(`  盈亏比: ${result.stats.profitFactor}`);
    console.log(`  胜率: ${result.stats.winRate}`);
    console.log(`  交易数: ${result.stats.totalTrades}`);
    console.log(`  最大回撤: ${result.stats.maxDrawdownPercent}`);
  }

  // 输出对比表格
  console.log('\n' + '='.repeat(80));
  console.log('双周期策略对比结果');
  console.log('='.repeat(80));
  console.log('');
  console.log('配置                     | 收益率   | 盈亏比 | 胜率    | 交易数 | 最大回撤');
  console.log('-'.repeat(80));
  
  for (const { name, result } of results) {
    const configName = name.replace('配置1: ', '').replace('配置2: ', '').replace('配置3: ', '');
    console.log(
      `${configName.padEnd(24)} | ` +
      `${result.returnPercent.toFixed(2).padStart(7)}% | ` +
      `${result.stats.profitFactor.padStart(6)} | ` +
      `${result.stats.winRate.padStart(7)} | ` +
      `${result.stats.totalTrades.toString().padStart(6)} | ` +
      `${result.stats.maxDrawdownPercent}`
    );
  }
  
  console.log('='.repeat(80));
  console.log('');
  console.log('💡 说明:');
  console.log('  H4震荡过滤: 仅在H4周期ADX<25时交易（更保守）');
  console.log('  H4趋势对齐: H4和H1趋势方向一致才交易');
  console.log('  双重过滤: 同时满足震荡和趋势对齐');
  console.log('');
}

main().catch(error => {
  console.error('回测失败:', error);
  process.exit(1);
});
