//+------------------------------------------------------------------+
//| XAUUSD M5 APlus V4.16 MASTER - M1 FILTER CLEANUP CANDIDATE                            |
//| Continuation file for the user's EA project                      |
//|                                                                  |
//| IMPORTANT: Development prototype; NOT live-ready.                 |
//| Rule-based SMC/ICT heuristics require MetaEditor compilation,     |
//| visual review and out-of-sample Strategy Tester validation.      |
//| Phases K-N: structural cleanup and static audit; still requires MetaEditor compilation, visual review and demo validation.       |
//| Phase N: input/timeframe/contract preflight hardening; full zone lifecycle registry and MT5 validation still pending. |
//+------------------------------------------------------------------+
#property strict
#property version   "4.16"
#property description "XAUUSD M5 APlus - development build; compile and backtest required"

#include <Trade/Trade.mqh>
CTrade trade;

enum ENUM_ZONE_CATEGORY
  {
   ZONE_NONE   = 0,
   ZONE_SUPER  = 1,
   ZONE_BIASA  = 2,
   ZONE_RETEST = 3
  };

enum ENUM_TRADE_DIRECTION
  {
   DIR_NONE = 0,
   DIR_BUY  = 1,
   DIR_SELL = -1
  };

//--------------------------- INPUTS ---------------------------------
input group "01. General"
input ulong  InpMagicNumber             = 4162026;
input bool   InpAllowNewEntries         = false; // Safety lock: do not enable until compile, news, and execution tests pass
input bool   InpRequireM5Chart          = true;
input bool   InpUseM1Confirmation       = true; // M1 is a closed-candle microstructure confirmation, not an independent entry engine
input bool   InpUseM1MicroConfirmation  = true; // M1 is a confirmation filter; M5 remains the setup/entry timeframe
input bool   InpUseM1EntryConfirmation   = true; // M1 is a confirmation filter; M5 remains the setup/execution timeframe
input int    InpM1MicroSwingBars         = 4; // Closed M1 candles used to define the micro-structure break
input int    InpMaxSlippagePoints       = 30;
input int    InpMaxQuoteAgeSeconds       = 10;
input int    InpEntryRecheckSeconds       = 5; // Recheck intrabar CE50 retracements; 0 = new M5 bars only
input bool   InpRequireTradeAllowed      = true;
input bool   InpRequireHedgingAccount    = true; // Separate category baskets require hedging semantics
input string InpTradeCommentPrefix      = "APlus416";

input group "02. Entry capacity (counts are limits, not signals)"
input int    InpMaxSuperPositions       = 8;
input int    InpMaxBiasaPositions       = 5;
input int    InpMaxRetestPositions      = 3;
input double InpLotSuper                = 0.05;
input double InpLotBiasa                = 0.05;
input double InpLotRetest               = 0.03;

input group "03. Risk Guardian"
input bool   InpUseRiskGuardian         = true;
input double InpRiskNormalPercent       = 0.35; // Risk budget per setup, calculated in account currency
input double InpRiskHighQualityPercent  = 0.50; // Risk budget per setup, calculated in account currency
input double InpDailyLossLimitPercent   = 4.00;
input double InpProfitTargetMoney       = 1000.0; // Account deposit currency; persistent target lock closes EA-owned positions
input bool   InpUseProfitLock           = true;
input bool   InpBlockIfRiskCannotBeCalc = true;
input double InpMaxAggregateOpenRiskPercent = 0.75;
input double InpRiskBufferPercent = 10.0;

input group "04. Spread and trading hours"
input bool   InpUseSpreadFilter         = true;
input int    InpMaxSpreadPoints         = 250;
input bool   InpUseKillzone             = true;
input int    InpUTCOffsetHours          = 7; // WIB = UTC+7; configure explicitly for another location
input int    InpLondonStartHour         = 15;
input int    InpLondonEndHour           = 17;
input int    InpNewYorkStartHour        = 20;
input int    InpNewYorkEndHour          = 22;

input group "05. EMA bias (filter only; not an SMC/ICT entry signal)"
input int    InpEMA_Fast                = 50;
input int    InpEMA_Slow                = 200;
input ENUM_TIMEFRAMES InpBiasTF1         = PERIOD_H1;
input ENUM_TIMEFRAMES InpBiasTF2         = PERIOD_M15;
input group "05A. M1 microstructure confirmation"

input group "06. ATR / SMC-ICT planned parameters"
input int    InpATRPeriod               = 14;
input double InpDisplacementATRMultiple = 1.5;
input double InpFVGEntryFraction        = 0.50; // CE 50%
input double InpMinimumRewardRisk       = 1.0;
input int    InpZoneScanBarsH4          = 50;
input int    InpZoneScanBarsM15         = 20;
input int    InpSwingLookbackM5          = 12;
input int    InpMaxZoneAgeBars            = 48;
input double InpMinFVG_ATR_Fraction       = 0.05;
input double InpCE50ToleranceATR           = 0.20; // Maximum distance from FVG CE50 to current quote

input group "07. News Intelligence"
input bool   InpUseNewsFilter           = true;
input int    InpNewsMinutesBefore       = 30;
input int    InpNewsMinutesAfter        = 30;
input bool   InpBlockWhenNewsDataUnavailable = true;
input string InpNewsCurrency             = "USD"; // MT5 economic calendar currency code
input bool   InpRequireHighImpactOnly     = true;

input group "08. Position management"
input bool   InpUseBreakEven            = true;
input int    InpBreakEvenTriggerPoints   = 400;
input int    InpBreakEvenPlusPoints      = 20;
input bool   InpUseTrailing             = true;
input int    InpTrailingStartPoints      = 600;
input int    InpTrailingDistancePoints   = 300;

//--------------------------- DATA -----------------------------------
struct SZone
  {
   bool               valid;
   ENUM_ZONE_CATEGORY category;
   ENUM_TRADE_DIRECTION direction; // Direction of the zone's expected trade
   double             low;
   double             high;
   double             obLow;       // OB invalidation boundary used for SL
   double             obHigh;
   datetime           created;
   string             source;      // e.g. OB, FVG, liquidity/MSS confluence
  };

int g_hEmaFastTF1 = INVALID_HANDLE;
int g_hEmaSlowTF1 = INVALID_HANDLE;
int g_hEmaFastTF2 = INVALID_HANDLE;
int g_hEmaSlowTF2 = INVALID_HANDLE;
int g_hATR_M5     = INVALID_HANDLE;
datetime g_lastBarTime = 0;
datetime g_lastEntrySignalBar = 0;
datetime g_lastEntryEvaluationTime = 0;
datetime g_riskDayStart = 0;
double g_dayPeakEquity = 0.0;
double g_protectedBalance = 0.0;
double g_targetReferenceBalance = 0.0;
double g_lastObservedBalance = 0.0;
bool g_riskStateReady = false;
bool g_balanceChangeNeedsReview = false;
bool g_profitLockActive = false;
string g_lastStatus = "Initializing";

//--------------------------- UTILITIES ------------------------------
bool IsFinitePositive(const double value)
  {
   return (MathIsValidNumber(value) && value > 0.0 && value != EMPTY_VALUE);
  }

bool IsNewBarM5()
  {
   datetime t = iTime(_Symbol, PERIOD_M5, 0);
   if(t <= 0) return false;
   if(t != g_lastBarTime)
     {
      g_lastBarTime = t;
      return true;
     }
   return false;
  }

bool IndicatorValue(const int handle, const int buffer, const int shift, double &value)
  {
   value = EMPTY_VALUE;
   if(handle == INVALID_HANDLE) return false;
   if(BarsCalculated(handle) <= shift) return false;
   double tmp[1];
   if(CopyBuffer(handle, buffer, shift, 1, tmp) != 1) return false;
   if(!MathIsValidNumber(tmp[0]) || tmp[0] == EMPTY_VALUE) return false;
   value = tmp[0];
   return true;
  }

bool ValidateSymbolAndQuote()
  {
   if(!SymbolSelect(_Symbol, true))
     {
      g_lastStatus = "Cannot select chart symbol";
      return false;
     }

   long tradeMode = 0;
   if(!SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE, tradeMode))
     {
      g_lastStatus = "Cannot read symbol trade mode";
      return false;
     }
   if(InpRequireTradeAllowed &&
      (tradeMode == SYMBOL_TRADE_MODE_DISABLED || tradeMode == SYMBOL_TRADE_MODE_CLOSEONLY))
     {
      g_lastStatus = "Symbol trading mode does not permit new entries";
      return false;
     }

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick) || tick.bid <= 0.0 || tick.ask <= 0.0 || tick.ask < tick.bid)
     {
      g_lastStatus = "Invalid or unavailable Bid/Ask quote";
      return false;
     }
   if(InpMaxQuoteAgeSeconds > 0 && tick.time > 0 && (TimeCurrent() - tick.time) > InpMaxQuoteAgeSeconds)
     {
      g_lastStatus = "Quote is stale; entry blocked";
      return false;
     }
   return true;
  }

// Normalize a requested volume to the broker's volume grid. This helper does
// not make the volume safe by itself; risk-based sizing must be performed first.
bool NormalizeVolumeToSymbol(const double requested, double &normalized)
  {
   normalized = 0.0;
   double vmin = 0.0, vmax = 0.0, vstep = 0.0;
   if(!SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN, vmin) ||
      !SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX, vmax) ||
      !SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP, vstep) ||
      vmin <= 0.0 || vmax < vmin || vstep <= 0.0 || requested <= 0.0)
      return false;

   double capped = MathMin(requested, vmax);
   double steps = MathFloor((capped - vmin) / vstep + 1e-8);
   normalized = vmin + steps * vstep;
   int digits = 0;
   double testStep = vstep;
   while(digits < 8 && MathAbs(testStep - MathRound(testStep)) > 1e-8)
     {
      testStep *= 10.0;
      digits++;
     }
   normalized = NormalizeDouble(normalized, digits);
   return (normalized >= vmin && normalized <= vmax);
  }

// Estimate the loss in account deposit currency for a hypothetical entry/SL.
// Returns false if broker calculation is unavailable; callers must fail closed.
bool EstimateLossAtStop(const ENUM_TRADE_DIRECTION direction,
                        const double volume,
                        const double entryPrice,
                        const double stopPrice,
                        double &lossMoney)
  {
   lossMoney = 0.0;
   if(volume <= 0.0 || entryPrice <= 0.0 || stopPrice <= 0.0 || direction == DIR_NONE)
      return false;
   if((direction == DIR_BUY && stopPrice >= entryPrice) ||
      (direction == DIR_SELL && stopPrice <= entryPrice))
      return false;

   double profit = 0.0;
   ENUM_ORDER_TYPE orderType = (direction == DIR_BUY ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   if(!OrderCalcProfit(orderType, _Symbol, volume, entryPrice, stopPrice, profit))
      return false;
   if(!MathIsValidNumber(profit) || profit >= 0.0)
      return false;
   lossMoney = -profit;
   return (lossMoney > 0.0 && MathIsValidNumber(lossMoney));
  }

bool NormalizePriceToTickSize(const double rawPrice, double &normalizedPrice)
  {
   normalizedPrice=0.0;
   double tickSize=0.0, point=0.0;
   long digitsLong=0;
   if(!SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE,tickSize) || tickSize<=0.0 ||
      !SymbolInfoDouble(_Symbol,SYMBOL_POINT,point) || point<=0.0 ||
      !SymbolInfoInteger(_Symbol,SYMBOL_DIGITS,digitsLong) || rawPrice<=0.0 || !MathIsValidNumber(rawPrice))
      return false;
   // Normalize to the actual tradable tick grid, not just decimal digits.
   normalizedPrice=NormalizeDouble(MathRound(rawPrice/tickSize)*tickSize,(int)digitsLong);
   return (normalizedPrice>0.0 && MathIsValidNumber(normalizedPrice));
  }

bool ValidateStopDistance(const ENUM_TRADE_DIRECTION direction,
                          const double entryPrice,
                          const double stopPrice,
                          const double targetPrice)
  {
   double point=SymbolInfoDouble(_Symbol,SYMBOL_POINT);
   long stopsLevel=0,freezeLevel=0;
   MqlTick tick;
   if(point<=0.0 || !SymbolInfoTick(_Symbol,tick) || tick.bid<=0.0 || tick.ask<=0.0 ||
      !SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL,stopsLevel) ||
      !SymbolInfoInteger(_Symbol,SYMBOL_TRADE_FREEZE_LEVEL,freezeLevel))
      return false;
   // Add one point of tolerance to avoid borderline rejects caused by rounding.
   double minDistance=(double)MathMax(stopsLevel,freezeLevel)*point+point;
   if(direction==DIR_BUY)
      return (entryPrice>0.0 && stopPrice>0.0 && targetPrice>0.0 &&
              stopPrice<entryPrice && targetPrice>entryPrice &&
              (tick.bid-stopPrice)>=minDistance && (targetPrice-tick.bid)>=minDistance);
   if(direction==DIR_SELL)
      return (entryPrice>0.0 && stopPrice>0.0 && targetPrice>0.0 &&
              stopPrice>entryPrice && targetPrice<entryPrice &&
              (stopPrice-tick.ask)>=minDistance && (tick.ask-targetPrice)>=minDistance);
   return false;
  }

// M1 confirmation: require a closed M1 candle to break the prior closed candle
// in the setup direction, while also closing directionally. This is a conservative
// microstructure filter; it does not replace the M5 SMC/ICT setup or HTF bias.
// Canonical M1 confirmation: one closed-candle micro-range break after a qualified M5 setup.
// Legacy switches are retained for input compatibility; all three must be enabled
// for this filter to run. It never generates a trade by itself.
bool ConfirmM1Microstructure(const ENUM_TRADE_DIRECTION direction)
  {
   // Fail closed if any legacy M1 confirmation switch is disabled. These three
   // inputs overlap; treating one disabled switch as a silent bypass would make
   // the actual entry policy ambiguous. Enable all three for this candidate.
   if(!(InpUseM1Confirmation && InpUseM1MicroConfirmation && InpUseM1EntryConfirmation))
     { g_lastStatus="M1 confirmation configuration incomplete; entry blocked"; return false; }
   if(direction!=DIR_BUY && direction!=DIR_SELL)
     { g_lastStatus="M1 confirmation blocked: direction unavailable"; return false; }
   int lookback=MathMax(2,MathMin(InpM1MicroSwingBars,20));
   int need=lookback+2;
   MqlRates m1[]; ArraySetAsSeries(m1,true);
   if(CopyRates(_Symbol,PERIOD_M1,0,need,m1)!=need)
     { g_lastStatus="M1 confirmation blocked: insufficient M1 history"; return false; }
   double priorHigh=-DBL_MAX,priorLow=DBL_MAX;
   for(int i=2;i<need;i++) { priorHigh=MathMax(priorHigh,m1[i].high); priorLow=MathMin(priorLow,m1[i].low); }
   bool confirmed=(direction==DIR_BUY ? (m1[1].close>m1[1].open && m1[1].close>priorHigh)
                                      : (m1[1].close<m1[1].open && m1[1].close<priorLow));
   if(!confirmed) g_lastStatus=(direction==DIR_BUY ? "M5 setup waiting for bullish M1 microstructure break" : "M5 setup waiting for bearish M1 microstructure break");
   return confirmed;
  }

bool ValidateMarketData()
  {
   if(!ValidateSymbolAndQuote()) return false;
   if(Bars(_Symbol, PERIOD_M5) < 100 || (InpUseM1Confirmation && Bars(_Symbol, PERIOD_M1) < 10) || Bars(_Symbol, InpBiasTF1) < InpEMA_Slow + 5 || Bars(_Symbol, InpBiasTF2) < InpEMA_Slow + 5)
     {
      g_lastStatus = "Waiting for enough price bars";
      return false;
     }
   double f1,s1,f2,s2,atr;
   if(!IndicatorValue(g_hEmaFastTF1,0,1,f1) || !IndicatorValue(g_hEmaSlowTF1,0,1,s1) ||
      !IndicatorValue(g_hEmaFastTF2,0,1,f2) || !IndicatorValue(g_hEmaSlowTF2,0,1,s2) ||
      !IndicatorValue(g_hATR_M5,0,1,atr) || !IsFinitePositive(atr))
     {
      g_lastStatus = "Invalid/unavailable indicator data; entry blocked";
      return false;
     }
   return true;
  }

bool CheckSpread()
  {
   if(!InpUseSpreadFilter) return true;
   long spread = 0;
   if(!SymbolInfoInteger(_Symbol, SYMBOL_SPREAD, spread))
     {
      g_lastStatus = "Cannot read spread";
      return false;
     }
   if(spread > InpMaxSpreadPoints)
     {
      g_lastStatus = "Spread too high";
      return false;
     }
   return true;
  }

bool IsHourInWindow(const int hour, const int startHour, const int endHour)
  {
   if(startHour == endHour) return true;
   if(startHour < endHour) return (hour >= startHour && hour < endHour);
   return (hour >= startHour || hour < endHour); // supports windows crossing midnight
  }

bool CheckKillzone()
  {
   if(!InpUseKillzone) return true;
   datetime localTime = TimeGMT() + InpUTCOffsetHours * 3600;
   MqlDateTime dt;
   if(!TimeToStruct(localTime, dt)) return false;
   bool london = IsHourInWindow(dt.hour, InpLondonStartHour, InpLondonEndHour);
   bool ny     = IsHourInWindow(dt.hour, InpNewYorkStartHour, InpNewYorkEndHour);
   return (london || ny);
  }

bool GetEMABias(ENUM_TRADE_DIRECTION &direction)
  {
   direction = DIR_NONE;
   double f1,s1,f2,s2;
   if(!IndicatorValue(g_hEmaFastTF1,0,1,f1) || !IndicatorValue(g_hEmaSlowTF1,0,1,s1) ||
      !IndicatorValue(g_hEmaFastTF2,0,1,f2) || !IndicatorValue(g_hEmaSlowTF2,0,1,s2))
      return false;
   bool bullish = (f1 > s1 && f2 > s2);
   bool bearish = (f1 < s1 && f2 < s2);
   if(bullish) direction = DIR_BUY;
   if(bearish) direction = DIR_SELL;
   return (direction != DIR_NONE);
  }

// Optional M1 confirmation: requires a closed M1 candle to break the previous
// closed candle in the intended direction. This is a lightweight microstructure
// filter, not a complete M1 SMC/ICT engine; it must be validated in Strategy Tester.
int CountPositionsByCategory(const ENUM_ZONE_CATEGORY category, const ENUM_TRADE_DIRECTION direction)
  {
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; --i)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if((ulong)PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      ENUM_POSITION_TYPE ptype = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      if(direction == DIR_BUY && ptype != POSITION_TYPE_BUY) continue;
      if(direction == DIR_SELL && ptype != POSITION_TYPE_SELL) continue;
      string comment = PositionGetString(POSITION_COMMENT);
      // Accept full category names and legacy short markers so positions opened
      // by older development builds are still counted toward hard capacity caps.
      bool matches=false;
      if(category==ZONE_SUPER)
         matches=(StringFind(comment,"SUPER")>=0 || StringFind(comment,"SUP")>=0);
      else if(category==ZONE_BIASA)
         matches=(StringFind(comment,"BIASA")>=0 || StringFind(comment,"BIA")>=0);
      else if(category==ZONE_RETEST)
         matches=(StringFind(comment,"RETEST")>=0 || StringFind(comment,"RET")>=0);
      if(matches) count++;
     }
   return count;
  }

int MaxPositionsForCategory(const ENUM_ZONE_CATEGORY category)
  {
   if(category == ZONE_SUPER) return InpMaxSuperPositions;
   if(category == ZONE_BIASA) return InpMaxBiasaPositions;
   if(category == ZONE_RETEST) return InpMaxRetestPositions;
   return 0;
  }

double LotForCategory(const ENUM_ZONE_CATEGORY category)
  {
   if(category == ZONE_SUPER) return InpLotSuper;
   if(category == ZONE_BIASA) return InpLotBiasa;
   if(category == ZONE_RETEST) return InpLotRetest;
   return 0.0;
  }

string CategoryName(const ENUM_ZONE_CATEGORY category)
  {
   if(category == ZONE_SUPER) return "SUPER";
   if(category == ZONE_BIASA) return "BIASA";
   if(category == ZONE_RETEST) return "RETEST";
   return "NONE";
  }


// Persistent per-zone guard: prevents the same reconstructed zone from
// generating repeated entries after a terminal/EA restart. This is a trade
// usage ledger, not a full historical zone registry; zone quality is still
// reconstructed from closed M5 bars on each evaluation.
string ZoneTradeKey(const SZone &zone,const ENUM_TRADE_DIRECTION direction)
  {
   string sym=StringSubstr(_Symbol,0,8);
   return StringFormat("APZ_%I64d_%I64u_%s_%d_%d_%I64d",
                       AccountInfoInteger(ACCOUNT_LOGIN),InpMagicNumber,
                       sym,(int)zone.category,(int)direction,(long)zone.created);
  }

// Persistent zone snapshot registry (Phase N development increment).
// This stores immutable zone identity/geometry plus lifecycle flags in terminal
// Global Variables. It is a bounded terminal-local registry, not a substitute
// for chart validation or a server-side database.
string ZoneRegistryKey(const SZone &zone,const string field)
  {
   string sym=StringSubstr(_Symbol,0,6);
   return StringFormat("APR_%I64d_%I64u_%s_%d_%I64d_%s",
                      