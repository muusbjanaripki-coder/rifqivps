
#property strict
#property version "4.16"

#include <Trade/Trade.mqh>

CTrade trade;

// APlus V4.16 MASTER
// Fondasi validasi saja. Tidak membuka transaksi.

input string InpSymbol = "XAUUSD";
input ENUM_TIMEFRAMES InpEntryTF = PERIOD_M5;

input double RiskNormalPct = 0.35;
input double RiskSuperPct = 0.50;
input double DailyLossLimitPct = 4.0;

input int MaxSuper = 8;
input int MaxBiasa = 5;
input int MaxRetest = 3;

input int SpreadMaxPoints = 250;
input int ATRPeriod = 14;
input ulong MagicNumber = 416001;

datetime lastBarTime = 0;
int atrHandle = INVALID_HANDLE;

//--------------------------------------------------
int OnInit()
{
   if(RiskNormalPct <= 0 || RiskNormalPct > 100 ||
      RiskSuperPct <= 0 || RiskSuperPct > 100 ||
      DailyLossLimitPct <= 0 || DailyLossLimitPct > 100 ||
      SpreadMaxPoints <= 0 || ATRPeriod < 2 ||
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

   atrHandle = iATR(InpSymbol, InpEntryTF, ATRPeriod);

   if(atrHandle == INVALID_HANDLE)
   {
      Print("ERROR: Gagal membuat indikator ATR.");
      return INIT_FAILED;
   }

   trade.SetExpertMagicNumber(MagicNumber);

   Print("APlus V4.16: validasi dasar aktif.");
   Print("Mode aman: transaksi otomatis tidak aktif.");

   return INIT_SUCCEEDED;
}

//--------------------------------------------------
void OnDeinit(const int reason)
{
   if(atrHandle != INVALID_HANDLE)
   {
      IndicatorRelease(atrHandle);
      atrHandle = INVALID_HANDLE;
   }
}

//--------------------------------------------------
bool ValidasiHargaDanSpread()
{
   MqlTick tick;

   if(!SymbolInfoTick(InpSymbol, tick))
      return false;

   if(tick.bid <= 0 || tick.ask <= 0 || tick.ask < tick.bid)
      return false;

   double point = SymbolInfoDouble(InpSymbol, SYMBOL_POINT);

   if(point <= 0)
      return false;

   double spreadPoints = (tick.ask - tick.bid) / point;

   if(spreadPoints > SpreadMaxPoints)
   {
      Print("Spread melebihi batas: ",
            DoubleToString(spreadPoints, 1), " points");
      return false;
   }

   return true;
}

//--------------------------------------------------
bool DataCandleTersedia(ENUM_TIMEFRAMES tf)
{
   long synchronized = 0;

   if(!SeriesInfoInteger(
      InpSymbol, tf, SERIES_SYNCHRONIZED, synchronized))
      return false;

   if(synchronized == 0)
      return false;

   return Bars(InpSymbol, tf) >= 100;
}

//--------------------------------------------------
bool ValidasiATR()
{
   if(atrHandle == INVALID_HANDLE)
      return false;

   if(BarsCalculated(atrHandle) < ATRPeriod + 2)
      return false;

   double atrBuffer[1];

   if(CopyBuffer(atrHandle, 0, 1, 1, atrBuffer) != 1)
      return false;

   if(atrBuffer[0] <= 0)
      return false;

   return true;
}

//--------------------------------------------------
void OnTick()
{
   // Tidak membuka posisi.
   if(!ValidasiHargaDanSpread())
      return;

   if(!DataCandleTersedia(PERIOD_M1))
      return;

   if(!DataCandleTersedia(PERIOD_M5))
      return;

   if(!DataCandleTersedia(InpEntryTF))
      return;

   if(!ValidasiATR())
      return;

   datetime barTime = iTime(InpSymbol, InpEntryTF, 0);

   if(barTime <= 0)
      return;

   if(barTime != lastBarTime)
   {
      lastBarTime = barTime;
      Print("Validasi dasar M1/M5 dan ATR berhasil. Simbol=",
            InpSymbol, ", TF=", EnumToString(InpEntryTF));
   }

   // Belum ada logika entry.
   // TODO: Bias multi-timeframe.
   // TODO: Sweep, displacement ATR, MSS.
   // TODO: FVG + CE50 dan Order Block.
   // TODO: Zona Super, Biasa, Retest.
   // TODO: Entry, SL, TP zona lawan sejenis.
   // TODO: Risk Guardian dan Profit Lock.
   // TODO: News Intelligence.
}
