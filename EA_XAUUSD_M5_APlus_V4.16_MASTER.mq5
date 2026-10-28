#property strict
#property version "4.16"

#include <Trade/Trade.mqh>

CTrade trade;

//==================================================
// EA XAUUSD M5 APLUS V4.16 MASTER
// MODE AMAN: BELUM MEMBUKA TRANSAKSI OTOMATIS
//==================================================

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

input int SwingLookback = 3;
input int SwingScanBars = 100;

input double DisplacementATRMultiplier = 1.5;
input double MinBodyToRangeRatio = 0.65;
input double MinFVG_ATR = 0.10;

datetime lastBarTime = 0;
int atrHandle = INVALID_HANDLE;

//--------------------------------------------------
// TIPE DATA ZONA
//--------------------------------------------------

enum KategoriZona
{
ZONA_SUPER = 0,
ZONA_BIASA = 1,
ZONA_RETEST = 2
};

struct ZonaFVG
{
bool valid;
bool bullish;
double batasBawah;
double batasAtas;
double ce50;
};

struct ZonaOB
{
bool valid;
bool bullish;
double batasBawah;
double batasAtas;
datetime waktu;
};

struct DataZona
{
bool valid;
bool bullish;
KategoriZona kategori;
double batasBawah;
double batasAtas;
double ce50;
datetime waktu;
};
//==================================================
// ZONE REGISTRY V4.16.1
// MODE AMAN: tidak membuka transaksi
//==================================================

#define MAX_ZONA_REGISTRY 100

DataZona RegistryZona[MAX_ZONA_REGISTRY];
int JumlahZonaRegistry = 0;

bool ZonaRegistryValid(DataZona &zona)
{
   if(!zona.valid) return false;
   if(zona.batasBawah <= 0.0) return false;
   if(zona.batasAtas <= zona.batasBawah) return false;
   if(zona.ce50 < zona.batasBawah ||
      zona.ce50 > zona.batasAtas) return false;
   if(zona.waktu <= 0) return false;

   if(zona.kategori != ZONA_SUPER &&
      zona.kategori != ZONA_BIASA &&
      zona.kategori != ZONA_RETEST)
      return false;

   return true;
}

int CariZonaRegistry(DataZona &zona, double toleransiHarga)
{
   if(toleransiHarga < 0.0) return -1;

   for(int i = 0; i < JumlahZonaRegistry; i++)
   {
      if(!RegistryZona[i].valid) continue;
      if(RegistryZona[i].bullish != zona.bullish) continue;
      if(RegistryZona[i].kategori != zona.kategori) continue;
      if(RegistryZona[i].waktu != zona.waktu) continue;

      if(MathAbs(RegistryZona[i].batasBawah -
                 zona.batasBawah) > toleransiHarga)
         continue;

      if(MathAbs(RegistryZona[i].batasAtas -
                 zona.batasAtas) > toleransiHarga)
         continue;

      return i;
   }

   return -1;
}

bool SimpanZonaRegistry(DataZona &zona, double toleransiHarga)
{
   if(!ZonaRegistryValid(zona))
   {
      Print("Zone Registry: zona tidak valid.");
      return false;
   }

   int indeks = CariZonaRegistry(zona, toleransiHarga);

   if(indeks >= 0)
   {
      RegistryZona[indeks] = zona;
      return true;
   }

   if(JumlahZonaRegistry >= MAX_ZONA_REGISTRY)
   {
      Print("Zone Registry penuh.");
      return false;
   }

   RegistryZona[JumlahZonaRegistry] = zona;
   JumlahZonaRegistry++;

   Print("Zone Registry: zona disimpan. Total=",
         JumlahZonaRegistry);

   return true;
}

bool NonaktifkanZonaRegistry(int indeks)
{
   if(indeks < 0 || indeks >= JumlahZonaRegistry)
      return false;

   RegistryZona[indeks].valid = false;
   return true;
}

int HitungZonaAktif(KategoriZona kategori, bool bullish)
{
   int total = 0;

   for(int i = 0; i < JumlahZonaRegistry; i++)
   {
      if(!RegistryZona[i].valid) continue;
      if(RegistryZona[i].kategori != kategori) continue;
      if(RegistryZona[i].bullish != bullish) continue;

      total++;
   }

   return total;
}
//--------------------------------------------------
// INISIALISASI DAN PEMBERSIHAN
//--------------------------------------------------

int OnInit()
{
if(RiskNormalPct <= 0 || RiskNormalPct > 100 ||
RiskSuperPct <= 0 || RiskSuperPct > 100 ||
DailyLossLimitPct <= 0 || DailyLossLimitPct > 100 ||
SpreadMaxPoints <= 0 || ATRPeriod < 2 ||
MaxSuper < 1 || MaxBiasa < 1 || MaxRetest < 1 ||
SwingLookback < 1 ||
SwingScanBars <= SwingLookback * 2 ||
DisplacementATRMultiplier <= 0 ||
MinBodyToRangeRatio <= 0 ||
MinBodyToRangeRatio > 1 ||
MinFVG_ATR < 0)
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

Print("APlus V4.16 MASTER berhasil diinisialisasi.");
Print("MODE AMAN: tidak membuka transaksi otomatis.");

return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
if(atrHandle != INVALID_HANDLE)
{
IndicatorRelease(atrHandle);
atrHandle = INVALID_HANDLE;
}
}

//--------------------------------------------------
// VALIDASI DATA PASAR
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
return false;

return true;
}

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

bool ValidasiATR()
{
if(atrHandle == INVALID_HANDLE)
return false;

if(BarsCalculated(atrHandle) < ATRPeriod + 2)
return false;

double atr[1];

if(CopyBuffer(atrHandle, 0, 1, 1, atr) != 1)
return false;

return atr[0] > 0;
}

double AmbilATR(ENUM_TIMEFRAMES tf)
{
int handle = iATR(InpSymbol, tf, ATRPeriod);

if(handle == INVALID_HANDLE)
return 0.0;

double buffer[1];

bool berhasil =
BarsCalculated(handle) >= ATRPeriod + 2 &&
CopyBuffer(handle, 0, 1, 1, buffer) == 1;

IndicatorRelease(handle);

if(!berhasil || buffer[0] <= 0)
return 0.0;

return buffer[0];
}

//--------------------------------------------------
// MODUL 1: SWING HIGH DAN SWING LOW
//--------------------------------------------------

bool DeteksiSwingHigh(ENUM_TIMEFRAMES tf, int shift)
{
int total = Bars(InpSymbol, tf);

if(SwingLookback < 1 || shift <= SwingLookback ||
shift + SwingLookback >= total)
return false;

double nilai = iHigh(InpSymbol, tf, shift);

if(nilai <= 0)
return false;

for(int i = 1; i <= SwingLookback; i++)
{
if(iHigh(InpSymbol, tf, shift - i) >= nilai)
return false;

if(iHigh(InpSymbol, tf, shift + i) > nilai)  
     return false;

}

return true;
}

bool DeteksiSwingLow(ENUM_TIMEFRAMES tf, int shift)
{
int total = Bars(InpSymbol, tf);

if(SwingLookback < 1 || shift <= SwingLookback ||
shift + SwingLookback >= total)
return false;

double nilai = iLow(InpSymbol, tf, shift);

if(nilai <= 0)
return false;

for(int i = 1; i <= SwingLookback; i++)
{
if(iLow(InpSymbol, tf, shift - i) <= nilai)
return false;

if(iLow(InpSymbol, tf, shift + i) < nilai)  
     return false;

}

return true;
}

double AmbilSwingTerakhir(ENUM_TIMEFRAMES tf, bool cariHigh)
{
int total = Bars(InpSymbol, tf);

if(total <= SwingLookback * 2 + 2)
return 0.0;

int batas = (int)MathMin(
SwingScanBars,
total - SwingLookback - 1
);

// Shift terkecil yang diuji adalah swing terbaru
// yang sudah mempunyai candle konfirmasi di sebelah kanan.
for(int shift = SwingLookback + 1;
shift < batas;
shift++)
{
if(cariHigh && DeteksiSwingHigh(tf, shift))
return iHigh(InpSymbol, tf, shift);

if(!cariHigh && DeteksiSwingLow(tf, shift))  
     return iLow(InpSymbol, tf, shift);

}

return 0.0;
}

//--------------------------------------------------
// MODUL 2: LIQUIDITY SWEEP
//--------------------------------------------------

bool DeteksiSweepHigh(ENUM_TIMEFRAMES tf)
{
double swingHigh = AmbilSwingTerakhir(tf, true);

if(swingHigh <= 0)
return false;

double high1 = iHigh(InpSymbol, tf, 1);
double close1 = iClose(InpSymbol, tf, 1);

return high1 > swingHigh && close1 < swingHigh;
}

bool DeteksiSweepLow(ENUM_TIMEFRAMES tf)
{
double swingLow = AmbilSwingTerakhir(tf, false);

if(swingLow <= 0)
return false;

double low1 = iLow(InpSymbol, tf, 1);
double close1 = iClose(InpSymbol, tf, 1);

return low1 < swingLow && close1 > swingLow;
}

//--------------------------------------------------
// MODUL 3: DISPLACEMENT BERBASIS ATR
//--------------------------------------------------

bool DeteksiDisplacement(ENUM_TIMEFRAMES tf, bool bullish)
{
double atr = AmbilATR(tf);

if(atr <= 0)
return false;

double open1 = iOpen(InpSymbol, tf, 1);
double close1 = iClose(InpSymbol, tf, 1);
double high1 = iHigh(InpSymbol, tf, 1);
double low1 = iLow(InpSymbol, tf, 1);

double range = high1 - low1;
double body = MathAbs(close1 - open1);

if(range <= 0)
return false;

if(body < atr * DisplacementATRMultiplier)
return false;

if(body / range < MinBodyToRangeRatio)
return false;

if(bullish)
return close1 > open1;

return close1 < open1;
}

//--------------------------------------------------
// MODUL 4: MARKET STRUCTURE SHIFT (MSS)
//--------------------------------------------------

bool DeteksiMSS(ENUM_TIMEFRAMES tf, bool bullish)
{
double close1 = iClose(InpSymbol, tf, 1);

if(close1 <= 0)
return false;

if(bullish)
{
double swingHigh = AmbilSwingTerakhir(tf, true);

return swingHigh > 0 && close1 > swingHigh;

}

double swingLow = AmbilSwingTerakhir(tf, false);

return swingLow > 0 && close1 < swingLow;
}

//--------------------------------------------------
// MODUL 5: FVG DAN CE50
//--------------------------------------------------

ZonaFVG DeteksiFVG(ENUM_TIMEFRAMES tf)
{
ZonaFVG zona;

zona.valid = false;
zona.bullish = false;
zona.batasBawah = 0;
zona.batasAtas = 0;
zona.ce50 = 0;

if(Bars(InpSymbol, tf) < 10)
return zona;

double high3 = iHigh(InpSymbol, tf, 3);
double low3 = iLow(InpSymbol, tf, 3);
double high1 = iHigh(InpSymbol, tf, 1);
double low1 = iLow(InpSymbol, tf, 1);

if(high3 <= 0 || low3 <= 0 ||
high1 <= 0 || low1 <= 0)
return zona;

if(low1 > high3)
{
zona.valid = true;
zona.bullish = true;
zona.batasBawah = high3;
zona.batasAtas = low1;
}
else if(high1 < low3)
{
zona.valid = true;
zona.bullish = false;
zona.batasBawah = high1;
zona.batasAtas = low3;
}

if(zona.valid)
{
double atr = AmbilATR(tf);

if(atr <= 0 ||  
     zona.batasAtas - zona.batasBawah <  
     atr * MinFVG_ATR)  
  {  
     zona.valid = false;  
     return zona;  
  }  

  zona.ce50 =  
     (zona.batasBawah + zona.batasAtas) / 2.0;

}

return zona;
}

//--------------------------------------------------
// MODUL 6: ORDER BLOCK DASAR
//--------------------------------------------------

ZonaOB DeteksiOB(ENUM_TIMEFRAMES tf, bool bullish)
{
ZonaOB zona;

zona.valid = false;
zona.bullish = bullish;
zona.batasBawah = 0;
zona.batasAtas = 0;
zona.waktu = 0;

int total = Bars(InpSymbol, tf);

if(total < 20)
return zona;

// Cari candle berlawanan sebelum candle displacement.
// Konfirmasi displacement dilakukan terpisah.
for(int shift = 2; shift <= 10 && shift < total; shift++)
{
double openC = iOpen(InpSymbol, tf, shift);
double closeC = iClose(InpSymbol, tf, shift);
double highC = iHigh(InpSymbol, tf, shift);
double lowC = iLow(InpSymbol, tf, shift);

if(highC <= lowC || openC <= 0 || closeC <= 0)  
     continue;  

  bool berlawanan =  
     bullish ? closeC < openC : closeC > openC;  

  if(!berlawanan)  
     continue;  

  zona.valid = true;  
  zona.batasBawah = lowC;  
  zona.batasAtas = highC;  
  zona.waktu = iTime(InpSymbol, tf, shift);  

  return zona;

}

return zona;
}

//--------------------------------------------------
// MODUL 7: BIAS MULTI-TIMEFRAME
//--------------------------------------------------

bool BiasBullish(ENUM_TIMEFRAMES tf)
{
double close1 = iClose(InpSymbol, tf, 1);
double close2 = iClose(InpSymbol, tf, 2);

return close1 > 0 && close2 > 0 && close1 > close2;
}

bool BiasBearish(ENUM_TIMEFRAMES tf)
{
double close1 = iClose(InpSymbol, tf, 1);
double close2 = iClose(InpSymbol, tf, 2);

return close1 > 0 && close2 > 0 && close1 < close2;
}

bool KonfirmasiBiasMTF(bool bullish)
{
if(!DataCandleTersedia(PERIOD_H1) ||
!DataCandleTersedia(PERIOD_M15))
return false;

if(bullish)
return BiasBullish(PERIOD_H1) &&
BiasBullish(PERIOD_M15);

return BiasBearish(PERIOD_H1) &&
BiasBearish(PERIOD_M15);
}

//--------------------------------------------------
// MODUL 8: FILTER MITIGASI DAN INVALIDASI ZONA
//--------------------------------------------------

bool ZonaMasihLayak(
ENUM_TIMEFRAMES tf,
bool bullish,
double batasBawah,
double batasAtas,
int shiftZona
)
{
if(batasBawah <= 0 ||
batasAtas <= batasBawah ||
shiftZona < 1)
return false;

// Invalidation sederhana:
// bullish invalid jika candle berikutnya menutup
// di bawah batas bawah zona.
// bearish invalid jika menutup di atas batas atas.
for(int shift = shiftZona - 1; shift >= 1; shift--)
{
double closeC = iClose(InpSymbol, tf, shift);

if(closeC <= 0)  
     return false;  

  if(bullish && closeC < batasBawah)  
     return false;  

  if(!bullish && closeC > batasAtas)  
     return false;

}

// Tolak zona yang sudah pernah dimasuki harga
// setelah candle pembentuk zona.
for(int shift = shiftZona - 1; shift >= 1; shift--)
{
double highC = iHigh(InpSymbol, tf, shift);
double lowC = iLow(InpSymbol, tf, shift);

bool overlap =  
     highC >= batasBawah && lowC <= batasAtas;  

  if(overlap)  
     return false;

}

return true;
}

//--------------------------------------------------
// MODUL 9: KATEGORI ZONA
//--------------------------------------------------

int BatasEntryKategori(KategoriZona kategori)
{
if(kategori == ZONA_SUPER)
return MaxSuper;

if(kategori == ZONA_BIASA)
return MaxBiasa;

return MaxRetest;
}

// Klasifikasi awal berdasarkan bukti yang tersedia.
// Ini bukan skor kualitas final atau izin entry.
KategoriZona KlasifikasiZona(
bool sweep,
bool displacement,
bool mss,
bool fvg,
bool ob
)
{
int skor = 0;

if(sweep)        skor++;
if(displacement) skor++;
if(mss)          skor++;
if(fvg)          skor++;
if(ob)           skor++;

if(skor >= 5)
return ZONA_SUPER;

if(skor >= 3)
return ZONA_BIASA;

return ZONA_RETEST;
}

//--------------------------------------------------
// MODUL 10: PEMERIKSAAN GABUNGAN
//--------------------------------------------------

bool ValidasiSinyalDasar(bool bullish)
{
   bool sweep = bullish
      ? DeteksiSweepLow(InpEntryTF)
      : DeteksiSweepHigh(InpEntryTF);

   bool displacement =
      DeteksiDisplacement(InpEntryTF, bullish);

   bool mss = DeteksiMSS(InpEntryTF, bullish);

   ZonaFVG fvg = DeteksiFVG(InpEntryTF);
   ZonaOB ob = DeteksiOB(InpEntryTF, bullish);

   bool fvgSearah =
      fvg.valid && fvg.bullish == bullish;

   bool bias = KonfirmasiBiasMTF(bullish);

   if(!sweep || !displacement || !mss ||
      !fvgSearah || !ob.valid || !bias)
      return false;

   // Bentuk data zona dari FVG yang tervalidasi.
   DataZona zona;

   zona.valid = true;
   zona.bullish = bullish;
   zona.batasBawah = fvg.batasBawah;
   zona.batasAtas = fvg.batasAtas;
   zona.ce50 = fvg.ce50;
   zona.waktu = iTime(InpSymbol, InpEntryTF, 1);

   zona.kategori = KlasifikasiZona(
      sweep,
      displacement,
      mss,
      fvgSearah,
      ob.valid
   );

   // Simpan zona dan cegah duplikasi.
   double toleransi =
      SymbolInfoDouble(InpSymbol, SYMBOL_POINT) * 2.0;

   bool tersimpan =
      SimpanZonaRegistry(zona, toleransi);

   if(!tersimpan)
      return false;

   Print("Zona tervalidasi dan diregistrasi. Kategori=",
         (int)zona.kategori,
         " | arah=",
         bullish ? "BUY" : "SELL");

   return true;
}

//--------------------------------------------------
// MODUL 11: PEMANTAUAN DASAR
//--------------------------------------------------

void OnTick()
{
// Mode aman: fungsi ini tidak pernah mengirim order.
if(!ValidasiHargaDanSpread())
return;

if(!DataCandleTersedia(PERIOD_M1) ||
!DataCandleTersedia(PERIOD_M5) ||
!DataCandleTersedia(PERIOD_M15) ||
!DataCandleTersedia(PERIOD_H1) ||
!DataCandleTersedia(PERIOD_H4) ||
!DataCandleTersedia(PERIOD_D1))
return;

if(!ValidasiATR())
return;

datetime barTime = iTime(InpSymbol, InpEntryTF, 0);

if(barTime <= 0 || barTime == lastBarTime)
return;

lastBarTime = barTime;

bool buyValidasi = ValidasiSinyalDasar(true);
bool sellValidasi = ValidasiSinyalDasar(false);

Print("APlus V4.16 | simbol=", InpSymbol,
" | BUY filter=", buyValidasi,
" | SELL filter=", sellValidasi,
" | mode aman aktif.");
}
//==================================================
// MODUL 12: FILTER KONFIRMASI M1
// MODE AMAN: hanya memeriksa sinyal
//==================================================

bool KonfirmasiM1(bool bullish)
{
   if(!DataCandleTersedia(PERIOD_M1))
      return false;

   double open1  = iOpen(InpSymbol, PERIOD_M1, 1);
   double close1 = iClose(InpSymbol, PERIOD_M1, 1);
   double high1  = iHigh(InpSymbol, PERIOD_M1, 1);
   double low1   = iLow(InpSymbol, PERIOD_M1, 1);

   if(open1 <= 0 || close1 <= 0 ||
      high1 <= low1)
      return false;

   if(bullish)
      return close1 > open1;

   return close1 < open1;
}
//==================================================
// MODUL 13: TARGET TP ZONA SEJENIS
// MODE AMAN: menghitung target saja, tidak membuka order
//==================================================

bool CariTargetZonaSejenis(
   DataZona &zonaEntry,
   DataZona &zonaTarget,
   double hargaSekarang
)
{
   if(!ZonaRegistryValid(zonaEntry))
      return false;

   if(hargaSekarang <= 0.0)
      return false;

   double jarakTerbaik = DBL_MAX;
   int indeksTerbaik = -1;

   for(int i = 0; i < JumlahZonaRegistry; i++)
   {
      if(!RegistryZona[i].valid)
         continue;

      // TP harus dari kategori yang sama.
      if(RegistryZona[i].kategori != zonaEntry.kategori)
         continue;

      // Target harus berlawanan arah dengan entry.
      if(RegistryZona[i].bullish == zonaEntry.bullish)
         continue;

      double targetHarga =
         (RegistryZona[i].batasBawah +
          RegistryZona[i].batasAtas) / 2.0;

      // BUY mencari target di atas harga saat ini.
      // SELL mencari target di bawah harga saat ini.
      if(zonaEntry.bullish && targetHarga <= hargaSekarang)
         continue;

      if(!zonaEntry.bullish && targetHarga >= hargaSekarang)
         continue;

      double jarak = MathAbs(targetHarga - hargaSekarang);

      if(jarak < jarakTerbaik)
      {
         jarakTerbaik = jarak;
         indeksTerbaik = i;
      }
   }

   if(indeksTerbaik < 0)
      return false;

   zonaTarget = RegistryZona[indeksTerbaik];
   return true;
}
//==================================================
// MODUL 14: RISK GUARDIAN
// MODE AMAN: pemantauan risiko, tanpa transaksi otomatis
//==================================================

input double MaxRiskPerBasketPct = 0.50;
input double MaxDailyLossPct = 4.0;

bool RiskGuardianValid()
{
   if(MaxRiskPerBasketPct <= 0.0 ||
      MaxRiskPerBasketPct > 100.0)
      return false;

   if(MaxDailyLossPct <= 0.0 ||
      MaxDailyLossPct > 100.0)
      return false;

   return true;
}

double HitungBatasKerugianHarian()
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);

   if(balance <= 0.0)
      return 0.0;

   return balance * MaxDailyLossPct / 100.0;
}

bool RiskGuardianBolehLanjut()
{
   if(!RiskGuardianValid())
   {
      Print("Risk Guardian: parameter risiko tidak valid.");
      return false;
   }

   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity  = AccountInfoDouble(ACCOUNT_EQUITY);

   if(balance <= 0.0 || equity <= 0.0)
      return false;

   double batasRugi = HitungBatasKerugianHarian();

   if(batasRugi <= 0.0)
      return false;

   double floatingLoss = balance - equity;

   if(floatingLoss >= batasRugi)
   {
      Print("Risk Guardian: batas floating loss tercapai.");
      return false;
   }

   return true;
}
//==================================================
// MODUL 15: DAILY LOSS GUARD
// MODE AMAN: pemantauan saja
//==================================================

datetime AwalHariServer()
{
   MqlDateTime waktu;
   TimeToStruct(TimeCurrent(), waktu);

   waktu.hour = 0;
   waktu.min  = 0;
   waktu.sec  = 0;

   return StructToTime(waktu);
}

double HitungKerugianTerealisasiHariIni()
{
   datetime mulai = AwalHariServer();
   datetime sekarang = TimeCurrent();

   if(sekarang <= 0 || mulai <= 0)
      return -1.0;

   if(!HistorySelect(mulai, sekarang))
      return -1.0;

   double hasilBersih = 0.0;
   int total = HistoryDealsTotal();

   for(int i = 0; i < total; i++)
   {
      ulong tiket = HistoryDealGetTicket(i);

      if(tiket == 0)
         continue;

      ENUM_DEAL_TYPE tipe =
         (ENUM_DEAL_TYPE)HistoryDealGetInteger(
            tiket, DEAL_TYPE);

      if(tipe != DEAL_TYPE_BUY &&
         tipe != DEAL_TYPE_SELL)
         continue;

      hasilBersih +=
         HistoryDealGetDouble(tiket, DEAL_PROFIT) +
         HistoryDealGetDouble(tiket, DEAL_SWAP) +
         HistoryDealGetDouble(tiket, DEAL_COMMISSION);
   }

   return hasilBersih;
}

bool BatasRugiHarianTercapai()
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);

   if(balance <= 0.0)
      return true;

   double hasilHariIni = HitungKerugianTerealisasiHariIni();

   if(hasilHariIni < 0.0)
   {
      Print("Daily Loss Guard: data riwayat gagal dibaca.");
      return true;
   }

   double batasRugi = balance * MaxDailyLossPct / 100.0;

   if(hasilHariIni <= -batasRugi)
   {
      Print("Daily Loss Guard: batas kerugian harian tercapai.");
      return true;
   }

   return false;
}
//==================================================
// MODUL 16: NEWS FILTER
// MODE AMAN: filter jadwal manual
//==================================================

input bool AktifkanNewsFilter = true;
input datetime NewsMulai = 0;
input datetime NewsSelesai = 0;

bool NewsSedangBerlangsung()
{
   if(!AktifkanNewsFilter)
      return false;

   // Jadwal belum diatur.
   if(NewsMulai <= 0 || NewsSelesai <= 0)
      return false;

   if(NewsSelesai <= NewsMulai)
   {
      Print("News Filter: jadwal tidak valid.");
      return true;
   }

   datetime sekarang = TimeTradeServer();

   if(sekarang <= 0)
      return true;

   return sekarang >= NewsMulai &&
          sekarang <= NewsSelesai;
}

bool NewsFilterBolehLanjut()
{
   if(NewsSedangBerlangsung())
   {
      Print("News Filter: waktu diblokir.");
      return false;
   }

   return true;
}
//==================================================
// MODUL 17: VALIDASI DATA INDIKATOR
// MODE AMAN: pemeriksaan data saja
//==================================================

bool ValidasiDataIndikator(ENUM_TIMEFRAMES tf)
{
   if(!DataCandleTersedia(tf))
      return false;

   int handleATR = iATR(InpSymbol, tf, ATRPeriod);

   if(handleATR == INVALID_HANDLE)
      return false;

   bool valid = false;

   if(BarsCalculated(handleATR) >= ATRPeriod + 2)
   {
      double atrBuffer[2];

      if(CopyBuffer(handleATR, 0, 1, 2, atrBuffer) == 2)
      {
         valid =
            atrBuffer[0] > 0.0 &&
            atrBuffer[1] > 0.0 &&
            MathIsValidNumber(atrBuffer[0]) &&
            MathIsValidNumber(atrBuffer[1]);
      }
   }

   IndicatorRelease(handleATR);

   if(!valid)
      Print("Validasi indikator gagal pada timeframe ",
            EnumToString(tf));

   return valid;
}

bool ValidasiSemuaTimeframe()
{
   if(!ValidasiDataIndikator(PERIOD_M1))  return false;
   if(!ValidasiDataIndikator(PERIOD_M5))  return false;
   if(!ValidasiDataIndikator(PERIOD_M15)) return false;
   if(!ValidasiDataIndikator(PERIOD_H1))  return false;
   if(!ValidasiDataIndikator(PERIOD_H4))  return false;
   if(!ValidasiDataIndikator(PERIOD_D1))  return false;

   return true;
}
//==================================================
// MODUL 18: PENGAMAN SPREAD DAN EKSEKUSI
// MODE AMAN: tidak mengirim order
//==================================================

input int DeviasiMaksimalPoints = 30;

bool ValidasiEksekusiPasar()
{
   if(!ValidasiHargaDanSpread())
   {
      Print("Execution Guard: spread atau harga tidak valid.");
      return false;
   }

   if(DeviasiMaksimalPoints < 0)
   {
      Print("Execution Guard: deviasi tidak valid.");
      return false;
   }

   if(!TerminalInfoInteger(TERMINAL_CONNECTED))
   {
      Print("Execution Guard: terminal tidak terhubung.");
      return false;
   }

   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
   {
      Print("Execution Guard: trading EA tidak diizinkan.");
      return false;
   }

   return true;
}

bool ValidasiVolumeOrder(double volume)
{
   double minLot = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_STEP);

   if(volume <= 0.0 || minLot <= 0.0 ||
      maxLot < minLot || stepLot <= 0.0)
      return false;

   if(volume < minLot || volume > maxLot)
      return false;

   double langkah = (volume - minLot) / stepLot;

   return MathAbs(langkah - MathRound(langkah)) < 0.000001;
}
//==================================================
// MODUL 19: PEMERIKSAAN POSISI DAN BATAS ENTRY
// MODE AMAN: tidak membuka atau menutup transaksi
//==================================================

input int MaxPosisiEA = 8;

int HitungPosisiEA()
{
   int total = 0;

   for(int i = 0; i < PositionsTotal(); i++)
   {
      ulong tiket = PositionGetTicket(i);

      if(tiket == 0)
         continue;

      string simbol = PositionGetString(POSITION_SYMBOL);
      ulong magic = (ulong)PositionGetInteger(POSITION_MAGIC);

      if(simbol == InpSymbol && magic == MagicNumber)
         total++;
   }

   return total;
}

bool BatasPosisiEAValid()
{
   if(MaxPosisiEA < 1)
      return false;

   int posisiAktif = HitungPosisiEA();

   if(posisiAktif >= MaxPosisiEA)
   {
      Print("Position Guard: batas posisi EA tercapai. Jumlah=",
            posisiAktif);
      return false;
   }

   return true;
}
//==================================================
// MODUL 20: PROFIT LOCK GUARD
// MODE AMAN: pemantauan saja
//==================================================

input bool AktifkanProfitLock = true;
input double ProfitLockAktifUSD = 10.0;
input double ProfitLockMundurUSD = 3.0;

double PuncakEkuitasEA = 0.0;
bool ProfitLockTerpicu = false;

void PerbaruiProfitLock()
{
   if(!AktifkanProfitLock)
      return;

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);

   if(equity <= 0.0)
      return;

   if(PuncakEkuitasEA <= 0.0)
      PuncakEkuitasEA = equity;

   if(equity > PuncakEkuitasEA)
      PuncakEkuitasEA = equity;

   double kenaikan = equity -
                     AccountInfoDouble(ACCOUNT_BALANCE);

   if(kenaikan >= ProfitLockAktifUSD &&
      PuncakEkuitasEA - equity >= ProfitLockMundurUSD)
   {
      ProfitLockTerpicu = true;

      Print("Profit Lock terpicu. Pemantauan saja; ",
            "tidak ada posisi yang ditutup otomatis.");
   }
}

bool ProfitLockBolehLanjut()
{
   PerbaruiProfitLock();

   return !ProfitLockTerpicu;
}
//==================================================
// MODUL 21: SAFETY GATE
// MODE AMAN: tidak membuka transaksi
//==================================================

bool SafetyGateLolos()
{
   if(!ValidasiHargaDanSpread())
      return false;

   if(!DataCandleTersedia(PERIOD_M1) ||
      !DataCandleTersedia(PERIOD_M5) ||
      !DataCandleTersedia(PERIOD_M15) ||
      !DataCandleTersedia(PERIOD_H1) ||
      !DataCandleTersedia(PERIOD_H4) ||
      !DataCandleTersedia(PERIOD_D1))
      return false;

   if(!ValidasiSemuaTimeframe())
      return false;

   if(!RiskGuardianBolehLanjut())
      return false;

   if(BatasRugiHarianTercapai())
      return false;

   if(!NewsFilterBolehLanjut())
      return false;

   if(!ValidasiEksekusiPasar())
      return false;

   if(!BatasPosisiEAValid())
      return false;

   if(!ProfitLockBolehLanjut())
      return false;

   return true;
}