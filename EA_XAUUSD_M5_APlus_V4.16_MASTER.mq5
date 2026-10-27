
#property strict
#property version "4.16"

#include <Trade/Trade.mqh>

CTrade trade;

// EA XAUUSD M5 APlus V4.16 MASTER
// Fondasi keselamatan - belum membuka transaksi.

input string InpSymbol = "XAUUSD";
input ENUM_TIMEFRAMES InpEntryTF = PERIOD_M5;

input double RiskNormalPct = 0.35;
input double RiskSuperPct = 0.50;
input double DailyLossLimitPct = 4.0;

input int MaxSuper = 8;
input int MaxBiasa = 5;
input int MaxRetest = 3;

input int SpreadMaxPoints = 250;
input ulong MagicNumber = 416001;
input int ATRPeriod = 14;
input ENUM_TIMEFRAMES ATRTimeframe = PERIOD_M5;
datetime lastBarTime = 0;

//-----------------------------------------------
int OnInit()
{
   if(RiskNormalPct <= 0 || RiskNormalPct > 100 ||
      RiskSuperPct <= 0 || RiskSuperPct > 100 ||
      DailyLossLimitPct <= 0 || DailyLossLimitPct > 100 ||
      SpreadMaxPoints <= 0 ||
      MaxSuper < 1 || MaxBiasa < 1 || MaxRetest < 1)
   {
      Print("ERROR: Parameter EA tidak valid.");
      return INIT_PARAMETERS_INCORRECT;
   }

   if(!SymbolSelect(InpSymbol, true))
   {
      Print("ERROR: Simbol tidak tersedia: ", InpSymbol);
      return INIT_FAILED;
   }

   trade.SetExpertMagicNumber(MagicNumber);

   Print("APlus V4.16 MASTER: fondasi berhasil dimuat.");
   Print("Mode aman: belum ada transaksi otomatis.");

   return INIT_SUCCEEDED;
}

//-----------------------------------------------
bool ValidasiHargaDanSpread()
{
   if(!SymbolSelect(InpSymbol, true))
      return false;

   MqlTick tick;

   if(!SymbolInfoTick(InpSymbol, tick))
   {
      Print("Data tick belum tersedia.");
      return false;
   }

   if(tick.bid <= 0 || tick.ask <= 0 || tick.ask < tick.bid)
   {
      Print("Data harga tidak valid.");
      return false;
   }

   double point = SymbolInfoDouble(InpSymbol, SYMBOL_POINT);

   if(point <= 0)
   {
      Print("Nilai point simbol tidak valid.");
      return false;
   }

   double spreadPoints = (tick.ask - tick.bid) / point;

   if(spreadPoints > SpreadMaxPoints)
   {
      Print("Spread terlalu tinggi: ",
            DoubleToString(spreadPoints, 1),
            " points. Analisis entry dilewati.");
      return false;
   }

   return true;
}

//-----------------------------------------------
bool DataCandleTersedia()
{
   long synchronized = 0;

   if(!SeriesInfoInteger(
      InpSymbol, InpEntryTF, SERIES_SYNCHRONIZED, synchronized))
   {
      return false;
   }

   if(synchronized == 0)
      return false;

   if(Bars(InpSymbol, InpEntryTF) < 100)
   {
      Print("Data candle belum cukup.");
      return false;
   }

   return true;
}

//-----------------------------------------------
void OnTick()
{
   // Fondasi pemeriksaan saja; tidak membuka transaksi.
   if(!ValidasiHargaDanSpread())
      return;

   if(!DataCandleTersedia())
      return;

   datetime barTime = iTime(InpSymbol, InpEntryTF, 0);

   if(barTime <= 0)
      return;

   if(barTime != lastBarTime)
   {
      lastBarTime = barTime;
      Print("Validasi dasar lolos. Simbol=", InpSymbol,
            ", timeframe=", EnumToString(InpEntryTF));
   }

   // TODO: Bias M1/M5/HTF.
   // TODO: Liquidity sweep, displacement ATR, MSS.
   // TODO: FVG + CE50, Order Block, validasi zona.
   // TODO: Entry, SL, TP zona lawan sejenis.
   // TODO: Risk Guardian, daily loss, Profit Lock.
   // TODO: News Intelligence dan tes keamanan.
}
