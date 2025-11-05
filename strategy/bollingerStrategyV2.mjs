/**
 * XAUUSD布林带震荡策略 V2 - 优化版
 * - 添加ATR动态止损止盈
 * - 添加MA趋势过滤
 * - 添加ADX震荡过滤
 * - 优化参数配置
 */

import {
  calculateBollingerBands,
  calculateATR,
  calculateSMA,
  calculateEMA,
  calculateADX,
  isRangebound
} from './indicators.mjs';

export const SignalType = {
  LONG: 'LONG',
  SHORT: 'SHORT',
  CLOSE: 'CLOSE',
  HOLD: 'HOLD'
};

export const DEFAULT_CONFIG_V2 = {
  // 布林带参数
  bollingerPeriod: 20,
  bollingerStdDev: 2.5,

  // 震荡判断
  angleThreshold: 20,
  slopeLookback: 3,

  // ATR参数
  atrPeriod: 14,
  atrStopLossMultiplier: 2.0,    // 止损 = ATR * 2
  atrTakeProfitMultiplier: 3.0,  // 止盈 = ATR * 3
  useATR: true,                  // 是否使用ATR动态止损

  // 固定止损止盈（当不使用ATR时）
  stopLossPercent: 1.5,
  takeProfitPercent: 3.0,

  // MA趋势过滤
  useMAFilter: true,
  maShortPeriod: 50,
  maLongPeriod: 200,
  maTrendThreshold: 0.02,  // 2% 差异认为是趋势

  // ADX过滤
  useADXFilter: true,
  adxPeriod: 14,
  adxThreshold: 25,          // ADX < 25 认为是震荡

  // 仓位管理
  positionSize: 1.0,         // 仓位比例（1.0 = 100%）
  maxDailyTrades: 50,        // 每日最大交易次数
};

export class BollingerRangeStrategyV2 {
  constructor(config = {}) {
    this.config = { ...DEFAULT_CONFIG_V2, ...config };
    this.position = null;
    this.dailyTrades = 0;
    this.lastTradeDay = null;
  }

  generateSignal(candles, index) {
    if (index < Math.max(this.config.bollingerPeriod, this.config.maLongPeriod || 0)) {
      return {
        signal: SignalType.HOLD,
        price: candles[index].close,
        reason: '数据不足',
        indicators: null
      };
    }

    // 检查日交易次数限制
    const currentDay = candles[index].time.toDateString();
    if (this.lastTradeDay !== currentDay) {
      this.dailyTrades = 0;
      this.lastTradeDay = currentDay;
    }

    if (this.dailyTrades >= this.config.maxDailyTrades) {
      return {
        signal: SignalType.HOLD,
        price: candles[index].close,
        reason: `达到日交易限制(${this.config.maxDailyTrades})`,
        indicators: null
      };
    }

    // 计算指标
    const closes = candles.slice(0, index + 1).map(c => c.close);
    const bb = calculateBollingerBands(closes, this.config.bollingerPeriod, this.config.bollingerStdDev);

    const currentCandle = candles[index];
    const currentPrice = currentCandle.close;
    const upperBand = bb.upper[index];
    const middleBand = bb.middle[index];
    const lowerBand = bb.lower[index];

    // 计算ATR
    let atr = null;
    if (this.config.useATR) {
      const atrArray = calculateATR(candles.slice(0, index + 1), this.config.atrPeriod);
      atr = atrArray[index];
    }

    // MA趋势过滤
    let maFilter = true;
    let maTrend = 'neutral';
    if (this.config.useMAFilter) {
      const maShort = calculateSMA(closes, this.config.maShortPeriod);
      const maLong = calculateSMA(closes, this.config.maLongPeriod);

      if (maShort[index] && maLong[index]) {
        const maDiff = (maShort[index] - maLong[index]) / maLong[index];

        if (maDiff > this.config.maTrendThreshold) {
          maFilter = false;
          maTrend = 'uptrend';
        } else if (maDiff < -this.config.maTrendThreshold) {
          maFilter = false;
          maTrend = 'downtrend';
        }
      }
    }

    // ADX过滤
    let adxFilter = true;
    let adxValue = null;
    if (this.config.useADXFilter) {
      const adxArray = calculateADX(candles.slice(0, index + 1), this.config.adxPeriod);
      adxValue = adxArray[index];

      if (adxValue !== null && adxValue > this.config.adxThreshold) {
        adxFilter = false;
      }
    }

    // 震荡判断
    const isRange = isRangebound(
      bb.middle,
      index,
      this.config.angleThreshold,
      this.config.slopeLookback
    );

    const indicators = {
      bb: { upper: upperBand, middle: middleBand, lower: lowerBand },
      atr,
      adx: adxValue,
      maTrend,
      isRange,
      maFilter,
      adxFilter
    };

    // 综合过滤判断
    if (!isRange || !maFilter || !adxFilter) {
      let reasons = [];
      if (!isRange) reasons.push('非震荡行情');
      if (!maFilter) reasons.push(`趋势市场(${maTrend})`);
      if (!adxFilter) reasons.push(`ADX过高(${adxValue?.toFixed(1)})`);

      return {
        signal: SignalType.HOLD,
        price: currentPrice,
        reason: reasons.join(', '),
        indicators
      };
    }

    // 计算动态止损止盈
    let stopLoss, takeProfit;
    if (this.config.useATR && atr) {
      stopLoss = atr * this.config.atrStopLossMultiplier;
      takeProfit = atr * this.config.atrTakeProfitMultiplier;
    } else {
      stopLoss = currentPrice * (this.config.stopLossPercent / 100);
      takeProfit = currentPrice * (this.config.takeProfitPercent / 100);
    }

    // 检查止损止盈
    if (this.position) {
      const priceDiff = this.position.type === SignalType.LONG
        ? currentPrice - this.position.entryPrice
        : this.position.entryPrice - currentPrice;

      // 止损
      if (priceDiff <= -this.position.stopLoss) {
        this.position = null;
        return {
          signal: SignalType.CLOSE,
          price: currentPrice,
          reason: `${this.position?.type}止损`,
          indicators
        };
      }

      // 止盈
      if (priceDiff >= this.position.takeProfit) {
        this.position = null;
        return {
          signal: SignalType.CLOSE,
          price: currentPrice,
          reason: `${this.position?.type}止盈`,
          indicators
        };
      }

      // 中轨平仓
      if (Math.abs(currentPrice - middleBand) / middleBand < 0.001) {
        this.position = null;
        return {
          signal: SignalType.CLOSE,
          price: currentPrice,
          reason: '到达中轨平仓',
          indicators
        };
      }

      return {
        signal: SignalType.HOLD,
        price: currentPrice,
        reason: `持有${this.position.type}`,
        indicators,
        position: this.position
      };
    }

    // 生成开仓信号
    if (currentPrice <= lowerBand * 1.001) {
      this.position = {
        type: SignalType.LONG,
        entryPrice: currentPrice,
        entryIndex: index,
        stopLoss,
        takeProfit
      };
      this.dailyTrades++;

      return {
        signal: SignalType.LONG,
        price: currentPrice,
        reason: `触及下轨(${lowerBand.toFixed(2)})做多, SL:${stopLoss.toFixed(2)}, TP:${takeProfit.toFixed(2)}`,
        indicators
      };
    }

    if (currentPrice >= upperBand * 0.999) {
      this.position = {
        type: SignalType.SHORT,
        entryPrice: currentPrice,
        entryIndex: index,
        stopLoss,
        takeProfit
      };
      this.dailyTrades++;

      return {
        signal: SignalType.SHORT,
        price: currentPrice,
        reason: `触及上轨(${upperBand.toFixed(2)})做空, SL:${stopLoss.toFixed(2)}, TP:${takeProfit.toFixed(2)}`,
        indicators
      };
    }

    return {
      signal: SignalType.HOLD,
      price: currentPrice,
      reason: '等待触及上下轨',
      indicators
    };
  }

  reset() {
    this.position = null;
    this.dailyTrades = 0;
    this.lastTradeDay = null;
  }
}
