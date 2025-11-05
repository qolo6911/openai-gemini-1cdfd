#!/usr/bin/env node

/**
 * 多周期回测脚本 - M15, H1, H4
 * Multi-Timeframe Backtest for XAUUSD Bollinger Bands Strategy
 */

import { BollingerRangeStrategy } from './bollingerStrategy.mjs';
import { Backtester, generateReport } from './backtester.mjs';
import { loadFromCSV } from './dataFetcher.mjs';
import { writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * 时间周期配置
 */
const TIMEFRAMES = [
  {
    name: 'M15',
    file: 'XAUUSDm_M15.csv',
    description: '15分钟',
    config: {
      bollingerPeriod: 14,
      bollingerStdDev: 2,
      angleThreshold: 30,
      slopeLookback: 3,
      stopLossPercent: 1.5,    // 短周期降低止损
      takeProfitPercent: 2.5
    }
  },
  {
    name: 'H1',
    file: 'XAUUSDm_H1.csv',
    description: '1小时',
    config: {
      bollingerPeriod: 14,
      bollingerStdDev: 2,
      angleThreshold: 30,
      slopeLookback: 3,
      stopLossPercent: 2,
      takeProfitPercent: 3
    }
  },
  {
    name: 'H4',
    file: 'XAUUSDm_H4.csv',
    description: '4小时',
    config: {
      bollingerPeriod: 14,
      bollingerStdDev: 2,
      angleThreshold: 30,
      slopeLookback: 3,
      stopLossPercent: 2.5,    // 长周期提高止损
      takeProfitPercent: 4
    }
  }
];

/**
 * 运行单个周期的回测
 */
async function runSingleTimeframe(timeframe, dataDir, resultsDir) {
  console.log('='.repeat(80));
  console.log(`回测周期: ${timeframe.name} (${timeframe.description})`);
  console.log('='.repeat(80));

  // 加载数据
  const dataFile = join(dataDir, timeframe.file);
  if (!existsSync(dataFile)) {
    throw new Error(`数据文件不存在: ${dataFile}`);
  }

  console.log(`加载数据: ${timeframe.file}`);
  const candles = await loadFromCSV(dataFile);
  console.log('');

  // 创建策略
  const strategy = new BollingerRangeStrategy(timeframe.config);

  // 创建回测引擎
  const backtester = new Backtester(strategy, 10000, 1.0);

  // 运行回测
  console.log('开始回测...\n');
  const startTime = Date.now();
  const result = backtester.run(candles);
  const duration = Date.now() - startTime;

  // 生成报告
  const report = generateReport(result);
  console.log('\n' + report);
  console.log(`\n回测耗时: ${duration}ms`);

  // 保存结果
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
  const resultFile = join(resultsDir, `backtest_${timeframe.name}_${timestamp}.json`);
  const reportFile = join(resultsDir, `report_${timeframe.name}_${timestamp}.txt`);
  const equityFile = join(resultsDir, `equity_${timeframe.name}_${timestamp}.csv`);

  await writeFile(resultFile, JSON.stringify(result, null, 2));
  await writeFile(reportFile, report);

  // 保存权益曲线
  const equityLines = ['Date,Balance'];
  for (const point of result.equity) {
    const dateStr = point.time.toISOString().replace('T', ' ').split('.')[0];
    equityLines.push(`${dateStr},${point.balance.toFixed(2)}`);
  }
  await writeFile(equityFile, equityLines.join('\n'));

  console.log(`\n结果已保存:`);
  console.log(`  JSON: ${resultFile}`);
  console.log(`  报告: ${reportFile}`);
  console.log(`  权益: ${equityFile}`);
  console.log('');

  return {
    timeframe: timeframe.name,
    description: timeframe.description,
    result,
    duration
  };
}

/**
 * 生成对比报告
 */
function generateComparisonReport(results) {
  const lines = [];

  lines.push('='.repeat(100));
  lines.push('多周期回测对比报告');
  lines.push('Multi-Timeframe Backtest Comparison Report');
  lines.push('='.repeat(100));
  lines.push('');

  // 创建对比表格
  lines.push('周期对比 (Timeframe Comparison):');
  lines.push('-'.repeat(100));

  // 表头
  const header = [
    '周期'.padEnd(8),
    '收益率'.padStart(10),
    '总交易'.padStart(8),
    '胜率'.padStart(10),
    '盈亏比'.padStart(10),
    '夏普'.padStart(10),
    '最大回撤'.padStart(12)
  ].join(' | ');
  lines.push(header);
  lines.push('-'.repeat(100));

  // 数据行
  for (const item of results) {
    const r = item.result;
    const row = [
      item.timeframe.padEnd(8),
      `${r.returnPercent > 0 ? '+' : ''}${r.returnPercent.toFixed(2)}%`.padStart(10),
      r.stats.totalTrades.toString().padStart(8),
      r.stats.winRate.padStart(10),
      r.stats.profitFactor.padStart(10),
      r.stats.sharpeRatio.padStart(10),
      r.stats.maxDrawdownPercent.padStart(12)
    ].join(' | ');
    lines.push(row);
  }

  lines.push('-'.repeat(100));
  lines.push('');

  // 详细对比
  lines.push('详细指标对比:');
  lines.push('-'.repeat(100));
  lines.push('');

  for (const item of results) {
    const r = item.result;
    lines.push(`【${item.timeframe} - ${item.description}】`);
    lines.push(`  初始资金:     $${r.initialBalance.toFixed(2)}`);
    lines.push(`  最终资金:     $${r.finalBalance.toFixed(2)}`);
    lines.push(`  净利润:       ${r.netProfit > 0 ? '+' : ''}$${r.netProfit.toFixed(2)}`);
    lines.push(`  收益率:       ${r.returnPercent > 0 ? '+' : ''}${r.returnPercent.toFixed(2)}%`);
    lines.push(`  总交易:       ${r.stats.totalTrades}`);
    lines.push(`  盈利交易:     ${r.stats.winningTrades}`);
    lines.push(`  亏损交易:     ${r.stats.losingTrades}`);
    lines.push(`  胜率:         ${r.stats.winRate}`);
    lines.push(`  平均盈利:     $${r.stats.avgWin}`);
    lines.push(`  平均亏损:     $${r.stats.avgLoss}`);
    lines.push(`  盈亏比:       ${r.stats.profitFactor}`);
    lines.push(`  夏普比率:     ${r.stats.sharpeRatio}`);
    lines.push(`  最大回撤:     ${r.stats.maxDrawdownPercent}`);
    lines.push(`  回测耗时:     ${item.duration}ms`);
    lines.push('');
  }

  lines.push('='.repeat(100));
  lines.push('');

  // 推荐周期
  lines.push('📊 周期分析:');
  lines.push('-'.repeat(100));

  // 找出最佳表现
  const bestReturn = results.reduce((best, curr) =>
    curr.result.returnPercent > best.result.returnPercent ? curr : best
  );
  const bestWinRate = results.reduce((best, curr) =>
    parseFloat(curr.result.stats.winRate) > parseFloat(best.result.stats.winRate) ? curr : best
  );
  const bestSharpe = results.reduce((best, curr) =>
    parseFloat(curr.result.stats.sharpeRatio) > parseFloat(best.result.stats.sharpeRatio) ? curr : best
  );

  lines.push(`最高收益率:   ${bestReturn.timeframe} (${bestReturn.result.returnPercent.toFixed(2)}%)`);
  lines.push(`最高胜率:     ${bestWinRate.timeframe} (${bestWinRate.result.stats.winRate})`);
  lines.push(`最佳夏普:     ${bestSharpe.timeframe} (${bestSharpe.result.stats.sharpeRatio})`);
  lines.push('');

  lines.push('💡 建议:');
  lines.push('-'.repeat(100));
  lines.push('1. 短周期（M15）: 交易频率高，适合日内交易，但需要更严格的风险控制');
  lines.push('2. 中周期（H1）: 平衡交易频率和稳定性，适合波段交易');
  lines.push('3. 长周期（H4）: 交易频率低，但信号更可靠，适合稳健型交易者');
  lines.push('');
  lines.push('根据回测结果选择最适合您风险偏好的时间周期。');
  lines.push('');

  lines.push('='.repeat(100));

  return lines.join('\n');
}

/**
 * 主函数
 */
async function main() {
  console.log('='.repeat(100));
  console.log('XAUUSD布林带震荡策略 - 多周期回测');
  console.log('XAUUSD Bollinger Bands Strategy - Multi-Timeframe Backtest');
  console.log('='.repeat(100));
  console.log('');

  // 确保目录存在
  const dataDir = join(__dirname, 'data');
  const resultsDir = join(__dirname, 'results');

  if (!existsSync(resultsDir)) {
    await mkdir(resultsDir, { recursive: true });
  }

  // 运行所有周期的回测
  const results = [];

  for (const timeframe of TIMEFRAMES) {
    try {
      const result = await runSingleTimeframe(timeframe, dataDir, resultsDir);
      results.push(result);
    } catch (error) {
      console.error(`回测失败 [${timeframe.name}]: ${error.message}`);
      console.log('');
    }
  }

  // 生成对比报告
  if (results.length > 0) {
    console.log('\n\n');
    const comparisonReport = generateComparisonReport(results);
    console.log(comparisonReport);

    // 保存对比报告
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
    const comparisonFile = join(resultsDir, `comparison_${timestamp}.txt`);
    await writeFile(comparisonFile, comparisonReport);
    console.log(`\n对比报告已保存: ${comparisonFile}`);
  }

  console.log('\n\n所有回测完成！');
}

// 运行主函数
main().catch(error => {
  console.error('回测失败:', error);
  process.exit(1);
});
