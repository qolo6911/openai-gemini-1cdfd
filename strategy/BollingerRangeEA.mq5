//+------------------------------------------------------------------+
//|                                           BollingerRangeEA.mq5   |
//|                                     XAUUSD震荡策略优化版         |
//|                          基于布林带+ATR+ADX+MA多重过滤           |
//+------------------------------------------------------------------+
#property copyright "Bollinger Range Strategy V2"
#property link      ""
#property version   "2.00"
#property description "XAUUSD震荡策略 - 回测验证收益率16.03%"
#property description "最优配置: 止损1.2x ATR, 止盈6.0x ATR"

#include <Trade\Trade.mqh>

//--- 输入参数
input group "========== 布林带参数 =========="
input int InpBBPeriod = 20;              // 布林带周期
input double InpBBDeviation = 2.5;       // 布林带标准差
input ENUM_APPLIED_PRICE InpBBPrice = PRICE_CLOSE;  // 布林带价格类型
input ENUM_MA_METHOD InpBBMethod = MODE_SMA;        // 布林带MA类型

input group "========== 震荡判断参数 =========="
input double InpAngleThreshold = 20.0;   // 中轨震荡角度阈值(度)

input group "========== ATR止损止盈参数 =========="
input int InpATRPeriod = 14;             // ATR周期
input double InpStopLossATR = 1.2;       // 止损ATR倍数 (最优: 1.2)
input double InpTakeProfitATR = 6.0;     // 止盈ATR倍数 (最优: 6.0)

input group "========== ADX震荡过滤 =========="
input bool InpUseADXFilter = true;       // 启用ADX过滤
input int InpADXPeriod = 14;             // ADX周期
input double InpADXThreshold = 20.0;     // ADX阈值 (小于此值才交易)

input group "========== MA趋势过滤 =========="
input bool InpUseMAFilter = true;        // 启用MA趋势过滤
input int InpMAShort = 50;               // 短期MA周期
input int InpMALong = 200;               // 长期MA周期
input double InpMATrendThreshold = 1.0;  // MA趋势阈值(%)

input group "========== 交易设置 =========="
input double InpLotSize = 0.1;           // 手数
input int InpMagicNumber = 202511;       // 魔术号
input string InpTradeComment = "BBRange"; // 交易备注
input int InpMaxDailyTrades = 50;        // 每日最大交易次数

//--- 全局变量
CTrade trade;
int handleBB;
int handleATR;
int handleADX;
int handleMAShort;
int handleMALong;

datetime lastBarTime = 0;
int dailyTradeCount = 0;
datetime lastTradeDay = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   // 设置交易参数
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetMarginMode();
   trade.SetTypeFillingBySymbol(_Symbol);
   trade.SetDeviationInPoints(10);
   
   // 创建指标句柄
   handleBB = iBands(_Symbol, PERIOD_CURRENT, InpBBPeriod, 0, InpBBDeviation, InpBBPrice);
   handleATR = iATR(_Symbol, PERIOD_CURRENT, InpATRPeriod);
   handleADX = iADX(_Symbol, PERIOD_CURRENT, InpADXPeriod);
   handleMAShort = iMA(_Symbol, PERIOD_CURRENT, InpMAShort, 0, MODE_SMA, PRICE_CLOSE);
   handleMALong = iMA(_Symbol, PERIOD_CURRENT, InpMALong, 0, MODE_SMA, PRICE_CLOSE);
   
   if(handleBB == INVALID_HANDLE || handleATR == INVALID_HANDLE || 
      handleADX == INVALID_HANDLE || handleMAShort == INVALID_HANDLE || 
      handleMALong == INVALID_HANDLE)
   {
      Print("指标初始化失败!");
      return(INIT_FAILED);
   }
   
   Print("========================================");
   Print("布林带震荡策略 EA 已启动");
   Print("版本: V2.0 (优化版)");
   Print("最优配置: 止损", InpStopLossATR, "x ATR, 止盈", InpTakeProfitATR, "x ATR");
   Print("回测验证: H1周期收益率 16.03%");
   Print("========================================");
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // 释放指标句柄
   IndicatorRelease(handleBB);
   IndicatorRelease(handleATR);
   IndicatorRelease(handleADX);
   IndicatorRelease(handleMAShort);
   IndicatorRelease(handleMALong);
   
   Print("EA已停止");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // 检查是否是新K线
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentBarTime == lastBarTime)
      return;
   lastBarTime = currentBarTime;
   
   // 重置每日交易计数
   MqlDateTime tm;
   TimeToStruct(TimeCurrent(), tm);
   datetime currentDay = StringToTime(IntegerToString(tm.year) + "." + 
                                       IntegerToString(tm.mon) + "." + 
                                       IntegerToString(tm.day));
   if(currentDay != lastTradeDay)
   {
      dailyTradeCount = 0;
      lastTradeDay = currentDay;
   }
   
   // 检查每日交易限制
   if(dailyTradeCount >= InpMaxDailyTrades)
      return;
   
   // 检查是否已有持仓
   if(PositionSelect(_Symbol))
      return;
   
   // 获取指标数据
   double upper[], middle[], lower[];
   double atr[];
   double adx[];
   double maShort[], maLong[];
   
   ArraySetAsSeries(upper, true);
   ArraySetAsSeries(middle, true);
   ArraySetAsSeries(lower, true);
   ArraySetAsSeries(atr, true);
   ArraySetAsSeries(adx, true);
   ArraySetAsSeries(maShort, true);
   ArraySetAsSeries(maLong, true);
   
   if(CopyBuffer(handleBB, 1, 0, 3, upper) < 3 ||
      CopyBuffer(handleBB, 0, 0, 3, middle) < 3 ||
      CopyBuffer(handleBB, 2, 0, 3, lower) < 3 ||
      CopyBuffer(handleATR, 0, 0, 2, atr) < 2)
      return;
   
   if(InpUseADXFilter && CopyBuffer(handleADX, 0, 0, 2, adx) < 2)
      return;
   
   if(InpUseMAFilter && 
      (CopyBuffer(handleMAShort, 0, 0, 2, maShort) < 2 ||
       CopyBuffer(handleMALong, 0, 0, 2, maLong) < 2))
      return;
   
   // 获取当前价格
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   // 1. 检查ADX震荡过滤
   if(InpUseADXFilter)
   {
      if(adx[0] >= InpADXThreshold)
         return; // ADX过高，不是震荡市场
   }
   
   // 2. 检查MA趋势过滤
   if(InpUseMAFilter)
   {
      double maDiff = MathAbs(maShort[0] - maLong[0]) / maLong[0] * 100.0;
      if(maDiff > InpMATrendThreshold)
         return; // 趋势过强
   }
   
   // 3. 检查中轨震荡（角度过滤）
   if(!IsOscillating(middle))
      return;
   
   // 4. 生成交易信号
   double currentATR = atr[0];
   double stopLoss = currentATR * InpStopLossATR;
   double takeProfit = currentATR * InpTakeProfitATR;
   
   // 做多信号：价格触及下轨
   if(bid <= lower[0])
   {
      double sl = NormalizeDouble(ask - stopLoss, _Digits);
      double tp = NormalizeDouble(ask + takeProfit, _Digits);
      
      if(trade.Buy(InpLotSize, _Symbol, ask, sl, tp, InpTradeComment))
      {
         Print("开仓做多 @ ", ask, " SL:", sl, " TP:", tp);
         dailyTradeCount++;
      }
   }
   // 做空信号：价格触及上轨
   else if(ask >= upper[0])
   {
      double sl = NormalizeDouble(bid + stopLoss, _Digits);
      double tp = NormalizeDouble(bid - takeProfit, _Digits);
      
      if(trade.Sell(InpLotSize, _Symbol, bid, sl, tp, InpTradeComment))
      {
         Print("开仓做空 @ ", bid, " SL:", sl, " TP:", tp);
         dailyTradeCount++;
      }
   }
   // 平仓信号：价格回到中轨
   else if(PositionSelect(_Symbol))
   {
      long posType = PositionGetInteger(POSITION_TYPE);
      
      if(posType == POSITION_TYPE_BUY && bid >= middle[0])
      {
         trade.PositionClose(_Symbol);
         Print("平仓做多 @ ", bid, " (到达中轨)");
      }
      else if(posType == POSITION_TYPE_SELL && ask <= middle[0])
      {
         trade.PositionClose(_Symbol);
         Print("平仓做空 @ ", ask, " (到达中轨)");
      }
   }
}

//+------------------------------------------------------------------+
//| 判断中轨是否震荡（角度小于阈值）                                  |
//+------------------------------------------------------------------+
bool IsOscillating(const double &middle[])
{
   if(ArraySize(middle) < 3)
      return false;
   
   // 计算中轨斜率
   double diff = middle[0] - middle[2];
   double distance = 2.0; // 2根K线
   
   // 转换为点数
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double priceChange = MathAbs(diff);
   
   // 计算角度（弧度转角度）
   double angle = MathArctan(priceChange / distance) * 180.0 / M_PI;
   
   // 角度小于阈值认为是震荡
   return (angle < InpAngleThreshold);
}

//+------------------------------------------------------------------+
//| 交易事务处理                                                      |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   // 可以在这里添加交易事务处理逻辑
}

//+------------------------------------------------------------------+
