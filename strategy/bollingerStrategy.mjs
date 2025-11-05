/**
 * XAUUSD布林带震荡策略
 * Bollinger Bands Range Trading Strategy for XAUUSD (Gold/USD)
 */

import {
  calculateBollingerBands,
  isRangebound
} from './indicators.mjs';

/**
 * 交易信号类型
 */
export const SignalType = {
  LONG: 'LONG',      // 做多
  SHORT: 'SHORT',    // 做空
  CLOSE: 'CLOSE',    // 平仓
  HOLD: 'HOLD'       // 持有/不操作
};

/**
 * 策略配置
 */
export const DEFAULT_CONFIG = {
  // 布林带参数
  bollingerPeriod: 14,        // 布林带周期
  bollingerStdDev: 2,         // 标准差乘数

  // 震荡判断参数
  angleThreshold: 30,         // 角度阈值（度）
  slopeLookback: 3,           // 斜率计算回看周期

  // 交易规则
  entryAtBands: true,         // 在布林带边缘入场
  exitAtMiddle: true,         // 在中轨出场

  // 风险管理
  stopLossPercent: 2,         // 止损百分比
  takeProfitPercent: 3,       // 止盈百分比
};

/**
 * XAUUSD布林带震荡策略类
 */
export class BollingerRangeStrategy {
  constructor(config = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.position = null; // 当前持仓 {type, entryPrice, entryIndex}
  }

  /**
   * 生成交易信号
   * @param {Object[]} candles - K线数据数组 [{open, high, low, close, time, volume}]
   * @param {number} index - 当前K线索引
   * @returns {Object} 信号 {signal, price, reason, bb}
   */
  generateSignal(candles, index) {
    if (index < this.config.bollingerPeriod) {
      return {
        signal: SignalType.HOLD,
        price: candles[index].close,
        reason: '数据不足，无法计算布林带',
        bb: null
      };
    }

    // 提取收盘价
    const closes = candles.slice(0, index + 1).map(c => c.close);

    // 计算布林带
    const bb = calculateBollingerBands(
      closes,
      this.config.bollingerPeriod,
      this.config.bollingerStdDev
    );

    const currentCandle = candles[index];
    const currentPrice = currentCandle.close;
    const upperBand = bb.upper[index];
    const middleBand = bb.middle[index];
    const lowerBand = bb.lower[index];

    // 判断是否为震荡行情
    const isRange = isRangebound(
      bb.middle,
      index,
      this.config.angleThreshold,
      this.config.slopeLookback
    );

    // 如果不是震荡行情，不交易
    if (!isRange) {
      return {
        signal: SignalType.HOLD,
        price: currentPrice,
        reason: '当前非震荡行情（中轨趋势角度 >= 30度）',
        bb: { upper: upperBand, middle: middleBand, lower: lowerBand },
        isRange: false
      };
    }

    // 检查止损止盈
    if (this.position) {
      const profitPercent = ((currentPrice - this.position.entryPrice) / this.position.entryPrice) * 100;

      if (this.position.type === SignalType.LONG) {
        // 多头止损
        if (profitPercent <= -this.config.stopLossPercent) {
          this.position = null;
          return {
            signal: SignalType.CLOSE,
            price: currentPrice,
            reason: `多头止损触发（亏损${profitPercent.toFixed(2)}%）`,
            bb: { upper: upperBand, middle: middleBand, lower: lowerBand },
            isRange: true
          };
        }
        // 多头止盈
        if (profitPercent >= this.config.takeProfitPercent) {
          this.position = null;
          return {
            signal: SignalType.CLOSE,
            price: currentPrice,
            reason: `多头止盈触发（盈利${profitPercent.toFixed(2)}%）`,
            bb: { upper: upperBand, middle: middleBand, lower: lowerBand },
            isRange: true
          };
        }
        // 价格回到中轨附近，平仓
        if (Math.abs(currentPrice - middleBand) / middleBand < 0.001) { // 0.1%范围内
          this.position = null;
          return {
            signal: SignalType.CLOSE,
            price: currentPrice,
            reason: `多头到达中轨，平仓（盈利${profitPercent.toFixed(2)}%）`,
            bb: { upper: upperBand, middle: middleBand, lower: lowerBand },
            isRange: true
          };
        }
      } else if (this.position.type === SignalType.SHORT) {
        // 空头止损
        if (profitPercent >= this.config.stopLossPercent) {
          this.position = null;
          return {
            signal: SignalType.CLOSE,
            price: currentPrice,
            reason: `空头止损触发（亏损${Math.abs(profitPercent).toFixed(2)}%）`,
            bb: { upper: upperBand, middle: middleBand, lower: lowerBand },
            isRange: true
          };
        }
        // 空头止盈
        if (profitPercent <= -this.config.takeProfitPercent) {
          this.position = null;
          return {
            signal: SignalType.CLOSE,
            price: currentPrice,
            reason: `空头止盈触发（盈利${Math.abs(profitPercent).toFixed(2)}%）`,
            bb: { upper: upperBand, middle: middleBand, lower: lowerBand },
            isRange: true
          };
        }
        // 价格回到中轨附近，平仓
        if (Math.abs(currentPrice - middleBand) / middleBand < 0.001) { // 0.1%范围内
          this.position = null;
          return {
            signal: SignalType.CLOSE,
            price: currentPrice,
            reason: `空头到达中轨，平仓（盈利${Math.abs(profitPercent).toFixed(2)}%）`,
            bb: { upper: upperBand, middle: middleBand, lower: lowerBand },
            isRange: true
          };
        }
      }
    }

    // 生成入场信号
    if (!this.position) {
      // 价格触及下轨 -> 做多信号
      if (currentPrice <= lowerBand * 1.001) { // 允许1%误差
        this.position = {
          type: SignalType.LONG,
          entryPrice: currentPrice,
          entryIndex: index
        };
        return {
          signal: SignalType.LONG,
          price: currentPrice,
          reason: `震荡行情，价格触及下轨（${lowerBand.toFixed(2)}），做多`,
          bb: { upper: upperBand, middle: middleBand, lower: lowerBand },
          isRange: true
        };
      }

      // 价格触及上轨 -> 做空信号
      if (currentPrice >= upperBand * 0.999) { // 允许1%误差
        this.position = {
          type: SignalType.SHORT,
          entryPrice: currentPrice,
          entryIndex: index
        };
        return {
          signal: SignalType.SHORT,
          price: currentPrice,
          reason: `震荡行情，价格触及上轨（${upperBand.toFixed(2)}），做空`,
          bb: { upper: upperBand, middle: middleBand, lower: lowerBand },
          isRange: true
        };
      }

      // 价格在中轨附近 -> 不开仓
      return {
        signal: SignalType.HOLD,
        price: currentPrice,
        reason: '震荡行情，价格在中轨区域，等待触及上下轨',
        bb: { upper: upperBand, middle: middleBand, lower: lowerBand },
        isRange: true
      };
    }

    // 持仓中，继续持有
    return {
      signal: SignalType.HOLD,
      price: currentPrice,
      reason: `持有${this.position.type}仓位`,
      bb: { upper: upperBand, middle: middleBand, lower: lowerBand },
      isRange: true,
      position: this.position
    };
  }

  /**
   * 重置策略状态
   */
  reset() {
    this.position = null;
  }
}
