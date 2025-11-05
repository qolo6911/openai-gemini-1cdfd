/**
 * 技术指标计算模块
 * Technical Indicators Module
 */

/**
 * 计算简单移动平均线 (SMA)
 * @param {number[]} data - 价格数据数组
 * @param {number} period - 周期
 * @returns {number[]} SMA数组
 */
export function calculateSMA(data, period) {
  const sma = [];

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      sma.push(null); // 数据不足，无法计算
      continue;
    }

    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += data[i - j];
    }
    sma.push(sum / period);
  }

  return sma;
}

/**
 * 计算标准差
 * @param {number[]} data - 数据数组
 * @param {number} period - 周期
 * @param {number[]} sma - 对应的SMA数组
 * @returns {number[]} 标准差数组
 */
export function calculateStdDev(data, period, sma) {
  const stdDev = [];

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1 || sma[i] === null) {
      stdDev.push(null);
      continue;
    }

    let sumSquaredDiff = 0;
    for (let j = 0; j < period; j++) {
      const diff = data[i - j] - sma[i];
      sumSquaredDiff += diff * diff;
    }

    stdDev.push(Math.sqrt(sumSquaredDiff / period));
  }

  return stdDev;
}

/**
 * 计算布林带
 * @param {number[]} prices - 价格数据（通常使用收盘价）
 * @param {number} period - 周期（默认14）
 * @param {number} stdDevMultiplier - 标准差乘数（默认2）
 * @returns {Object} 布林带数据 {upper, middle, lower}
 */
export function calculateBollingerBands(prices, period = 14, stdDevMultiplier = 2) {
  const middle = calculateSMA(prices, period);
  const stdDev = calculateStdDev(prices, period, middle);

  const upper = [];
  const lower = [];

  for (let i = 0; i < prices.length; i++) {
    if (middle[i] === null || stdDev[i] === null) {
      upper.push(null);
      lower.push(null);
    } else {
      upper.push(middle[i] + stdDevMultiplier * stdDev[i]);
      lower.push(middle[i] - stdDevMultiplier * stdDev[i]);
    }
  }

  return { upper, middle, lower };
}

/**
 * 计算线性回归斜率（用于判断趋势角度）
 * @param {number[]} data - 数据数组
 * @param {number} lookback - 回看周期（默认3，用于判断近期趋势）
 * @returns {number[]} 斜率数组
 */
export function calculateSlope(data, lookback = 3) {
  const slopes = [];

  for (let i = 0; i < data.length; i++) {
    if (i < lookback - 1 || data[i] === null) {
      slopes.push(null);
      continue;
    }

    // 简化的线性回归：使用起点和终点计算斜率
    const y1 = data[i - lookback + 1];
    const y2 = data[i];
    const slope = (y2 - y1) / (lookback - 1);

    slopes.push(slope);
  }

  return slopes;
}

/**
 * 将斜率转换为角度（度数）
 * @param {number} slope - 斜率
 * @param {number} baseValue - 基准值（用于归一化）
 * @returns {number} 角度（度数）
 */
export function slopeToAngle(slope, baseValue) {
  if (slope === null || baseValue === null || baseValue === 0) {
    return null;
  }

  // 将斜率归一化为百分比变化率
  const normalizedSlope = slope / baseValue;

  // 转换为角度（弧度转度数）
  const angleRadians = Math.atan(normalizedSlope);
  const angleDegrees = angleRadians * (180 / Math.PI);

  return angleDegrees;
}

/**
 * 判断是否为震荡行情（中轨趋平）
 * @param {number[]} middleBand - 中轨数据
 * @param {number} index - 当前索引
 * @param {number} angleThreshold - 角度阈值（默认30度）
 * @param {number} lookback - 回看周期（默认3）
 * @returns {boolean} 是否为震荡行情
 */
export function isRangebound(middleBand, index, angleThreshold = 30, lookback = 3) {
  if (index < lookback - 1) {
    return false;
  }

  const slopes = calculateSlope(middleBand, lookback);
  const slope = slopes[index];

  if (slope === null) {
    return false;
  }

  const baseValue = middleBand[index];
  const angle = slopeToAngle(slope, baseValue);

  if (angle === null) {
    return false;
  }

  // 判断角度是否在阈值范围内（接近水平）
  return Math.abs(angle) < angleThreshold;
}

/**
 * 计算真实波幅 (ATR - Average True Range)
 * @param {Object[]} candles - K线数据数组 [{high, low, close}]
 * @param {number} period - 周期（默认14）
 * @returns {number[]} ATR数组
 */
export function calculateATR(candles, period = 14) {
  const atr = [];
  const tr = []; // True Range

  for (let i = 0; i < candles.length; i++) {
    if (i === 0) {
      // 第一根K线的TR就是高低差
      tr.push(candles[i].high - candles[i].low);
      atr.push(null);
    } else {
      // TR = max(high-low, |high-prevClose|, |low-prevClose|)
      const highLow = candles[i].high - candles[i].low;
      const highClose = Math.abs(candles[i].high - candles[i - 1].close);
      const lowClose = Math.abs(candles[i].low - candles[i - 1].close);

      tr.push(Math.max(highLow, highClose, lowClose));

      if (i < period) {
        atr.push(null);
      } else if (i === period) {
        // 第一个ATR是TR的简单平均
        let sum = 0;
        for (let j = 1; j <= period; j++) {
          sum += tr[j];
        }
        atr.push(sum / period);
      } else {
        // 后续ATR使用指数移动平均
        // ATR = (Previous ATR * (period - 1) + Current TR) / period
        const prevATR = atr[i - 1];
        atr.push((prevATR * (period - 1) + tr[i]) / period);
      }
    }
  }

  return atr;
}

/**
 * 计算指数移动平均线 (EMA)
 * @param {number[]} data - 价格数据数组
 * @param {number} period - 周期
 * @returns {number[]} EMA数组
 */
export function calculateEMA(data, period) {
  const ema = [];
  const multiplier = 2 / (period + 1);

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      ema.push(null);
    } else if (i === period - 1) {
      // 第一个EMA是SMA
      let sum = 0;
      for (let j = 0; j < period; j++) {
        sum += data[i - j];
      }
      ema.push(sum / period);
    } else {
      // EMA = (Price - Previous EMA) * Multiplier + Previous EMA
      const value = (data[i] - ema[i - 1]) * multiplier + ema[i - 1];
      ema.push(value);
    }
  }

  return ema;
}

/**
 * 计算ADX (Average Directional Index) - 趋势强度指标
 * @param {Object[]} candles - K线数据数组 [{high, low, close}]
 * @param {number} period - 周期（默认14）
 * @returns {number[]} ADX数组
 */
export function calculateADX(candles, period = 14) {
  const adx = [];
  const plusDM = []; // +DM
  const minusDM = []; // -DM
  const tr = []; // True Range
  const plusDI = []; // +DI
  const minusDI = []; // -DI
  const dx = []; // DX

  for (let i = 0; i < candles.length; i++) {
    if (i === 0) {
      plusDM.push(0);
      minusDM.push(0);
      tr.push(candles[i].high - candles[i].low);
      plusDI.push(null);
      minusDI.push(null);
      dx.push(null);
      adx.push(null);
      continue;
    }

    // 计算+DM和-DM
    const highDiff = candles[i].high - candles[i - 1].high;
    const lowDiff = candles[i - 1].low - candles[i].low;

    let currentPlusDM = 0;
    let currentMinusDM = 0;

    if (highDiff > lowDiff && highDiff > 0) {
      currentPlusDM = highDiff;
    }
    if (lowDiff > highDiff && lowDiff > 0) {
      currentMinusDM = lowDiff;
    }

    plusDM.push(currentPlusDM);
    minusDM.push(currentMinusDM);

    // 计算TR
    const highLow = candles[i].high - candles[i].low;
    const highClose = Math.abs(candles[i].high - candles[i - 1].close);
    const lowClose = Math.abs(candles[i].low - candles[i - 1].close);
    tr.push(Math.max(highLow, highClose, lowClose));

    // 计算平滑的+DM, -DM, TR
    if (i >= period) {
      let smoothedPlusDM, smoothedMinusDM, smoothedTR;

      if (i === period) {
        smoothedPlusDM = plusDM.slice(1, period + 1).reduce((a, b) => a + b, 0);
        smoothedMinusDM = minusDM.slice(1, period + 1).reduce((a, b) => a + b, 0);
        smoothedTR = tr.slice(1, period + 1).reduce((a, b) => a + b, 0);
      } else {
        const prevIndex = i - 1;
        smoothedPlusDM = plusDI[prevIndex] * smoothedTR / 100 * (period - 1) + plusDM[i];
        smoothedMinusDM = minusDI[prevIndex] * smoothedTR / 100 * (period - 1) + minusDM[i];
        smoothedTR = tr[prevIndex] * (period - 1) + tr[i];
      }

      // 计算+DI和-DI
      const currentPlusDI = smoothedTR !== 0 ? (smoothedPlusDM / smoothedTR) * 100 : 0;
      const currentMinusDI = smoothedTR !== 0 ? (smoothedMinusDM / smoothedTR) * 100 : 0;

      plusDI.push(currentPlusDI);
      minusDI.push(currentMinusDI);

      // 计算DX
      const diSum = currentPlusDI + currentMinusDI;
      const currentDX = diSum !== 0 ? (Math.abs(currentPlusDI - currentMinusDI) / diSum) * 100 : 0;
      dx.push(currentDX);

      // 计算ADX（DX的EMA）
      if (i === period * 2 - 1) {
        const adxValue = dx.slice(period, period * 2).reduce((a, b) => a + b, 0) / period;
        adx.push(adxValue);
      } else if (i >= period * 2) {
        const adxValue = (adx[adx.length - 1] * (period - 1) + dx[dx.length - 1]) / period;
        adx.push(adxValue);
      } else {
        adx.push(null);
      }
    } else {
      plusDI.push(null);
      minusDI.push(null);
      dx.push(null);
      adx.push(null);
    }
  }

  return adx;
}
