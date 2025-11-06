#!/usr/bin/env node
/**
 * 同时训练H1和M15周期
 * 直接测试关键参数组合，避免大规模网格搜索导致的异常退出
 */

import { BollingerRangeStrategyV2 } from './bollingerStrategyV2.mjs';
import { Backtester } from './backtester.mjs';
import { loadFromCSV } from './dataFetcher.mjs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function testConfig(candles, config, name) {
  const strategy = new BollingerRangeStrategyV2(config);
  const backtester = new Backtester(strategy, 10000, 1.0);
  backtester.verbose = false;
  
  const result = backtester.run(candles, false);
  
  return {
    name,
    config,
    returnPercent: result.returnPercent,
    profitFactor: parseFloat(result.stats.profitFactor),
    winRate: parseFloat(result.stats.winRate.replace('%', '')),
    trades: result.stats.totalTrades,
    maxDD: parseFloat(result.stats.maxDrawdownPercent.replace('%', ''))
  };
}

async function trainTimeframe(timeframe, dataFile) {
  console.log(`\n${'='.repeat(80)}`);
  console.log(`开始训练 ${timeframe} 周期`);
  console.log('='.repeat(80));
  
  console.log(`加载 ${timeframe} 数据...`);
  const candles = await loadFromCSV(dataFile);
  console.log(`成功加载 ${candles.length} 条数据\n`);
  
  // 关键参数组合（避免大规模搜索）
  const configs = [
    // 当前最优配置
    {
      name: '当前最优 (1.2x/6.0x)',
      config: {
        atrStopLossMultiplier: 1.2,
        atrTakeProfitMultiplier: 6.0,
        adxThreshold: 20,
        maTrendThreshold: 0.01
      }
    },
    // 更激进止盈
    {
      name: '激进止盈 (1.2x/8.0x)',
      config: {
        atrStopLossMultiplier: 1.2,
        atrTakeProfitMultiplier: 8.0,
        adxThreshold: 20,
        maTrendThreshold: 0.01
      }
    },
    // 更紧止损
    {
      name: '紧止损 (1.0x/6.0x)',
      config: {
        atrStopLossMultiplier: 1.0,
        atrTakeProfitMultiplier: 6.0,
        adxThreshold: 20,
        maTrendThreshold: 0.01
      }
    },
    // 平衡配置
    {
      name: '平衡配置 (1.5x/5.0x)',
      config: {
        atrStopLossMultiplier: 1.5,
        atrTakeProfitMultiplier: 5.0,
        adxThreshold: 20,
        maTrendThreshold: 0.01
      }
    },
    // 宽松ADX
    {
      name: '宽松ADX (1.2x/6.0x, ADX<25)',
      config: {
        atrStopLossMultiplier: 1.2,
        atrTakeProfitMultiplier: 6.0,
        adxThreshold: 25,
        maTrendThreshold: 0.01
      }
    }
  ];
  
  const results = [];
  
  for (let i = 0; i < configs.length; i++) {
    const { name, config } = configs[i];
    console.log(`[${i+1}/${configs.length}] 测试 ${name}...`);
    
    try {
      const result = await testConfig(candles, config, name);
      results.push(result);
      console.log(`  ✓ 收益率: ${result.returnPercent.toFixed(2)}%, 盈亏比: ${result.profitFactor.toFixed(2)}, 胜率: ${result.winRate.toFixed(2)}%`);
    } catch (error) {
      console.log(`  ✗ 测试失败: ${error.message}`);
    }
  }
  
  // 排序找出最优
  results.sort((a, b) => b.returnPercent - a.returnPercent);
  
  console.log(`\n${'='.repeat(80)}`);
  console.log(`${timeframe} 周期训练结果 (按收益率排序)`);
  console.log('='.repeat(80));
  console.log('排名 | 配置名称                | 收益率   | 盈亏比 | 胜率   | 交易数');
  console.log('-'.repeat(80));
  
  for (let i = 0; i < results.length; i++) {
    const r = results[i];
    const rank = i === 0 ? '🏆' : `${i+1} `;
    console.log(
      `${rank}   | ${r.name.padEnd(23)} | ` +
      `${r.returnPercent.toFixed(2).padStart(7)}% | ` +
      `${r.profitFactor.toFixed(2).padStart(6)} | ` +
      `${r.winRate.toFixed(2).padStart(6)}% | ` +
      `${r.trades.toString().padStart(6)}`
    );
  }
  
  console.log('='.repeat(80));
  
  if (results.length > 0) {
    const best = results[0];
    console.log(`\n🏆 ${timeframe} 最优配置: ${best.name}`);
    console.log(`   收益率: ${best.returnPercent.toFixed(2)}%`);
    console.log(`   盈亏比: ${best.profitFactor.toFixed(2)}`);
    console.log(`   胜率: ${best.winRate.toFixed(2)}%`);
    console.log(`   最大回撤: ${best.maxDD.toFixed(2)}%`);
    console.log('\n   参数:');
    console.log(`   - 止损: ${best.config.atrStopLossMultiplier}x ATR`);
    console.log(`   - 止盈: ${best.config.atrTakeProfitMultiplier}x ATR`);
    console.log(`   - ADX阈值: ${best.config.adxThreshold}`);
    console.log(`   - MA阈值: ${(best.config.maTrendThreshold * 100).toFixed(1)}%`);
  }
  
  return results;
}

async function main() {
  console.log('='.repeat(80));
  console.log('双周期同时训练系统');
  console.log('='.repeat(80));
  console.log('\n策略: 布林带震荡策略 V2');
  console.log('目标: 为H1和M15周期分别找到最优参数\n');
  
  const dataDir = join(__dirname, 'data');
  
  // 训练H1周期
  const h1Results = await trainTimeframe('H1', join(dataDir, 'XAUUSDm_H1.csv'));
  
  // 训练M15周期
  const m15Results = await trainTimeframe('M15', join(dataDir, 'XAUUSDm_M15.csv'));
  
  // 最终对比
  console.log(`\n${'='.repeat(80)}`);
  console.log('双周期最优配置对比');
  console.log('='.repeat(80));
  
  if (h1Results.length > 0 && m15Results.length > 0) {
    const h1Best = h1Results[0];
    const m15Best = m15Results[0];
    
    console.log('\n周期 | 最优配置              | 收益率   | 盈亏比 | 胜率   | 交易数');
    console.log('-'.repeat(80));
    console.log(
      `H1   | ${h1Best.name.padEnd(21)} | ` +
      `${h1Best.returnPercent.toFixed(2).padStart(7)}% | ` +
      `${h1Best.profitFactor.toFixed(2).padStart(6)} | ` +
      `${h1Best.winRate.toFixed(2).padStart(6)}% | ` +
      `${h1Best.trades.toString().padStart(6)}`
    );
    console.log(
      `M15  | ${m15Best.name.padEnd(21)} | ` +
      `${m15Best.returnPercent.toFixed(2).padStart(7)}% | ` +
      `${m15Best.profitFactor.toFixed(2).padStart(6)} | ` +
      `${m15Best.winRate.toFixed(2).padStart(6)}% | ` +
      `${m15Best.trades.toString().padStart(6)}`
    );
    console.log('='.repeat(80));
    
    console.log('\n💡 推荐:');
    if (h1Best.returnPercent > m15Best.returnPercent) {
      console.log(`   使用 H1 周期 (收益率 ${h1Best.returnPercent.toFixed(2)}% > M15 ${m15Best.returnPercent.toFixed(2)}%)`);
      console.log(`   配置: ${h1Best.name}`);
    } else {
      console.log(`   使用 M15 周期 (收益率 ${m15Best.returnPercent.toFixed(2)}% > H1 ${h1Best.returnPercent.toFixed(2)}%)`);
      console.log(`   配置: ${m15Best.name}`);
    }
  }
  
  console.log('\n训练完成！\n');
}

main().catch(error => {
  console.error('训练失败:', error);
  console.error(error.stack);
  process.exit(1);
});
