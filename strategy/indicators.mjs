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
