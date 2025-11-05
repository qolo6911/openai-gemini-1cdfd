#!/usr/bin/env node

/**
 * XAUUSD布林带震荡策略回测运行脚本
 * Run Backtest for XAUUSD Bollinger Bands Range Strategy
 */

import { BollingerRangeStrategy } from './bollingerStrategy.mjs';
import { Backtester, generateReport } from './backtester.mjs';
import {
  generateMockData,
  fetchFromYahoo,
  loadFromCSV,
  saveToCSV,
  cachedFetch
} from './dataFetcher.mjs';
import { writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * 主函数
 */
async function main() {
  console.log('='.repeat(80));
  console.log('XAUUSD布林带震荡策略回测系统');
  console.log('XAUUSD Bollinger Bands Range Trading Strategy Backtest');
  console.log('='.repeat(80));
  console.log('');

  // 确保数据目录存在
  const dataDir = join(__dirname, 'data');
  if (!existsSync(dataDir)) {
    await mkdir(dataDir, { recursive: true });
  }

  // 获取历史数据
  let candles;
  const useRealData = process.env.USE_REAL_DATA === 'true';
  const dataSource = process.env.DATA_SOURCE || 'mock'; // mock, yahoo, csv

  try {
    if (dataSource === 'yahoo' && useRealData) {
      console.log('数据源: Yahoo Finance (黄金期货 GC=F)');
      const cacheFile = join(dataDir, 'xauusd_yahoo.csv');

      // 获取最近2年的日线数据
      const period2 = Math.floor(Date.now() / 1000);
      const period1 = period2 - (365 * 2 * 24 * 60 * 60); // 2年前

      candles = await cachedFetch(
        cacheFile,
        () => fetchFromYahoo(period1, period2, '1d'),
        24 * 60 * 60 * 1000 // 缓存24小时
      );

      console.log(`成功获取 ${candles.length} 条真实历史数据\n`);
    } else if (dataSource === 'csv') {
      console.log('数据源: 本地CSV文件');
      const csvFile = process.env.CSV_FILE || join(dataDir, 'xauusd.csv');
      candles = await loadFromCSV(csvFile);
      console.log(`成功加载 ${candles.length} 条数据\n`);
    } else {
      console.log('数据源: 模拟数据（用于演示）');
      console.log('提示: 设置环境变量 USE_REAL_DATA=true DATA_SOURCE=yahoo 使用真实数据\n');

      // 生成模拟数据：1年，起始价格2000
      candles = generateMockData(365, 2000);
      console.log(`生成 ${candles.length} 条模拟数据\n`);

      // 保存模拟数据以供参考
      const mockFile = join(dataDir, 'xauusd_mock.csv');
      await saveToCSV(candles, mockFile);
      console.log(`模拟数据已保存到: ${mockFile}\n`);
    }
  } catch (error) {
    console.error(`数据获取失败: ${error.message}`);
    console.log('使用模拟数据继续...\n');
    candles = generateMockData(365, 2000);
  }

  // 创建策略实例
  const strategy = new BollingerRangeStrategy({
    bollingerPeriod: 14,        // 布林带周期14
    bollingerStdDev: 2,         // 标准差2
    angleThreshold: 30,         // 震荡判断：角度小于30度
    slopeLookback: 3,           // 斜率计算回看3周期
    stopLossPercent: 2,         // 止损2%
    takeProfitPercent: 3        // 止盈3%
  });

  // 创建回测引擎
  const backtester = new Backtester(
    strategy,
    10000,  // 初始资金 $10,000
    1.0     // 100%仓位
  );

  // 运行回测
  console.log('开始回测...\n');
  const startTime = Date.now();
  const result = backtester.run(candles);
  const duration = Date.now() - startTime;

  // 生成并打印报告
  const report = generateReport(result);
  console.log('\n' + report);

  console.log(`\n回测耗时: ${duration}ms`);

  // 保存详细结果到文件
  const resultsDir = join(__dirname, 'results');
  if (!existsSync(resultsDir)) {
    await mkdir(resultsDir, { recursive: true });
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
  const resultFile = join(resultsDir, `backtest_${timestamp}.json`);
  const reportFile = join(resultsDir, `report_${timestamp}.txt`);

  await writeFile(resultFile, JSON.stringify(result, null, 2));
  await writeFile(reportFile, report);

  console.log(`\n详细结果已保存到:`);
  console.log(`  JSON: ${resultFile}`);
  console.log(`  报告: ${reportFile}`);

  // 生成权益曲线数据（可用于绘图）
  const equityFile = join(resultsDir, `equity_${timestamp}.csv`);
  const equityLines = ['Date,Balance'];
  for (const point of result.equity) {
    const dateStr = point.time.toISOString().split('T')[0];
    equityLines.push(`${dateStr},${point.balance.toFixed(2)}`);
  }
  await writeFile(equityFile, equityLines.join('\n'));
  console.log(`  权益曲线: ${equityFile}`);

  console.log('\n回测完成！');
}

// 运行主函数
main().catch(error => {
  console.error('回测失败:', error);
  process.exit(1);
});
