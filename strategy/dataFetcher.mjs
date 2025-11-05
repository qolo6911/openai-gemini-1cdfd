/**
 * 历史数据获取模块
 * Historical Data Fetcher
 */

import { readFile, writeFile } from 'fs/promises';
import { existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * 使用Alpha Vantage API获取XAUUSD历史数据（免费）
 * 注意：Alpha Vantage有API调用限制（免费版每分钟5次，每天500次）
 * @param {string} apiKey - Alpha Vantage API密钥
 * @param {string} interval - 时间间隔 (1min, 5min, 15min, 30min, 60min, daily)
 * @returns {Promise<Object[]>} K线数据数组
 */
export async function fetchFromAlphaVantage(apiKey, interval = 'daily') {
  const symbol = 'XAU'; // 黄金
  const market = 'USD';  // 美元

  let functionType;
  if (interval === 'daily') {
    functionType = 'FX_DAILY';
  } else {
    functionType = 'FX_INTRADAY';
  }

  const url = functionType === 'FX_DAILY'
    ? `https://www.alphavantage.co/query?function=${functionType}&from_symbol=${symbol}&to_symbol=${market}&apikey=${apiKey}&outputsize=full`
    : `https://www.alphavantage.co/query?function=${functionType}&from_symbol=${symbol}&to_symbol=${market}&interval=${interval}&apikey=${apiKey}&outputsize=full`;

  try {
    const response = await fetch(url);
    const data = await response.json();

    if (data['Error Message']) {
      throw new Error(`API错误: ${data['Error Message']}`);
    }

    if (data['Note']) {
      throw new Error(`API调用限制: ${data['Note']}`);
    }

    const timeSeriesKey = Object.keys(data).find(key => key.includes('Time Series'));
    if (!timeSeriesKey) {
      throw new Error('无法找到时间序列数据');
    }

    const timeSeries = data[timeSeriesKey];
    const candles = [];

    for (const [time, values] of Object.entries(timeSeries)) {
      candles.push({
        time: new Date(time),
        timestamp: new Date(time).getTime(),
        open: parseFloat(values['1. open']),
        high: parseFloat(values['2. high']),
        low: parseFloat(values['3. low']),
        close: parseFloat(values['4. close']),
        volume: 0 // FX数据通常没有交易量
      });
    }

    // 按时间升序排序
    candles.sort((a, b) => a.timestamp - b.timestamp);

    return candles;
  } catch (error) {
    throw new Error(`获取数据失败: ${error.message}`);
  }
}

/**
 * 使用Yahoo Finance获取XAUUSD历史数据（通过非官方API）
 * @param {string} period1 - 开始时间戳（秒）
 * @param {string} period2 - 结束时间戳（秒）
 * @param {string} interval - 时间间隔 (1m, 5m, 15m, 1h, 1d)
 * @returns {Promise<Object[]>} K线数据数组
 */
export async function fetchFromYahoo(period1, period2, interval = '1d') {
  const symbol = 'GC=F'; // 黄金期货

  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?period1=${period1}&period2=${period2}&interval=${interval}`;

  try {
    const response = await fetch(url);
    const data = await response.json();

    if (!data.chart || !data.chart.result || data.chart.result.length === 0) {
      throw new Error('无法获取数据');
    }

    const result = data.chart.result[0];
    const timestamps = result.timestamp;
    const quotes = result.indicators.quote[0];

    const candles = timestamps.map((timestamp, i) => ({
      time: new Date(timestamp * 1000),
      timestamp: timestamp * 1000,
      open: quotes.open[i],
      high: quotes.high[i],
      low: quotes.low[i],
      close: quotes.close[i],
      volume: quotes.volume[i] || 0
    }));

    // 过滤掉无效数据
    return candles.filter(c => c.open !== null && c.close !== null);
  } catch (error) {
    throw new Error(`获取Yahoo数据失败: ${error.message}`);
  }
}

/**
 * 生成模拟的XAUUSD历史数据（用于测试）
 * @param {number} days - 生成天数
 * @param {number} startPrice - 起始价格
 * @returns {Object[]} K线数据数组
 */
export function generateMockData(days = 365, startPrice = 2000) {
  const candles = [];
  const now = Date.now();
  const dayMs = 24 * 60 * 60 * 1000;

  let price = startPrice;

  for (let i = days - 1; i >= 0; i--) {
    const timestamp = now - (i * dayMs);

    // 模拟价格波动
    const volatility = 20; // 日波动幅度
    const trend = Math.sin(i / 30) * 10; // 模拟周期性趋势

    const open = price + (Math.random() - 0.5) * volatility;
    const close = open + trend + (Math.random() - 0.5) * volatility;
    const high = Math.max(open, close) + Math.random() * volatility / 2;
    const low = Math.min(open, close) - Math.random() * volatility / 2;

    candles.push({
      time: new Date(timestamp),
      timestamp,
      open,
      high,
      low,
      close,
      volume: Math.floor(Math.random() * 100000)
    });

    price = close;
  }

  return candles;
}

/**
 * 从本地CSV文件加载数据
 * CSV格式: Date,Open,High,Low,Close,Volume
 * @param {string} filePath - CSV文件路径
 * @returns {Promise<Object[]>} K线数据数组
 */
export async function loadFromCSV(filePath) {
  try {
    const content = await readFile(filePath, 'utf-8');
    const lines = content.trim().split('\n');
    const candles = [];

    for (let i = 1; i < lines.length; i++) { // 跳过标题行
      const parts = lines[i].split(',');
      if (parts.length < 5) continue;

      candles.push({
        time: new Date(parts[0]),
        timestamp: new Date(parts[0]).getTime(),
        open: parseFloat(parts[1]),
        high: parseFloat(parts[2]),
        low: parseFloat(parts[3]),
        close: parseFloat(parts[4]),
        volume: parts[5] ? parseFloat(parts[5]) : 0
      });
    }

    // 按时间升序排序
    candles.sort((a, b) => a.timestamp - b.timestamp);

    return candles;
  } catch (error) {
    throw new Error(`读取CSV文件失败: ${error.message}`);
  }
}

/**
 * 保存数据到CSV文件
 * @param {Object[]} candles - K线数据数组
 * @param {string} filePath - 保存路径
 */
export async function saveToCSV(candles, filePath) {
  const lines = ['Date,Open,High,Low,Close,Volume'];

  for (const candle of candles) {
    const dateStr = candle.time.toISOString().split('T')[0];
    lines.push(`${dateStr},${candle.open},${candle.high},${candle.low},${candle.close},${candle.volume}`);
  }

  await writeFile(filePath, lines.join('\n'), 'utf-8');
}

/**
 * 缓存数据获取器
 * @param {string} cacheFile - 缓存文件路径
 * @param {Function} fetcher - 数据获取函数
 * @param {number} maxAge - 缓存有效期（毫秒）
 * @returns {Promise<Object[]>} K线数据数组
 */
export async function cachedFetch(cacheFile, fetcher, maxAge = 24 * 60 * 60 * 1000) {
  try {
    if (existsSync(cacheFile)) {
      const stats = await import('fs/promises').then(m => m.stat(cacheFile));
      const age = Date.now() - stats.mtimeMs;

      if (age < maxAge) {
        console.log('使用缓存数据...');
        return await loadFromCSV(cacheFile);
      }
    }
  } catch (error) {
    console.log('缓存读取失败，重新获取数据...');
  }

  console.log('获取新数据...');
  const data = await fetcher();
  await saveToCSV(data, cacheFile);
  return data;
}
