#property strict
#property version "4.162"
#property description "APlus V4.16.2 MASTER - SIGNAL_ONLY monitoring build"

#include <Trade/Trade.mqh>
CTrade trade;

//==================================================
// EA XAUUSD M5 APLUS V4.16.2 MASTER
// SAFE MODE: SIGNAL_ONLY
//==================================================

input string InpSymbol = "XAUUSD";
string SymbolKerja = "";

input ENUM_TIMEFRAMES InpEntryTF = PERIOD_M5;

enum ModeOperasiEA
{
   SIGNAL_ONLY = 0,
   AUTO_TRADE = 1
};

input ModeOperasiEA ModeOperasi = SIGNAL_ONLY;

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

input double MaxRiskPerBasketPct = 0.50;
input double MaxDailyLossPct = 4.0;

input bool AktifkanNewsFilter = false;
input datetime NewsMulai = 0;
input datetime NewsSelesai = 0;

input int DeviasiMaksimalPoints = 30;
input int MaxPosisiEA = 8;

input bool AktifkanProfitLock = true;
input bool TampilkanZonaChart = true;
input bool AktifkanAlertSinyal = false;

input int ZonaExtendBars = 30;
input double ProfitLockAktifUSD = 10.0;
input double ProfitLockMundurUSD = 3.0;

//==================================================
// STATE GLOBAL
//==================================================

datetime lastBarTime = 0;
int atrHandle = INVALID_HANDLE;

double EkuitasAwalHari = 0.0;
datetime HariTercatat = 0;
double PuncakEkuitasEA = 0.0;
double EkuitasAwalProfitLock = 0.0;

bool ProfitLockTerpicu = false;

double MetrikAwalHariEA = 0.0;
double PuncakMetrikHariEA = 0.0;

bool DailyLossTerpicu = false;

string GVPrefix = "";
string RegistryGVPrefix = "";

bool StatePersistenceOK = false;

//==================================================
// STRUKTUR ZONA
//==================================================

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
// REGISTRY GLOBAL
//==================================================

#define MAX_ZONA_REGISTRY 100

DataZona RegistryZona[MAX_ZONA_REGISTRY];
int JumlahZonaRegistry = 0;

//==================================================
// VISUALISASI ZONA
//==================================================

string NamaObjekZona(DataZona &zona)
{
   string arah = zona.bullish ? "BUY" : "SELL";

   return StringFormat(
      "A416_%I64u_%s_%d_%I64d",
      MagicNumber,
      arah,
      (int)zona.kategori,
      (long)zona.waktu
   );
}

//==================================================
// VALIDASI ZONA REGISTRY
//==================================================

bool ZonaRegistryValid(DataZona &zona)
{
   if(!zona.valid ||
      !MathIsValidNumber(zona.batasBawah) ||
      !MathIsValidNumber(zona.batasAtas) ||
      !MathIsValidNumber(zona.ce50) ||
      zona.batasBawah <= 0.0 ||
      zona.batasAtas <= zona.batasBawah ||
      zona.ce50 < zona.batasBawah ||
      zona.ce50 > zona.batasAtas ||
      zona.waktu <= 0)
   {
      return false;
   }

   if(zona.kategori != ZONA_SUPER &&
      zona.kategori != ZONA_BIASA &&
      zona.kategori != ZONA_RETEST)
   {
      return false;
   }

   return true;
}

//==================================================
// NAMA OBJEK DAN GAMBAR ZONA
//==================================================

void GambarZona(DataZona &zona)
{
   if(!TampilkanZonaChart || !ZonaRegistryValid(zona))
      return;

   string name = NamaObjekZona(zona);

   datetime t1 = zona.waktu;

   int sec = PeriodSeconds(InpEntryTF);

   if(sec <= 0)
      sec = 300;

   datetime t2 = TimeCurrent() + sec * MathMax(1, ZonaExtendBars);

   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(
         0,
         name,
         OBJ_RECTANGLE,
         0,
         t1,
         zona.batasAtas,
         t2,
         zona.batasBawah
      );
   }
   else
   {
      ObjectMove(0, name, 0, t1, zona.batasAtas);
      ObjectMove(0, name, 1, t2, zona.batasBawah);
   }

   color clr = zona.bullish ? clrDarkSeaGreen : clrLightCoral;

   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_DOT);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
   ObjectSetInteger(0, name, OBJPROP_FILL, true);
   ObjectSetInteger(0, name, OBJPROP_BACK, true);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);

   string label = name + "_TXT";

   string cat =
      zona.kategori == ZONA_SUPER ? "SUPER" :
      zona.kategori == ZONA_BIASA ? "BIASA" : "RETEST";

   string txt = cat +
                (zona.bullish ? " BUY" : " SELL") +
                " | CE50 " +
                DoubleToString(zona.ce50, _Digits);

   if(ObjectFind(0, label) < 0)
      ObjectCreate(0, label, OBJ_TEXT, 0, t2, zona.ce50);
   else
      ObjectMove(0, label, 0, t2, zona.ce50);

   ObjectSetString(0, label, OBJPROP_TEXT, txt);
   ObjectSetInteger(0, label, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, label, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, label, OBJPROP_SELECTABLE, false);
}

//==================================================
// CARI ZONA YANG SAMA
//==================================================

int CariZonaRegistry(DataZona &zona, double toleransiHarga)
{
   if(!MathIsValidNumber(toleransiHarga) ||
      toleransiHarga < 0.0 ||
      JumlahZonaRegistry < 0 ||
      JumlahZonaRegistry > MAX_ZONA_REGISTRY ||
      !ZonaRegistryValid(zona))
   {
      return -1;
   }

   for(int i = 0; i < JumlahZonaRegistry; i++)
   {
      if(!RegistryZona[i].valid)
         continue;

      if(RegistryZona[i].bullish != zona.bullish ||
         RegistryZona[i].kategori != zona.kategori ||
         RegistryZona[i].waktu != zona.waktu)
      {
         continue;
      }

      if(MathAbs(
         RegistryZona[i].batasBawah - zona.batasBawah
      ) > toleransiHarga)
      {
         continue;
      }

      if(MathAbs(
         RegistryZona[i].batasAtas - zona.batasAtas
      ) > toleransiHarga)
      {
         continue;
      }

      return i;
   }

   return -1;
}

//==================================================
// CARI SLOT KOSONG
//==================================================

int CariSlotKosongRegistry()
{
   if(JumlahZonaRegistry < 0 ||
      JumlahZonaRegistry > MAX_ZONA_REGISTRY)
   {
      return -1;
   }

   for(int i = 0; i < JumlahZonaRegistry; i++)
   {
      if(!RegistryZona[i].valid)
         return i;
   }

   if(JumlahZonaRegistry < MAX_ZONA_REGISTRY)
      return JumlahZonaRegistry;

   return -1;
}

//==================================================
// SIMPAN SATU ZONA KE GLOBAL VARIABLE
//==================================================

bool SimpanSatuZonaRegistry(int indeks)
{
   if(RegistryGVPrefix == "" ||
      indeks < 0 ||
      indeks >= MAX_ZONA_REGISTRY)
   {
      return false;
   }

   string k = IntegerToString(indeks) + "_";

   DataZona z = RegistryZona[indeks];

   bool ok = true;

   ok = (GlobalVariableSet(
      RegistryGVPrefix + k + "v",
      z.valid ? 1.0 : 0.0
   ) > 0) && ok;

   ok = (GlobalVariableSet(
      RegistryGVPrefix + k + "b",
      z.bullish ? 1.0 : 0.0
   ) > 0) && ok;

   ok = (GlobalVariableSet(
      RegistryGVPrefix + k + "k",
      (double)z.kategori
   ) > 0) && ok;

   ok = (GlobalVariableSet(
      RegistryGVPrefix + k + "lo",
      z.batasBawah
   ) > 0) && ok;

   ok = (GlobalVariableSet(
      RegistryGVPrefix + k + "hi",
      z.batasAtas
   ) > 0) && ok;

   ok = (GlobalVariableSet(
      RegistryGVPrefix + k + "ce",
      z.ce50
   ) > 0) && ok;

   ok = (GlobalVariableSet(
      RegistryGVPrefix + k + "tm",
      (double)z.waktu
   ) > 0) && ok;

   return ok;
}

//==================================================
// SIMPAN SEMUA ZONA REGISTRY
//==================================================

bool SimpanSemuaZonaRegistry()
{
   if(RegistryGVPrefix == "" ||
      JumlahZonaRegistry < 0 ||
      JumlahZonaRegistry > MAX_ZONA_REGISTRY)
   {
      return false;
   }

   bool ok = true;

   for(int i = 0; i < MAX_ZONA_REGISTRY; i++)
   {
      if(i < JumlahZonaRegistry)
      {
         if(!SimpanSatuZonaRegistry(i))
            ok = false;
      }
      else
      {
         string k = IntegerToString(i) + "_";

         GlobalVariableSet(RegistryGVPrefix + k + "v", 0.0);
      }
   }

   if(!GlobalVariableSet(
      RegistryGVPrefix + "count",
      (double)JumlahZonaRegistry
   ))
   {
      ok = false;
   }

   GlobalVariablesFlush();

   return ok;
}

//==================================================
// SIMPAN ZONA DENGAN ROLLBACK
//==================================================

bool SimpanZonaRegistry(DataZona &zona, double toleransiHarga)
{
   if(!ZonaRegistryValid(zona))
   {
      Print("Zone Registry: zona tidak valid.");
      return false;
   }

   if(!MathIsValidNumber(toleransiHarga) ||
      toleransiHarga < 0.0)
   {
      Print("Zone Registry: toleransi tidak valid.");
      return false;
   }

   if(JumlahZonaRegistry < 0 ||
      JumlahZonaRegistry > MAX_ZONA_REGISTRY)
   {
      Print("Zone Registry: jumlah slot di luar batas.");
      return false;
   }

   int idx = CariZonaRegistry(zona, toleransiHarga);

   if(idx < 0)
      idx = CariSlotKosongRegistry();

   if(idx < 0 || idx >= MAX_ZONA_REGISTRY)
   {
      Print("Zone Registry penuh.");
      return false;
   }

   int jumlahLama = JumlahZonaRegistry;

   bool slotBaru = (idx == jumlahLama);

   DataZona zonaLama;

   if(!slotBaru)
      zonaLama = RegistryZona[idx];

   RegistryZona[idx] = zona;

   if(slotBaru)
      JumlahZonaRegistry++;

   if(!SimpanSemuaZonaRegistry())
   {
      RegistryZona[idx] = zonaLama;
      JumlahZonaRegistry = jumlahLama;

      Print("Zone Registry: penyimpanan gagal, rollback dilakukan.");

      return false;
   }

   GambarZona(zona);

   Print(
      "Zone Registry: zona tersimpan pada slot ",
      idx,
      ". Total=",
      JumlahZonaRegistry
   );

   return true;
}

//==================================================
// PULIHKAN ZONA DARI GLOBAL VARIABLE
//==================================================

bool PulihkanZonaRegistry()
{
   if(RegistryGVPrefix == "")
      return false;

   JumlahZonaRegistry = 0;

   if(!GlobalVariableCheck(RegistryGVPrefix + "count"))
   {
      Print("Zone Registry: belum ada data tersimpan.");

      GlobalVariableSet(RegistryGVPrefix + "count", 0.0);
      GlobalVariablesFlush();

      return true;
   }

   double countValue = 0.0;

   if(!GlobalVariableGet(
      RegistryGVPrefix + "count",
      countValue
   ))
   {
      return false;
   }

   if(!MathIsValidNumber(countValue) ||
      countValue < 0 ||
      countValue > MAX_ZONA_REGISTRY)
   {
      Print("Zone Registry: nilai count tidak valid.");
      return false;
   }

   int count = (int)countValue;

   for(int i = 0; i < MAX_ZONA_REGISTRY; i++)
   {
      RegistryZona[i].valid = false;
      RegistryZona[i].bullish = false;
      RegistryZona[i].kategori = ZONA_SUPER;
      RegistryZona[i].batasBawah = 0.0;
      RegistryZona[i].batasAtas = 0.0;
      RegistryZona[i].ce50 = 0.0;
      RegistryZona[i].waktu = 0;
   }

   for(int i = 0; i < count; i++)
   {
      string k = IntegerToString(i) + "_";

      double v, b, kategori, lo, hi, ce, tm;

      if(!GlobalVariableGet(RegistryGVPrefix + k + "v", v) ||
         !GlobalVariableGet(RegistryGVPrefix + k + "b", b) ||
         !GlobalVariableGet(RegistryGVPrefix + k + "k", kategori) ||
         !GlobalVariableGet(RegistryGVPrefix + k + "lo", lo) ||
         !GlobalVariableGet(RegistryGVPrefix + k + "hi", hi) ||
         !GlobalVariableGet(RegistryGVPrefix + k + "ce", ce) ||
         !GlobalVariableGet(RegistryGVPrefix + k + "tm", tm))
      {
         Print("Zone Registry: data slot ", i, " tidak lengkap.");
         return false;
      }

      if(v < 0.5)
         continue;

      if(kategori < ZONA_SUPER || kategori > ZONA_RETEST)
         return false;

      DataZona z;

      z.valid = true;
      z.bullish = (b >= 0.5);
      z.kategori = (KategoriZona)(int)kategori;
      z.batasBawah = lo;
      z.batasAtas = hi;
      z.ce50 = ce;
      z.waktu = (datetime)tm;

      if(!ZonaRegistryValid(z))
      {
         Print("Zone Registry: zona rusak pada slot ", i);
         return false;
      }

      RegistryZona[i] = z;

      if(i >= JumlahZonaRegistry)
         JumlahZonaRegistry = i + 1;

      GambarZona(RegistryZona[i]);
   }

   Print(
      "Zone Registry: pemulihan selesai. Zona aktif=",
      JumlahZonaRegistry
   );

   return true;
}

//==================================================
// NONAKTIFKAN ZONA
//==================================================

bool NonaktifkanZonaRegistry(int indeks)
{
   if(indeks < 0 || indeks >= JumlahZonaRegistry)
      return false;

   RegistryZona[indeks].valid = false;

   if(!SimpanSemuaZonaRegistry())
   {
      Print("Zone Registry: gagal menyimpan status nonaktif.");
      return false;
   }

   return true;
}

//==================================================
// HITUNG ZONA AKTIF
//==================================================

int HitungZonaAktif(KategoriZona kategori, bool bullish)
{
   int jumlah = 0;

   for(int i = 0; i < JumlahZonaRegistry; i++)
   {
      if(!RegistryZona[i].valid)
         continue;

      if(RegistryZona[i].kategori == kategori &&
         RegistryZona[i].bullish == bullish)
      {
         jumlah++;
      }
   }

   return jumlah;
}

//==================================================
// SYMBOL RESOLVER
//==================================================

bool AkhiranSimbolDiizinkan(string suffix)
{
   if(suffix == "")
      return true;

   string allowed[] =
   {
      "c", "m", ".pro", ".raw", ".ecn",
      ".a", ".i", "_pro", "-pro"
   };

   string low = suffix;
   StringToLower(low);

   for(int i = 0; i < ArraySize(allowed); i++)
   {
      if(low == allowed[i])
         return true;
   }

   return false;
}

string CariSimbolKerja()
{
   string base = InpSymbol;
   StringToUpper(base);

   if(base != "XAUUSD")
      return "";

   string chart = _Symbol;
   string upper = chart;

   StringToUpper(upper);

   if(StringFind(upper, "XAUUSD") == 0 &&
      AkhiranSimbolDiizinkan(StringSubstr(chart, 6)) &&
      SymbolSelect(chart, true))
   {
      return chart;
   }

   if(SymbolSelect(InpSymbol, true))
      return InpSymbol;

   int total = SymbolsTotal(false);

   for(int i = 0; i < total; i++)
   {
      string candidate = SymbolName(i, false);

      string u = candidate;
      StringToUpper(u);

      if(StringFind(u, "XAUUSD") != 0)
         continue;

      if(!AkhiranSimbolDiizinkan(StringSubstr(candidate, 6)))
         continue;

      if(SymbolSelect(candidate, true))
         return candidate;
   }

   return "";
}

//==================================================
// GLOBAL VARIABLE PREFIX
//==================================================

string BuatGVPrefix()
{
   long login = AccountInfoInteger(ACCOUNT_LOGIN);

   string server = AccountInfoString(ACCOUNT_SERVER);
   StringReplace(server, " ", "_");

   string sym = SymbolKerja;

   StringReplace(sym, ".", "_");
   StringReplace(sym, "-", "_");

   string key = StringFormat(
      "A416_%I64d_%s_%s_%I64u",
      login,
      server,
      sym,
      MagicNumber
   );

   if(StringLen(key) > 60)
      key = StringSubstr(key, 0, 60);

   return key;
}

bool SimpanGV(string nama, double nilai)
{
   if(GlobalVariableSet(GVPrefix + nama, nilai) == 0)
   {
      Print(
         "State save gagal: ",
         nama,
         " err=",
         GetLastError()
      );

      return false;
   }

   GlobalVariablesFlush();

   return true;
}

bool BacaGV(string nama, double &nilai)
{
   if(!GlobalVariableCheck(GVPrefix + nama))
      return false;

   return GlobalVariableGet(GVPrefix + nama, nilai);
}

//==================================================
// INISIALISASI
//==================================================

int OnInit()
{
   if(ModeOperasi != SIGNAL_ONLY)
   {
      Print(
         "AUTO_TRADE BELUM TERSEDIA. "
         "Gunakan SIGNAL_ONLY sampai execution engine divalidasi."
      );

      return INIT_PARAMETERS_INCORRECT;
   }

   if(RiskNormalPct <= 0 || RiskNormalPct > 100 ||
      RiskSuperPct <= 0 || RiskSuperPct > 100 ||
      DailyLossLimitPct <= 0 || DailyLossLimitPct > 100 ||
      MaxDailyLossPct <= 0 || MaxDailyLossPct > 100 ||
      MaxRiskPerBasketPct <= 0 || MaxRiskPerBasketPct > 100 ||
      SpreadMaxPoints <= 0 ||
      ATRPeriod < 2 ||
      MaxSuper < 1 ||
      MaxBiasa < 1 ||
      MaxRetest < 1 ||
      SwingLookback < 1 ||
      SwingScanBars <= SwingLookback * 2 ||
      DisplacementATRMultiplier <= 0 ||
      MinBodyToRangeRatio <= 0 ||
      MinBodyToRangeRatio > 1 ||
      MinFVG_ATR < 0 ||
      MaxPosisiEA < 1 ||
      DeviasiMaksimalPoints < 0 ||
      ProfitLockAktifUSD < 0 ||
      ProfitLockMundurUSD < 0 ||
      ZonaExtendBars < 1)
   {
      Print("ERROR: Parameter EA tidak valid.");
      return INIT_PARAMETERS_INCORRECT;
   }

   SymbolKerja = CariSimbolKerja();

   if(SymbolKerja == "")
   {
      Print("ERROR: Simbol XAUUSD tidak ditemukan.");
      return INIT_FAILED;
   }

   GVPrefix = BuatGVPrefix();

   StatePersistenceOK = (GVPrefix != "");

   RegistryGVPrefix = StringSubstr(GVPrefix, 0, 24) + "_ZR_";

   if(!StatePersistenceOK || !PulihkanZonaRegistry())
   {
      Print("ERROR: State/Zone Registry gagal dipulihkan.");
      return INIT_FAILED;
   }

   Print(
      "[SYMBOL] Chart=",
      _Symbol,
      " | Symbol kerja=",
      SymbolKerja,
      " | SAFE MODE aktif."
   );

   atrHandle = iATR(SymbolKerja, InpEntryTF, ATRPeriod);

   if(atrHandle == INVALID_HANDLE)
   {
      Print("ERROR: Gagal membuat indikator ATR.");
      return INIT_FAILED;
   }

   trade.SetExpertMagicNumber(MagicNumber);

   Print(
      "APlus V4.16.2 diinisialisasi. "
      "MODE SIGNAL_ONLY aktif."
   );

   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(atrHandle != INVALID_HANDLE)
   {
      IndicatorRelease(atrHandle);
      atrHandle = INVALID_HANDLE;
   }

   // Objek zona dipertahankan saat EA dilepas.
}

//--------------------------------------------------
// MODUL 1: SWING
//--------------------------------------------------
bool DeteksiSwingHigh(ENUM_TIMEFRAMES tf,int shift) {
   int total=Bars(SymbolKerja,tf);
   if(SwingLookback<1 || shift<=SwingLookback || shift+SwingLookback>=total) return false;
   double v=iHigh(SymbolKerja,tf,shift);
   if(v<=0) return false;
   for(int i=1;i<=SwingLookback;i++) {
      if(iHigh(SymbolKerja,tf,shift-i)>=v || iHigh(SymbolKerja,tf,shift+i)>v) return false;
   }
   return true;
}

bool DeteksiSwingLow(ENUM_TIMEFRAMES tf,int shift) {
   int total=Bars(SymbolKerja,tf);
   if(SwingLookback<1 || shift<=SwingLookback || shift+SwingLookback>=total) return false;
   double v=iLow(SymbolKerja,tf,shift);
   if(v<=0) return false;
   for(int i=1;i<=SwingLookback;i++) {
      if(iLow(SymbolKerja,tf,shift-i)<=v || iLow(SymbolKerja,tf,shift+i)<v) return false;
   }
   return true;
}

double AmbilSwingTerakhir(ENUM_TIMEFRAMES tf,bool cariHigh) {
   int total=Bars(SymbolKerja,tf);
   if(total<=SwingLookback*2+2) return 0.0;
   int batas=(int)MathMin(SwingScanBars,total-SwingLookback-1);
   for(int shift=SwingLookback+1;shift<batas;shift++) {
      if(cariHigh && DeteksiSwingHigh(tf,shift)) return iHigh(SymbolKerja,tf,shift);
      if(!cariHigh && DeteksiSwingLow(tf,shift)) return iLow(SymbolKerja,tf,shift);
   }
   return 0.0;
}

//--------------------------------------------------
// MODUL 2: LIQUIDITY SWEEP
//--------------------------------------------------
bool DeteksiSweepHigh(ENUM_TIMEFRAMES tf) {
   double s=AmbilSwingTerakhir(tf,true);
   if(s<=0) return false;
   return iHigh(SymbolKerja,tf,1)>s && iClose(SymbolKerja,tf,1)<s;
}
bool DeteksiSweepLow(ENUM_TIMEFRAMES tf) {
   double s=AmbilSwingTerakhir(tf,false);
   if(s<=0) return false;
   return iLow(SymbolKerja,tf,1)<s && iClose(SymbolKerja,tf,1)>s;
}

//--------------------------------------------------
// MODUL 3: DISPLACEMENT
//--------------------------------------------------
bool DeteksiDisplacement(ENUM_TIMEFRAMES tf,bool bullish) {
   double atr=AmbilATR(tf);
   if(atr<=0) return false;
   double o=iOpen(SymbolKerja,tf,1), c=iClose(SymbolKerja,tf,1);
   double h=iHigh(SymbolKerja,tf,1), l=iLow(SymbolKerja,tf,1);
   double range=h-l, body=MathAbs(c-o);
   if(range<=0 || body<atr*DisplacementATRMultiplier || body/range<MinBodyToRangeRatio)
      return false;
   return bullish ? c>o : c<o;
}

//--------------------------------------------------
// MODUL 4: MARKET STRUCTURE SHIFT
//--------------------------------------------------
bool DeteksiMSS(ENUM_TIMEFRAMES tf,bool bullish) {
   double c=iClose(SymbolKerja,tf,1);
   if(c<=0) return false;
   if(bullish) {
      double s=AmbilSwingTerakhir(tf,true);
      return s>0 && c>s;
   }
   double s=AmbilSwingTerakhir(tf,false);
   return s>0 && c<s;
}

//--------------------------------------------------
// MODUL 5: FVG DAN CE50
//--------------------------------------------------
ZonaFVG DeteksiFVG(ENUM_TIMEFRAMES tf) {
   ZonaFVG z; z.valid=false; z.bullish=false; z.batasBawah=0; z.batasAtas=0; z.ce50=0;
   if(Bars(SymbolKerja,tf)<10) return z;
   double h3=iHigh(SymbolKerja,tf,3), l3=iLow(SymbolKerja,tf,3);
   double h1=iHigh(SymbolKerja,tf,1), l1=iLow(SymbolKerja,tf,1);
   if(h3<=0 || l3<=0 || h1<=0 || l1<=0) return z;
   if(l1>h3) { z.batasBawah=h3; z.batasAtas=l1; z.bullish=true; z.valid=true; }
   else if(h1<l3) { z.batasBawah=h1; z.batasAtas=l3; z.bullish=false; z.valid=true; }
   if(z.valid) {
      double atr=AmbilATR(tf);
      if(atr<=0 || z.batasAtas<=z.batasBawah ||
         z.batasAtas-z.batasBawah<atr*MinFVG_ATR) z.valid=false;
      else z.ce50=(z.batasBawah+z.batasAtas)/2.0;
   }
   return z;
}

//--------------------------------------------------
// MODUL 6: ORDER BLOCK DASAR
//--------------------------------------------------
ZonaOB DeteksiOB(ENUM_TIMEFRAMES tf,bool bullish) {
   ZonaOB z; z.valid=false; z.bullish=bullish; z.batasBawah=0; z.batasAtas=0; z.waktu=0;
   int total=Bars(SymbolKerja,tf);
   if(total<20) return z;
   for(int shift=2;shift<=10 && shift<total;shift++) {
      double o=iOpen(SymbolKerja,tf,shift), c=iClose(SymbolKerja,tf,shift);
      double h=iHigh(SymbolKerja,tf,shift), l=iLow(SymbolKerja,tf,shift);
      if(h<=l || o<=0 || c<=0) continue;
      bool opposite=bullish ? c<o : c>o;
      if(!opposite) continue;
      z.valid=true; z.batasBawah=l; z.batasAtas=h; z.waktu=iTime(SymbolKerja,tf,shift);
      return z;
   }
   return z;
}

//--------------------------------------------------
// MODUL 7: BIAS MULTI-TIMEFRAME
//--------------------------------------------------
bool BiasBullish(ENUM_TIMEFRAMES tf) {
   double c1=iClose(SymbolKerja,tf,1), c2=iClose(SymbolKerja,tf,2);
   return c1>0 && c2>0 && c1>c2;
}
bool BiasBearish(ENUM_TIMEFRAMES tf) {
   double c1=iClose(SymbolKerja,tf,1), c2=iClose(SymbolKerja,tf,2);
   return c1>0 && c2>0 && c1<c2;
}
bool KonfirmasiBiasMTF(bool bullish) {
   if(!DataCandleTersedia(PERIOD_H1) || !DataCandleTersedia(PERIOD_M15)) return false;
   return bullish ? (BiasBullish(PERIOD_H1)&&BiasBullish(PERIOD_M15))
                  : (BiasBearish(PERIOD_H1)&&BiasBearish(PERIOD_M15));
}

//--------------------------------------------------
// MODUL 8: FILTER MITIGASI / INVALIDASI FVG
//--------------------------------------------------
bool ZonaMasihLayak(ENUM_TIMEFRAMES tf,bool bullish,double bawah,double atas,int shiftZona) {
   if(bawah<=0 || atas<=bawah || shiftZona<1) return false;
   int total=Bars(SymbolKerja,tf);
   if(total<=shiftZona+1) return false;
   for(int shift=shiftZona-1;shift>=1;shift--) {
      double c=iClose(SymbolKerja,tf,shift), h=iHigh(SymbolKerja,tf,shift), l=iLow(SymbolKerja,tf,shift);
      if(c<=0 || h<=0 || l<=0) return false;
      if(bullish && c<bawah) return false;
      if(!bullish && c>atas) return false;
      if(h>=bawah && l<=atas) return false;
   }
   return true;
}

//--------------------------------------------------
// MODUL 9: KATEGORI ZONA
//--------------------------------------------------
int BatasEntryKategori(KategoriZona k) {
   if(k==ZONA_SUPER) return MaxSuper;
   if(k==ZONA_BIASA) return MaxBiasa;
   if(k==ZONA_RETEST) return MaxRetest;
   return 0;
}
KategoriZona KlasifikasiZona(bool sweep,bool displacement,bool mss,bool fvg,bool ob) {
   // Dipanggil hanya setelah syarat inti lolos. RETEST tidak boleh menjadi
   // tempat penampungan sinyal yang belum memenuhi konfirmasi.
   int score=0;
   if(sweep) score++;
   if(displacement) score++;
   if(mss) score++;
   if(fvg) score++;
   if(ob) score++;
   if(score>=5) return ZONA_SUPER;
   return ZONA_BIASA;
}

//--------------------------------------------------
// MODUL 10: VALIDASI SINYAL + REGISTRASI
//--------------------------------------------------
bool ValidasiSinyalDasar(bool bullish) {
   bool sweep=bullish ? DeteksiSweepLow(InpEntryTF) : DeteksiSweepHigh(InpEntryTF);
   bool displacement=DeteksiDisplacement(InpEntryTF,bullish);
   bool mss=DeteksiMSS(InpEntryTF,bullish);
   ZonaFVG fvg=DeteksiFVG(InpEntryTF);
   ZonaOB ob=DeteksiOB(InpEntryTF,bullish);
   bool fvgSearah=fvg.valid && fvg.bullish==bullish;
   bool bias=KonfirmasiBiasMTF(bullish);

   // Syarat inti: sweep + MSS + bias MTF + FVG searah.
   // Displacement dan OB menjadi penguat kualitas agar kategori tidak selalu Super.
   if(!sweep || !mss || !fvgSearah || !bias) return false;

   // FVG tiga candle berpusat pada candle shift 2. Pastikan belum tersentuh
   // atau tertutup invalidasi oleh candle tertutup setelah pembentukannya.
   if(!ZonaMasihLayak(InpEntryTF,bullish,fvg.batasBawah,fvg.batasAtas,2)) return false;

   DataZona z;
   z.valid=true; z.bullish=bullish; z.batasBawah=fvg.batasBawah;
   z.batasAtas=fvg.batasAtas; z.ce50=fvg.ce50;
   z.waktu=iTime(SymbolKerja,InpEntryTF,2);
   z.kategori=KlasifikasiZona(sweep,displacement,mss,fvgSearah,ob.valid);
   double point=SymbolInfoDouble(SymbolKerja,SYMBOL_POINT);
   if(z.waktu<=0 || point<=0 || !SimpanZonaRegistry(z,point*2.0)) return false;
   Print("Zona tervalidasi dan diregistrasi. Kategori=",(int)z.kategori,
         " | sweep=",sweep," | displacement=",displacement,
         " | MSS=",mss," | FVG=",fvgSearah," | OB=",ob.valid,
         " | arah=",bullish ? "BUY" : "SELL");
   return true;
}

//--------------------------------------------------
// MODUL 13: TP ZONA SEJENIS (TARGET SAJA, BUKAN ORDER)
//--------------------------------------------------
bool CariTargetZonaSejenis(DataZona &zonaEntry,double hargaSekarang,DataZona &zonaTarget) {
   if(!ZonaRegistryValid(zonaEntry) || hargaSekarang<=0) return false;
   double best=DBL_MAX;
   int bestIndex=-1;
   int batas=MathMin(JumlahZonaRegistry,MAX_ZONA_REGISTRY);
   for(int i=0;i<batas;i++) {
      if(!ZonaRegistryValid(RegistryZona[i])) continue;
      if(RegistryZona[i].kategori!=zonaEntry.kategori) continue;
      if(RegistryZona[i].bullish==zonaEntry.bullish || RegistryZona[i].waktu==zonaEntry.waktu) continue;
      double target=RegistryZona[i].ce50;
      if(target<=0) continue;
      if(zonaEntry.bullish && target<=hargaSekarang) continue;
      if(!zonaEntry.bullish && target>=hargaSekarang) continue;
      double dist=MathAbs(target-hargaSekarang);
      if(dist>0 && dist<best) { best=dist; bestIndex=i; }
   }
   if(bestIndex<0) return false;
   zonaTarget=RegistryZona[bestIndex];
   return true;
}

//--------------------------------------------------
// MODUL 14: RISK GUARDIAN
//--------------------------------------------------
bool RiskGuardianValid() {
   return MaxRiskPerBasketPct>0 && MaxRiskPerBasketPct<=100 &&
          MaxDailyLossPct>0 && MaxDailyLossPct<=100;
}
double HitungBatasKerugianHarian() {
   double balance=AccountInfoDouble(ACCOUNT_BALANCE);
   if(balance<=0) return 0;
   return balance*MaxDailyLossPct/100.0;
}
bool RiskGuardianBolehLanjut() {
   if(!RiskGuardianValid()) return false;
   double limit=HitungBatasKerugianHarian();
   if(limit<=0) return false;
   double floatingLoss=0;
   for(int i=0;i<PositionsTotal();i++) {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=SymbolKerja ||
         (ulong)PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      double p=PositionGetDouble(POSITION_PROFIT)+PositionGetDouble(POSITION_SWAP);
      if(p<0) floatingLoss+=-p;
   }
   if(floatingLoss>=limit) { Print("Risk Guardian: batas floating loss EA tercapai."); return false; }
   return true;
}

//--------------------------------------------------
// MODUL 15: DAILY LOSS GUARD 鈥� hanya transaksi/posisi EA ini
//--------------------------------------------------
datetime AwalHariServer()
{
   datetime now=TimeTradeServer(); if(now<=0) now=TimeCurrent();
   MqlDateTime t; TimeToStruct(now,t); t.hour=0; t.min=0; t.sec=0;
   return StructToTime(t);
}
double HitungProfitRealisasiEASejak(datetime mulai)
{
   datetime now=TimeTradeServer(); if(now<=0) now=TimeCurrent();
   if(mulai<=0 || now<mulai || !HistorySelect(mulai,now)) return EMPTY_VALUE;
   double total=0.0;
   for(int i=0;i<HistoryDealsTotal();i++) {
      ulong ticket=HistoryDealGetTicket(i); if(ticket==0) continue;
      if(HistoryDealGetString(ticket,DEAL_SYMBOL)!=SymbolKerja) continue;
      if((ulong)HistoryDealGetInteger(ticket,DEAL_MAGIC)!=MagicNumber) continue;
      total += HistoryDealGetDouble(ticket,DEAL_PROFIT)
             + HistoryDealGetDouble(ticket,DEAL_SWAP)
             + HistoryDealGetDouble(ticket,DEAL_COMMISSION);
   }
   return total;
}
double HitungFloatingEA()
{
   double total=0.0;
   for(int i=0;i<PositionsTotal();i++) {
      ulong ticket=PositionGetTicket(i); if(ticket==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=SymbolKerja ||
         (ulong)PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      total += PositionGetDouble(POSITION_PROFIT)+PositionGetDouble(POSITION_SWAP);
   }
   return total;
}
bool PerbaruiMetrikHarianEA()
{
   datetime day=AwalHariServer(); if(day<=0 || GVPrefix=="") return false;
   double savedDay=0, savedBase=0, savedPeak=0, savedTriggered=0;
   bool sameDay=BacaGV("day",savedDay) && (datetime)savedDay==day;
   if(!sameDay) {
      // baseline metric dibuat dari saldo saat pertama kali EA aktif hari itu;
      // tidak dapat merekonstruksi posisi yang sudah ditutup sebelum EA pertama kali berjalan.
      MetrikAwalHariEA=AccountInfoDouble(ACCOUNT_BALANCE);
      PuncakMetrikHariEA=MetrikAwalHariEA;
      DailyLossTerpicu=false;
      if(!SimpanGV("day",(double)day) || !SimpanGV("dBase",MetrikAwalHariEA) ||
         !SimpanGV("dPeak",PuncakMetrikHariEA) || !SimpanGV("dTrip",0.0)) return false;
   } else {
      if(!BacaGV("dBase",savedBase) || !BacaGV("dPeak",savedPeak) || !BacaGV("dTrip",savedTriggered)) return false;
      MetrikAwalHariEA=savedBase; PuncakMetrikHariEA=savedPeak; DailyLossTerpicu=(savedTriggered>=1.0);
   }
   double realized=HitungProfitRealisasiEASejak(day);
   if(realized==EMPTY_VALUE) return false;
   double metric=MetrikAwalHariEA+realized+HitungFloatingEA();
   if(!MathIsValidNumber(metric) || metric<=0) return false;
   if(metric>PuncakMetrikHariEA) { PuncakMetrikHariEA=metric; if(!SimpanGV("dPeak",PuncakMetrikHariEA)) return false; }
   double ddPct=(PuncakMetrikHariEA-metric)/PuncakMetrikHariEA*100.0;
   if(ddPct>=MaxDailyLossPct && !DailyLossTerpicu) {
      DailyLossTerpicu=true; SimpanGV("dTrip",1.0);
      Print("Daily Loss Guard: drawdown metrik EA ",DoubleToString(ddPct,2),"% >= ",DoubleToString(MaxDailyLossPct,2),"%. Sinyal dikunci; SAFE MODE tidak menutup posisi.");
   }
   return true;
}
bool BatasRugiHarianTercapai()
{
   if(!PerbaruiMetrikHarianEA()) { Print("Daily Loss Guard: data/status tidak valid; fail-safe blokir sinyal."); return true; }
   return DailyLossTerpicu;
}

//--------------------------------------------------
// MODUL 16: NEWS FILTER MANUAL
//--------------------------------------------------
bool NewsFilterBolehLanjut() {
   if(!AktifkanNewsFilter) return true;
   if(NewsMulai<=0 || NewsSelesai<=0 || NewsSelesai<=NewsMulai) {
      Print("News Filter: jadwal belum diatur atau tidak valid; diblokir demi keamanan.");
      return false;
   }
   datetime now=TimeTradeServer();
   if(now<=0) return false;
   if(now>=NewsMulai && now<=NewsSelesai) {
      Print("News Filter: pemantauan diblokir pada jadwal berita."); return false;
   }
   return true;
}

//--------------------------------------------------
// MODUL 17: GUARD DATA INDIKATOR (di atas)
//--------------------------------------------------

//--------------------------------------------------
// MODUL 18: EXECUTION GUARD (pemeriksaan saja)
//--------------------------------------------------
bool ValidasiEksekusiPasar() {
   if(!ValidasiHargaDanSpread()) return false;
   if(DeviasiMaksimalPoints<0 || !TerminalInfoInteger(TERMINAL_CONNECTED) ||
      !MQLInfoInteger(MQL_TRADE_ALLOWED)) return false;
   return true;
}
bool ValidasiVolumeOrder(double volume) {
   double minLot=SymbolInfoDouble(SymbolKerja,SYMBOL_VOLUME_MIN);
   double maxLot=SymbolInfoDouble(SymbolKerja,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(SymbolKerja,SYMBOL_VOLUME_STEP);
   if(volume<=0 || minLot<=0 || maxLot<minLot || step<=0 || volume<minLot || volume>maxLot)
      return false;
   return MathAbs((volume-minLot)/step-MathRound((volume-minLot)/step))<0.000001;
}

//--------------------------------------------------
// MODUL 19: POSITION GUARD
//--------------------------------------------------
int HitungPosisiEA() {
   int total=0;
   for(int i=0;i<PositionsTotal();i++) {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      if(PositionGetString(POSITION_SYMBOL)==SymbolKerja &&
         (ulong)PositionGetInteger(POSITION_MAGIC)==MagicNumber) total++;
   }
   return total;
}
bool BatasPosisiEAValid() {
   if(MaxPosisiEA<1) return false;
   int n=HitungPosisiEA();
   if(n>=MaxPosisiEA) { Print("Position Guard: batas posisi EA tercapai. Jumlah=",n); return false; }
   return true;
}

//--------------------------------------------------
// MODUL 20: PROFIT LOCK 鈥� khusus P/L EA dan status persisten
//--------------------------------------------------
void PerbaruiProfitLock()
{
   if(!AktifkanProfitLock || GVPrefix=="") return;
   double start=0, peak=0, tripped=0, savedDay=0;
   datetime day=AwalHariServer();
   if(day<=0) return;
   bool sameDay=BacaGV("plDay",savedDay) && (datetime)savedDay==day;
   if(!sameDay) {
      start=0.0; peak=0.0; tripped=0.0;
      if(!SimpanGV("plDay",(double)day) || !SimpanGV("plBase",start) ||
         !SimpanGV("plPeak",peak) || !SimpanGV("plTrip",tripped)) return;
   } else if(!BacaGV("plBase",start) || !BacaGV("plPeak",peak) || !BacaGV("plTrip",tripped)) {
      Print("Profit Lock: state persisten hilang; fail-safe memblokir sinyal.");
      ProfitLockTerpicu=true; return;
   }
   EkuitasAwalProfitLock=start; PuncakEkuitasEA=peak; ProfitLockTerpicu=(tripped>=1.0);
   if(ProfitLockTerpicu) return;
   double realized=HitungProfitRealisasiEASejak(day);
   if(realized==EMPTY_VALUE) return;
   double pnl=realized+HitungFloatingEA();
   if(pnl>PuncakEkuitasEA) { PuncakEkuitasEA=pnl; SimpanGV("plPeak",PuncakEkuitasEA); }
   if(PuncakEkuitasEA>=ProfitLockAktifUSD && (PuncakEkuitasEA-pnl)>=ProfitLockMundurUSD) {
      ProfitLockTerpicu=true; SimpanGV("plTrip",1.0);
      Print("Profit Lock terpicu pada P/L EA. Sinyal dikunci; SAFE MODE tidak menutup posisi.");
   }
}
bool ProfitLockBolehLanjut()
{
   PerbaruiProfitLock();
   return !ProfitLockTerpicu;
}

//--------------------------------------------------
// MODUL 21: SAFETY GATE
//--------------------------------------------------
bool SafetyGateLolos() {
   if(!ValidasiHargaDanSpread()) return false;
   if(!DataCandleTersedia(PERIOD_M1) || !DataCandleTersedia(PERIOD_M5) ||
      !DataCandleTersedia(PERIOD_M15) || !DataCandleTersedia(PERIOD_H1) ||
      !DataCandleTersedia(PERIOD_H4) || !DataCandleTersedia(PERIOD_D1)) return false;
   if(!ValidasiSemuaTimeframe()) return false;
   if(!RiskGuardianBolehLanjut()) return false;
   if(BatasRugiHarianTercapai()) return false;
   if(!NewsFilterBolehLanjut()) return false;
   if(!TerminalInfoInteger(TERMINAL_CONNECTED)) return false;
   if(!BatasPosisiEAValid()) return false;
   if(!ProfitLockBolehLanjut()) return false;
   return true;
}

//--------------------------------------------------
// KONFIRMASI M1
//--------------------------------------------------
bool KonfirmasiM1(bool bullish) {
   if(!DataCandleTersedia(PERIOD_M1)) return false;
   double o=iOpen(SymbolKerja,PERIOD_M1,1), c=iClose(SymbolKerja,PERIOD_M1,1);
   double h=iHigh(SymbolKerja,PERIOD_M1,1), l=iLow(SymbolKerja,PERIOD_M1,1);
   if(o<=0 || c<=0 || h<=l) return false;
   return bullish ? c>o : c<o;
}

//--------------------------------------------------
// ONTICK: SIGNAL_ONLY 鈥� TIDAK ADA PENGIRIMAN ORDER
//--------------------------------------------------
void OnTick() {
   // BUILD INI KHUSUS SIGNAL_ONLY. Tidak ada trade.Buy, trade.Sell, PositionClose atau OrderSend.
   if(!SafetyGateLolos()) return;
   if(!ValidasiATR()) return;
   datetime barTime=iTime(SymbolKerja,InpEntryTF,0);
   if(barTime<=0 || barTime==lastBarTime) return;
   lastBarTime=barTime;

   bool buyValid=ValidasiSinyalDasar(true) && KonfirmasiM1(true);
   bool sellValid=ValidasiSinyalDasar(false) && KonfirmasiM1(false);

   string status=StringFormat("APlus V4.16.2 | SIGNAL_ONLY | BUY=%s | SELL=%s | PosisiEA=%d | Zona Super BUY/SELL=%d/%d | BIAS MTF=%s",
      buyValid ? "VALID" : "-",sellValid ? "VALID" : "-",HitungPosisiEA(),
      HitungZonaAktif(ZONA_SUPER,true),HitungZonaAktif(ZONA_SUPER,false),
      buyValid ? "BULLISH" : (sellValid ? "BEARISH" : "NETRAL/WAIT"));
   Print(status);
   if(AktifkanAlertSinyal && (buyValid || sellValid)) Alert(status);
}