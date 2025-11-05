#!/usr/bin/env node
/**
 * 双周期策略
 * H4周期: 判断大趋势和市场环境
 * H1周期: 执行具体交易
 */

import { BollingerRangeStrategyV2 } from './bollingerStrategyV2.mjs';
import { calculateADX, calculateSMA } from './indicators.mjs';

export class DualTimeframeStrategy {
  constructor(config = {}) {
    this.config = {
      // H4周期配置（趋势判断）
      h4TrendPeriod: 50,
      h4ADXThreshold: 25,
      
      // H1周期配置（交易执行）
      h1Strategy: new BollingerRangeStrategyV2({
        bollingerPeriod: 20,
        bollingerStdDev: 2.5,
        angleThreshold: 20,
        atrStopLossMultiplier: 1.2,
        atrTakeProfitMultiplier: 6.0,
        adxThreshold: 20,
        maTrendThreshold: 0.01
      }),
      
      // 双周期过滤
      requireH4Oscillation: true,  // H4必须震荡
      requireH4Align: false,        // H4和H1方向一致
      
      ...config
    };
  }

  /**
   * 从H1数据构建H4数据
   */
  buildH4FromH1(h1Candles) {
    const h4Candles = [];
    
    for (let i = 0; i < h1Candles.length; i += 4) {
      if (i + 3 >= h1Candles.length) break;
      
      const fourHourCandles = h1Candles.slice(i, i + 4);
      const h4Candle = {
        time: fourHourCandles[0].time,
        open: fourHourCandles[0].open,
        high: Math.max(...fourHourCandles.map(c => c.high)),
        low: Math.min(...fourHourCandles.map(c => c.low)),
        close: fourHourCandles[3].close,
        volume: fourHourCandles.reduce((sum, c) => sum + (c.volume || 0), 0)
      };
      
      h4Candles.push(h4Candle);
    }
    
    return h4Candles;
  }

  /**
   * 判断H4是否处于震荡
   */
  isH4Oscillating(h4Candles, h4Index) {
    if (h4Index < this.config.h4TrendPeriod || h4Index >= h4Candles.length) return false;

    // 计算H4的ADX
    const adx = calculateADX(h4Candles, 14);
    if (!adx || !adx[h4Index]) return false;

    // ADX低于阈值表示震荡
    return adx[h4Index] < this.config.h4ADXThreshold;
  }

  /**
   * 获取H4趋势方向
   */
  getH4Trend(h4Candles, h4Index) {
    if (h4Index < this.config.h4TrendPeriod || h4Index >= h4Candles.length) return 0;

    const sma = calculateSMA(h4Candles.map(c => c.close), this.config.h4TrendPeriod);
    const currentCandle = h4Candles[h4Index];

    if (!currentCandle || !currentCandle.close) return 0;

    const currentPrice = currentCandle.close;
    const smaValue = sma[h4Index];

    if (!smaValue) return 0;

    const diff = (currentPrice - smaValue) / smaValue;

    if (diff > 0.005) return 1;   // 上涨趋势
    if (diff < -0.005) return -1;  // 下跌趋势
    return 0;  // 震荡
  }

  /**
   * 生成交易信号
   */
  generateSignal(h1Candles, h1Index, h4Candles = null) {
    // 如果没有提供H4数据，从H1构建
    if (!h4Candles) {
      h4Candles = this.buildH4FromH1(h1Candles.slice(0, h1Index + 1));
    }

    const h4Index = Math.floor(h1Index / 4);

    // 确保H4索引有效
    if (h4Index >= h4Candles.length) {
      return { signal: 'HOLD', reason: 'H4数据不足' };
    }

    // H4过滤检查
    if (this.config.requireH4Oscillation) {
      if (!this.isH4Oscillating(h4Candles, h4Index)) {
        return { signal: 'HOLD', reason: 'H4不满足震荡条件' };
      }
    }

    // H1策略信号
    const h1Signal = this.config.h1Strategy.generateSignal(h1Candles, h1Index);

    // H4方向对齐检查
    if (this.config.requireH4Align && h1Signal.signal !== 'HOLD' && h1Signal.signal !== 'CLOSE') {
      const h4Trend = this.getH4Trend(h4Candles, h4Index);

      if (h1Signal.signal === 'LONG' && h4Trend === -1) {
        return { signal: 'HOLD', reason: 'H4下跌趋势，不做多' };
      }
      if (h1Signal.signal === 'SHORT' && h4Trend === 1) {
        return { signal: 'HOLD', reason: 'H4上涨趋势，不做空' };
      }
    }

    return h1Signal;
  }

  reset() {
    this.config.h1Strategy.reset();
  }
}
