//+------------------------------------------------------------------+
//| EA_XAUUSD_M5_APlus_V4.16_MASTER.mq5                             |
//| Version: 4.16.1                                                  |
//| Module: Zone Registry - Safe Mode                                |
//| Catatan: Belum membuka order otomatis                            |
//+------------------------------------------------------------------+
#property strict
#property version "4.16.1"
#property description "APlus V4.16.1 - Zone Registry Safe Mode"

#include <Trade/Trade.mqh>
CTrade trade;

//--- Pengaturan umum
input bool   ModeAman              = true;
input bool   LogDiagnostics        = true;
input int    MaxStoredZones        = 200;

//--- Pengaturan validasi zona
input int    ATRPeriod             = 14;
input int    SwingLookback         = 5;
input double DisplacementATR       = 1.20;
input double MinFVG_ATR            = 0.10;
input int    MaxSpreadPoints       = 250;

//--- Batas kategori
input int    MaxSuper              = 8;
input int    MaxBiasa              = 5;
input int    MaxRetest             = 3;

//--- Struktur data zona
struct ZonaFVG
{
   bool   valid;
   bool   bullish;
   double top;
   double bottom;
   double ce50;
};

struct ZonaOB
{
   bool     valid;
   bool     bullish;
   double   top;
   double   bottom;
   datetime sourceTime;
};

struct DataZona
{
   bool     valid;
   bool     bullish;
   string   category;
   double   top;
   double   bottom;
   double   ce50;
   datetime zoneTime;
   ENUM_TIMEFRAMES timeframe;
   bool     mitigated;
   bool     invalidated;
   bool     used;
   string   id;
};

DataZona RegistryZona[];

int atrHandle = INVALID_HANDLE;

//--- Diagnostik
void LogPesan(string pesan)
{
   if(LogDiagnostics)
      Print("[APlus V4.16.1] ", pesan);
}

//--- Validasi parameter
bool ValidasiParameter()
{
   if(ATRPeriod < 2)
   {
      LogPesan("ATRPeriod harus minimal 2.");
      return false;
   }

   if(SwingLookback < 2)
   {
      LogPesan("SwingLookback harus minimal 2.");
      return false;
   }

   if(MaxStoredZones < 10)
   {
      LogPesan("MaxStoredZones terlalu kecil.");
      return false;
   }

   if(MaxSuper < 0 || MaxBiasa < 0 || MaxRetest < 0)
   {
      LogPesan("Batas kategori tidak boleh negatif.");
      return false;
   }

   if(DisplacementATR <= 0 || MinFVG_ATR < 0)
   {
      LogPesan("Parameter ATR tidak valid.");
      return false;
   }

   return true;
}

//--- Validasi harga dan spread
bool ValidasiHargaDanSpread()
{
   MqlTick tick;

   if(!SymbolInfoTick(_Symbol, tick))
      return false;

   if(tick.ask <= 0 || tick.bid <= 0)
      return false;

   if(tick.ask < tick.bid)
      return false;

   double spreadPoints =
      (tick.ask - tick.bid) / _Point;

   if(spreadPoints > MaxSpreadPoints)
      return false;

   return true;
}

//--- Memastikan data candle tersedia
bool DataCandleTersedia(
   ENUM_TIMEFRAMES tf,
   int jumlah
)
{
   if(Bars(_Symbol, tf) < jumlah)
      return false;

   return true;
}

//--- Membaca ATR
double AmbilATR(
   ENUM_TIMEFRAMES tf,
   int shift
)
{
   int handle = INVALID_HANDLE;

   if(tf == PERIOD_CURRENT)
   {
      if(atrHandle == INVALID_HANDLE)
         return 0;

      handle = atrHandle;
   }
   else
   {
      handle = iATR(_Symbol, tf, ATRPeriod);
   }

   if(handle == INVALID_HANDLE)
      return 0;

   double buffer[];
   ArraySetAsSeries(buffer, true);

   int copied = CopyBuffer(
      handle, 0, shift, 1, buffer
   );

   if(tf != PERIOD_CURRENT)
      IndicatorRelease(handle);

   if(copied != 1)
      return 0;

   if(buffer[0] <= 0)
      return 0;

   return buffer[0];
}

//--- Pemeriksaan swing high
bool SwingHighTerdeteksi(
   ENUM_TIMEFRAMES tf,
   int shift,
   int lookback
)
{
   if(shift <= lookback)
      return false;

   double kandidat = iHigh(_Symbol, tf, shift);

   if(kandidat <= 0)
      return false;

   for(int i = 1; i <= lookback; i++)
   {
      if(iHigh(_Symbol, tf, shift-i) >= kandidat)
         return false;

      if(iHigh(_Symbol, tf, shift+i) > kandidat)
         return false;
   }

   return true;
}

//--- Pemeriksaan swing low
bool SwingLowTerdeteksi(
   ENUM_TIMEFRAMES tf,
   int shift,
   int lookback
)
{
   if(shift <= lookback)
      return false;

   double kandidat = iLow(_Symbol, tf, shift);

   if(kandidat <= 0)
      return false;

   for(int i = 1; i <= lookback; i++)
   {
      if(iLow(_Symbol, tf, shift-i) <= kandidat)
         return false;

      if(iLow(_Symbol, tf, shift+i) < kandidat)
         return false;
   }

   return true;
}

//--- Pemeriksaan sweep likuiditas
bool SweepHighTerdeteksi(
   ENUM_TIMEFRAMES tf,
   int shift,
   int lookback
)
{
   double highCandle = iHigh(_Symbol, tf, shift);
   double closeCandle = iClose(_Symbol, tf, shift);

   if(highCandle <= 0 || closeCandle <= 0)
      return false;

   double swingHigh = 0;

   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      double h = iHigh(_Symbol, tf, i);

      if(h > swingHigh)
         swingHigh = h;
   }

   return (
      swingHigh > 0 &&
      highCandle > swingHigh &&
      closeCandle < swingHigh
   );
}

bool SweepLowTerdeteksi(
   ENUM_TIMEFRAMES tf,
   int shift,
   int lookback
)
{
   double lowCandle = iLow(_Symbol, tf, shift);
   double closeCandle = iClose(_Symbol, tf, shift);

   if(lowCandle <= 0 || closeCandle <= 0)
      return false;

   double swingLow = DBL_MAX;

   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      double l = iLow(_Symbol, tf, i);

      if(l < swingLow)
         swingLow = l;
   }

   return (
      swingLow < DBL_MAX &&
      lowCandle < swingLow &&
      closeCandle > swingLow
   );
}