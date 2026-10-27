
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

 //--------------------------------------------------
// MODUL 1: DETEKSI SWING HIGH DAN SWING LOW
// Hanya membaca struktur candle; tidak membuka transaksi.

input int SwingLookback = 3;
input int SwingScanBars = 100;

bool DeteksiSwingHigh(ENUM_TIMEFRAMES tf, int shift)
{
   if(SwingLookback < 1 || shift <= SwingLookback)
      return false;

   if(shift + SwingLookback >= Bars(InpSymbol, tf))
      return false;

   double nilai = iHigh(InpSymbol, tf, shift);
   if(nilai <= 0)
      return false;

   for(int i = 1; i <= SwingLookback; i++)
   {
      if(iHigh(InpSymbol, tf, shift-i) >= nilai)
         return false;

      if(iHigh(InpSymbol, tf, shift+i) > nilai)
         return false;
   }

   return true;
}

bool DeteksiSwingLow(ENUM_TIMEFRAMES tf, int shift)
{
   if(SwingLookback < 1 || shift <= SwingLookback)
      return false;

   if(shift + SwingLookback >= Bars(InpSymbol, tf))
      return false;

   double nilai = iLow(InpSymbol, tf, shift);
   if(nilai <= 0)
      return false;

   for(int i = 1; i <= SwingLookback; i++)
   {
      if(iLow(InpSymbol, tf, shift-i) <= nilai)
         return false;

      if(iLow(InpSymbol, tf, shift+i) < nilai)
         return false;
   }

   return true;
}

// Mengambil swing terakhir yang sudah terkonfirmasi.
double AmbilSwingTerakhir(ENUM_TIMEFRAMES tf, bool cariHigh)
{
   if(SwingScanBars <= SwingLookback * 2)
      return 0.0;

   int batas = MathMin(
      SwingScanBars,
      Bars(InpSymbol, tf) - SwingLookback - 1
   );

   for(int shift = SwingLookback + 1; shift < batas; shift++)
   {
      if(cariHigh && DeteksiSwingHigh(tf, shift))
         return iHigh(InpSymbol, tf, shift);

      if(!cariHigh && DeteksiSwingLow(tf, shift))
         return iLow(InpSymbol, tf, shift);
   }

 //--------------------------------------------------
// MODUL 2: DETEKSI LIQUIDITY SWEEP
// Hanya mendeteksi sweep pada candle yang sudah tertutup.
// Tidak membuka transaksi.

bool DeteksiSweepHigh(ENUM_TIMEFRAMES tf)
{
   double swingHigh = AmbilSwingTerakhir(tf, true);
   if(swingHigh <= 0.0)
      return false;

   double highCandle = iHigh(InpSymbol, tf, 1);
   double closeCandle = iClose(InpSymbol, tf, 1);

   if(highCandle <= 0.0 || closeCandle <= 0.0)
      return false;

   // Harga menembus swing high, lalu ditutup kembali di bawahnya.
   return highCandle > swingHigh && closeCandle < swingHigh;
}

bool DeteksiSweepLow(ENUM_TIMEFRAMES tf)
{
   double swingLow = AmbilSwingTerakhir(tf, false);
   if(swingLow <= 0.0)
      return false;

   double lowCandle = iLow(InpSymbol, tf, 1);
   double closeCandle = iClose(InpSymbol, tf, 1);

   if(lowCandle <= 0.0 || closeCandle <= 0.0)
      return false;

   // Harga menembus swing low, lalu ditutup kembali di atasnya.
   return lowCandle < swingLow && closeCandle > swingLow;
}

   return 0.0;
}

 //--------------------------------------------------
// MODUL 3: DISPLACEMENT BERBASIS ATR
// Memeriksa candle tertutup; tidak membuka transaksi.

input double DisplacementATRMultiplier = 1.5;
input double MinBodyToRangeRatio = 0.65;

bool DeteksiDisplacement(ENUM_TIMEFRAMES tf, bool bullish)
{
   if(DisplacementATRMultiplier <= 0.0 ||
      MinBodyToRangeRatio <= 0.0 ||
      MinBodyToRangeRatio > 1.0)
      return false;

   int handle = iATR(InpSymbol, tf, ATRPeriod);
   if(handle == INVALID_HANDLE)
      return false;

   double atr[1];
   bool dataSiap =
      BarsCalculated(handle) >= ATRPeriod + 2 &&
      CopyBuffer(handle, 0, 1, 1, atr) == 1;

   IndicatorRelease(handle);

   if(!dataSiap || atr[0] <= 0.0)
      return false;

   double open1  = iOpen(InpSymbol, tf, 1);
   double close1 = iClose(InpSymbol, tf, 1);
   double high1  = iHigh(InpSymbol, tf, 1);
   double low1   = iLow(InpSymbol, tf, 1);

   double range = high1 - low1;
   double body = MathAbs(close1 - open1);

   if(range <= 0.0)
      return false;

   if(body < atr[0] * DisplacementATRMultiplier)
      return false;

   if(body / range < MinBodyToRangeRatio)
      return false;

   if(bullish)
      return close1 > open1;

   return close1 < open1;
}

 //--------------------------------------------------
// MODUL 4: MARKET STRUCTURE SHIFT (MSS)
// Pemeriksaan struktur sederhana; tidak membuka transaksi.

bool DeteksiMSS(ENUM_TIMEFRAMES tf, bool bullish)
{
   double close1 = iClose(InpSymbol, tf, 1);

   if(close1 <= 0.0)
      return false;

   if(bullish)
   {
      double swingHigh = AmbilSwingTerakhir(tf, true);

      if(swingHigh <= 0.0)
         return false;

      return close1 > swingHigh;
   }
   else
   {
      double swingLow = AmbilSwingTerakhir(tf, false);

      if(swingLow <= 0.0)
         return false;

      return close1 < swingLow;
   }
}

 //--------------------------------------------------
// MODUL 5: FAIR VALUE GAP (FVG) + CE50
// Membaca tiga candle yang sudah tertutup.
// Tidak membuka transaksi.

struct ZonaFVG
{
   bool valid;
   bool bullish;
   double batasBawah;
   double batasAtas;
   double ce50;
};

ZonaFVG DeteksiFVG(ENUM_TIMEFRAMES tf)
{
   ZonaFVG zona;
   zona.valid = false;
   zona.bullish = false;
   zona.batasBawah = 0.0;
   zona.batasAtas = 0.0;
   zona.ce50 = 0.0;

   // Candle terbaru yang tertutup = shift 1.
   // Bandingkan dengan candle shift 3.
   double high3 = iHigh(InpSymbol, tf, 3);
   double low3  = iLow(InpSymbol, tf, 3);
   double high1 = iHigh(InpSymbol, tf, 1);
   double low1  = iLow(InpSymbol, tf, 1);

   if(high3 <= 0.0 || low3 <= 0.0 ||
      high1 <= 0.0 || low1 <= 0.0)
      return zona;

   // Bullish FVG: low candle 1 di atas high candle 3.
   if(low1 > high3)
   {
      zona.valid = true;
      zona.bullish = true;
      zona.batasBawah = high3;
      zona.batasAtas = low1;
   }
   // Bearish FVG: high candle 1 di bawah low candle 3.
   else if(high1 < low3)
   {
      zona.valid = true;
      zona.bullish = false;
      zona.batasBawah = high1;
      zona.batasAtas = low3;
   }

   if(zona.valid)
      zona.ce50 = (zona.batasBawah + zona.batasAtas) / 2.0;

   return zona;
}

 //--------------------------------------------------
// MODUL 6: ORDER BLOCK (OB) DASAR
// Mencari candle berlawanan sebelum displacement.
// Tidak membuka transaksi.

struct ZonaOB
{
   bool valid;
   bool bullish;
   double batasBawah;
   double batasAtas;
   datetime waktu;
};

ZonaOB DeteksiOB(ENUM_TIMEFRAMES tf, bool bullish)
{
   ZonaOB zona;
   zona.valid = false;
   zona.bullish = bullish;
   zona.batasBawah = 0.0;
   zona.batasAtas = 0.0;
   zona.waktu = 0;

   // Cari candle sumber di antara candle 2 sampai 10.
   for(int shift = 2; shift <= 10; shift++)
   {
      double openC = iOpen(InpSymbol, tf, shift);
      double closeC = iClose(InpSymbol, tf, shift);
      double highC = iHigh(InpSymbol, tf, shift);
      double lowC = iLow(InpSymbol, tf, shift);

      if(openC <= 0.0 || closeC <= 0.0 ||
         highC <= lowC)
         continue;

      bool candleBerlawanan =
         bullish ? (closeC < openC) : (closeC > openC);

      if(!candleBerlawanan)
         continue;

      zona.valid = true;
      zona.batasBawah = lowC;
      zona.batasAtas = highC;
      zona.waktu = iTime(InpSymbol, tf, shift);

      return zona;
   }

   return zona;
}
