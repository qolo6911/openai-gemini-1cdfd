#!/usr/bin/env node

/**
 * 参数优化引擎 (静默版)
 * Parameter Optimization Engine (Quiet Version)
 */

import { BollingerRangeStrategyV2 } from './bollingerStrategyV2.mjs';
import { Backtester } from './backtester.mjs';
import { loadFromCSV } from './dataFetcher.mjs';
import { writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * 参数搜索空间定义
 */
const PARAMETER_SPACE = {
  // 布林带参数
  bollingerPeriod: [14, 20, 30],
  bollingerStdDev: [2.0, 2.5, 3.0],

  // 震荡判断
  angleThreshold: [15, 20, 30],

  // ATR止损止盈倍数
  atrStopLossMultiplier: [1.5, 2.0, 2.5],
  atrTakeProfitMultiplier: [2.5, 3.0, 4.0],

  // ADX阈值
  adxThreshold: [20, 25, 30],

  // MA趋势阈值
  maTrendThreshold: [0.01, 0.02, 0.03]
};

/**
 * 评分函数：综合评估策略表现
 */
function calculateScore(result) {
  try {
    const returnPct = result.returnPercent;
    const sharpe = parseFloat(result.stats.sharpeRatio);
    const winRate = parseFloat(result.stats.winRate.replace('%', '')) / 100;
    const profitFactor = parseFloat(result.stats.profitFactor);
    const maxDD = parseFloat(result.stats.maxDrawdownPercent.replace('%', '')) / 100;

    // 加权评分
    const score =
      returnPct * 0.4 +                    // 收益率权重40%
      sharpe * 10 * 0.2 +                  // 夏普比率权重20%
      (winRate - 0.5) * 50 * 0.15 +        // 胜率权重15%
      (profitFactor - 1) * 20 * 0.15 +     // 盈亏比权重15%
      (-maxDD) * 50 * 0.1;                 // 最大回撤权重10%（负向）

    return score;
  } catch (error) {
    return -Infinity;
  }
}

/**
 * 数据分割
 */
function splitData(candles, trainRatio = 0.7) {
  const splitIndex = Math.floor(candles.length * trainRatio);
  return {
    train: candles.slice(0, splitIndex),
    test: candles.slice(splitIndex)
  };
}

/**
 * 运行单次回测（静默模式）
 */
function runSingleBacktest(candles, config) {
  const strategy = new BollingerRangeStrategyV2(config);
  // 创建静默backtester
  const backtester = new Backtester(strategy, 10000, 1.0);
  backtester.verbose = false; // 关闭详细输出
  return backtester.run(candles, false); // false = 静默模式
}

/**
 * 网格搜索优化
 */
async function gridSearchOptimization(trainData, paramSpace, options = {}) {
  const {
    maxCombinations = 1000
  } = options;

  // 生成所有参数组合
  const combinations = generateCombinations(paramSpace);

  console.log(`总共 ${combinations.length} 个参数组合需要测试`);

  if (combinations.length > maxCombinations) {
    console.log(`限制为前 ${maxCombinations} 个组合`);
    combinations.length = maxCombinations;
  }

  const results = [];
  let completed = 0;
  let lastProgressReport = Date.now();

  for (const params of combinations) {
    try {
      const result = runSingleBacktest(trainData, params);
      const score = calculateScore(result);

      results.push({
        params,
        result,
        score,
        returnPercent: result.returnPercent,
        sharpe: result.stats.sharpeRatio,
        winRate: result.stats.winRate,
        profitFactor: result.stats.profitFactor,
        maxDD: result.stats.maxDrawdownPercent
      });

      completed++;

      // 每30秒报告一次进度
      const now = Date.now();
      if (now - lastProgressReport > 30000) {
        console.log(`进度: ${completed}/${combinations.length} (${(completed/combinations.length*100).toFixed(1)}%) - 最近得分: ${score.toFixed(2)}`);
        lastProgressReport = now;
      }
    } catch (error) {
      console.error(`参数组合测试失败:`, JSON.stringify(params), error.message);
      completed++;
    }
  }

  console.log(`完成! 共测试 ${completed}/${combinations.length} 个组合`);

  // 按得分排序
  results.sort((a, b) => b.score - a.score);

  return results;
}

/**
 * 生成所有参数组合
 */
function generateCombinations(paramSpace) {
  const keys = Object.keys(paramSpace);
  const combinations = [];

  function recurse(index, current) {
    if (index === keys.length) {
      combinations.push({ ...current });
      return;
    }

    const key = keys[index];
    const values = paramSpace[key];

    for (const value of values) {
      current[key] = value;
      recurse(index + 1, current);
    }
  }

  recurse(0, {});
  return combinations;
}

/**
 * 生成优化报告
 */
function generateOptimizationReport(trainResults, testResults, topN = 10) {
  const lines = [];

  lines.push('='.repeat(100));
  lines.push('参数优化报告');
  lines.push('Parameter Optimization Report');
  lines.push('='.repeat(100));
  lines.push('');

  lines.push(`测试组合数: ${trainResults.length}`);
  lines.push(`训练数据: ${trainResults[0]?.result.stats.totalTrades || 'N/A'} 笔交易`);
  lines.push('');

  lines.push('Top ' + topN + ' 参数组合（训练集表现）:');
  lines.push('-'.repeat(100));
  lines.push('');

  for (let i = 0; i < Math.min(topN, trainResults.length); i++) {
    const item = trainResults[i];
    lines.push(`【第 ${i + 1} 名】 得分: ${item.score.toFixed(2)}`);
    lines.push('参数:');
    lines.push(`  布林带周期: ${item.params.bollingerPeriod}, 标准差: ${item.params.bollingerStdDev}`);
    lines.push(`  角度阈值: ${item.params.angleThreshold}°`);
    lines.push(`  ATR止损倍数: ${item.params.atrStopLossMultiplier}, 止盈倍数: ${item.params.atrTakeProfitMultiplier}`);
    lines.push(`  ADX阈值: ${item.params.adxThreshold}`);
    lines.push(`  MA趋势阈值: ${(item.params.maTrendThreshold * 100).toFixed(1)}%`);
    lines.push('训练集表现:');
    lines.push(`  收益率: ${item.returnPercent.toFixed(2)}%`);
    lines.push(`  夏普比率: ${item.sharpe}`);
    lines.push(`  胜率: ${item.winRate}`);
    lines.push(`  盈亏比: ${item.profitFactor}`);
    lines.push(`  最大回撤: ${item.maxDD}`);

    // 如果有测试集结果
    if (testResults && testResults[i]) {
      const testItem = testResults[i];
      lines.push('测试集表现:');
      lines.push(`  收益率: ${testItem.returnPercent.toFixed(2)}%`);
      lines.push(`  夏普比率: ${testItem.sharpe}`);
      lines.push(`  胜率: ${testItem.winRate}`);
      lines.push(`  盈亏比: ${testItem.profitFactor}`);
      lines.push(`  最大回撤: ${testItem.maxDD}`);
    }

    lines.push('');
  }

  lines.push('='.repeat(100));

  return lines.join('\n');
}

/**
 * 主函数
 */
async function main() {
  console.log('='.repeat(100));
  console.log('XAUUSD布林带策略参数优化 (静默模式)');
  console.log('Parameter Optimization for XAUUSD Bollinger Strategy (Quiet Mode)');
  console.log('='.repeat(100));
  console.log('');

  // 加载数据
  const dataDir = join(__dirname, 'data');
  const dataFile = process.env.DATA_FILE || join(dataDir, 'XAUUSDm_H1.csv');

  console.log(`加载数据: ${dataFile}`);
  const candles = await loadFromCSV(dataFile);
  console.log(`加载了 ${candles.length} 条数据`);
  console.log('');

  // 分割数据
  console.log('分割数据: 70% 训练集, 30% 测试集');
  const { train, test } = splitData(candles, 0.7);
  console.log(`训练集: ${train.length} 条`);
  console.log(`测试集: ${test.length} 条`);
  console.log('');

  // 训练集优化
  console.log('开始网格搜索优化...');
  const startTime = Date.now();
  const trainResults = await gridSearchOptimization(train, PARAMETER_SPACE, {
    maxCombinations: 10  // 快速测试：10个组合
  });
  const duration = Date.now() - startTime;
  console.log(`优化完成！耗时: ${(duration / 1000).toFixed(1)}秒`);
  console.log('');

  // 测试最优参数
  console.log('在测试集上验证 Top 10 参数...');
  const testResults = [];
  for (let i = 0; i < Math.min(10, trainResults.length); i++) {
    const params = trainResults[i].params;
    try {
      const result = runSingleBacktest(test, params);
      const score = calculateScore(result);

      testResults.push({
        params,
        result,
        score,
        returnPercent: result.returnPercent,
        sharpe: result.stats.sharpeRatio,
        winRate: result.stats.winRate,
        profitFactor: result.stats.profitFactor,
        maxDD: result.stats.maxDrawdownPercent
      });
      console.log(`  测试完成 ${i+1}/10`);
    } catch (error) {
      console.error(`测试集验证失败 (参数组${i+1}):`, error.message);
    }
  }
  console.log('');

  // 生成报告
  const report = generateOptimizationReport(trainResults, testResults, 10);
  console.log(report);

  // 保存结果
  const resultsDir = join(__dirname, 'results');
  if (!existsSync(resultsDir)) {
    await mkdir(resultsDir, { recursive: true });
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
  const reportFile = join(resultsDir, `optimization_${timestamp}.txt`);
  const resultsFile = join(resultsDir, `optimization_results_${timestamp}.json`);

  await writeFile(reportFile, report);
  await writeFile(resultsFile, JSON.stringify({
    trainResults: trainResults.slice(0, 20),
    testResults: testResults,
    parameterSpace: PARAMETER_SPACE,
    dataInfo: {
      total: candles.length,
      train: train.length,
      test: test.length
    }
  }, null, 2));

  console.log(`\n结果已保存:`);
  console.log(`  报告: ${reportFile}`);
  console.log(`  详细数据: ${resultsFile}`);
  console.log('');

  // 输出最优参数
  const best = trainResults[0];
  console.log('🏆 最优参数配置:');
  console.log('```javascript');
  console.log(JSON.stringify(best.params, null, 2));
  console.log('```');
  console.log('');
  console.log('训练集表现:', `收益率 ${best.returnPercent.toFixed(2)}%`, `夏普 ${best.sharpe}`);
  if (testResults.length > 0) {
    console.log('测试集表现:', `收益率 ${testResults[0].returnPercent.toFixed(2)}%`, `夏普 ${testResults[0].sharpe}`);
  }
}

// 运行
main().catch(error => {
  console.error('优化失败:', error);
  console.error(error.stack);
  process.exit(1);
});
