#property strict
#property version   "4.163"
#property description "APlus V4.16.3 MASTER - SIGNAL_ONLY FIXED BUILD"

#include <Trade/Trade.mqh>
CTrade trade;

//==================================================
// EA XAUUSD M5 APLUS V4.16.3 MASTER
// SAFE MODE: SIGNAL_ONLY - TIDAK MENGIRIM ORDER
//==================================================

input string InpSymbol = "XAUUSD";
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
input double MaxRiskPerBasketPct = 0.50;
input double MaxDailyLossPct = 4.0;

input int MaxSuper = 8;
input int MaxBiasa = 5;
input int MaxRetest = 3;
input int MaxRBR = 3;
input int MaxDBD = 3;

input double LotSuperMinimum = 0.08;
input double LotBiasaMinimum = 0.05;
input double LotRetestMinimum = 0.03;
input double LotRBRMinimum = 0.03;
input double LotDBDMinimum = 0.03;

input double TargetProfitHarian = 1000.0;
input int SpreadMaxPoints = 250;
input int ATRPeriod = 14;
input ulong MagicNumber = 416001;

input int SwingLookback = 3;
input int SwingScanBars = 100;

input double DisplacementATRMultiplier = 1.5;
input double MinBodyToRangeRatio = 0.65;
input double MinFVG_ATR = 0.10;

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

input bool AktifkanRBR_DBD = true;
input int BaseMinCandles = 1;
input int BaseMaxCandles = 4;
input double BaseMaxRangeATR = 0.60;

//==================================================
// STATE
//==================================================

string SymbolKerja = "";
string GVPrefix = "";
string RegistryGVPrefix = "";

datetime lastBarTime = 0;
int atrHandle = INVALID_HANDLE;

bool StatePersistenceOK = false;
bool DailyLossTerpicu = false;
bool ProfitLockTerpicu = false;

double MetrikAwalHariEA = 0.0;
double PuncakMetrikHariEA = 0.0;
double PuncakProfitEA = 0.0;

enum KategoriZona
{
   ZONA_SUPER = 0,
   ZONA_BIASA = 1,
   ZONA_RETEST = 2,
   ZONA_RBR = 3,
   ZONA_DBD = 4
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

#define MAX_ZONA_REGISTRY 100

DataZona RegistryZona[MAX_ZONA_REGISTRY];
int JumlahZonaRegistry = 0;

//==================================================
// UTILITAS DATA DAN SIMBOL
//==================================================

bool DataCandleTersedia(ENUM_TIMEFRAMES tf)
{
   int need = MathMax(
      ATRPeriod + 10,
      SwingLookback * 2 + 20
   );

   return (Bars(SymbolKerja, tf) >= need);
}

double AmbilATR(ENUM_TIMEFRAMES tf)
{
   int handle = INVALID_HANDLE;

   if(tf == InpEntryTF && atrHandle != INVALID_HANDLE)
      handle = atrHandle;
   else
      handle = iATR(SymbolKerja, tf, ATRPeriod);

   if(handle == INVALID_HANDLE)
      return 0.0;

   double buffer[];
   ArraySetAsSeries(buffer, true);

   int copied = CopyBuffer(handle, 0, 1, 1, buffer);

   double value = (copied == 1 ? buffer[0] : 0.0);

   if(tf != InpEntryTF)
      IndicatorRelease(handle);

   if(!MathIsValidNumber(value) || value <= 0.0)
      return 0.0;

   return value;
}

bool ValidasiATR()
{
   double atr = AmbilATR(InpEntryTF);

   return (atr > 0.0 && MathIsValidNumber(atr));
}

bool ValidasiHargaDanSpread()
{
   if(SymbolKerja == "")
      return false;

   MqlTick tick;

   if(!SymbolInfoTick(SymbolKerja, tick))
      return false;

   double point = SymbolInfoDouble(
      SymbolKerja,
      SYMBOL_POINT
   );

   if(point <= 0.0 ||
      tick.ask <= 0.0 ||
      tick.bid <= 0.0 ||
      tick.ask < tick.bid)
      return false;

   double spreadPoints = (tick.ask - tick.bid) / point;

   return (
      MathIsValidNumber(spreadPoints) &&
      spreadPoints <= SpreadMaxPoints
   );
}

bool ValidasiSemuaTimeframe()
{
   ENUM_TIMEFRAMES tfs[] =
   {
      PERIOD_M1,
      PERIOD_M5,
      PERIOD_M15,
      PERIOD_H1,
      PERIOD_H4,
      PERIOD_D1
   };

   for(int i = 0; i < ArraySize(tfs); i++)
   {
      if(!DataCandleTersedia(tfs[i]))
         return false;
   }

   return true;
}

bool AkhiranSimbolDiizinkan(string suffix)
{
   if(suffix == "")
      return true;

   string allowed[] =
   {
      "c", "m", ".pro", ".raw",
      ".ecn", ".a", ".i", "_pro", "-pro"
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
   string upper = _Symbol;

   StringToUpper(upper);

   if(StringFind(upper, "XAUUSD") == 0 &&
      AkhiranSimbolDiizinkan(StringSubstr(chart, 6)) &&
      SymbolSelect(chart, true))
      return chart;

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

string BuatGVPrefix()
{
   long login = AccountInfoInteger(ACCOUNT_LOGIN);
   string server = AccountInfoString(ACCOUNT_SERVER);

   StringReplace(server, " ", "");

   string sym = SymbolKerja;

   StringReplace(sym, ".", "");
   StringReplace(sym, "-", "");

   string key = StringFormat(
      "A416%I64d_%s_%s_%I64u",
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
   ResetLastError();

   datetime result = GlobalVariableSet(
      GVPrefix + nama,
      nilai
   );

   if(result == 0)
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

datetime AwalHariServer()
{
   datetime now = TimeTradeServer();

   if(now <= 0)
      now = TimeCurrent();

   MqlDateTime t;

   TimeToStruct(now, t);

   t.hour = 0;
   t.min = 0;
   t.sec = 0;

   return StructToTime(t);
}

//==================================================
// REGISTRY ZONA DAN VISUAL
//==================================================

bool ZonaRegistryValid(DataZona &z)
{
   if(!z.valid ||
      !MathIsValidNumber(z.batasBawah) ||
      !MathIsValidNumber(z.batasAtas) ||
      !MathIsValidNumber(z.ce50) ||
      z.batasBawah <= 0.0 ||
      z.batasAtas <= z.batasBawah ||
      z.ce50 < z.batasBawah ||
      z.ce50 > z.batasAtas ||
      z.waktu <= 0)
      return false;

   if(z.kategori < ZONA_SUPER ||
      z.kategori > ZONA_DBD)
      return false;

   return true;
}

string NamaObjekZona(DataZona &z)
{
   string arah = z.bullish ? "BUY" : "SELL";

   return StringFormat(
      "A416_%I64u_%s_%d_%I64d",
      MagicNumber,
      arah,
      (int)z.kategori,
      (long)z.waktu
   );
}

void GambarZona(DataZona &z)
{
   if(!TampilkanZonaChart || !ZonaRegistryValid(z))
      return;

   string name = NamaObjekZona(z);

   int sec = PeriodSeconds(InpEntryTF);

   if(sec <= 0)
      sec = 300;

   datetime t2 = TimeCurrent() + sec * ZonaExtendBars;

   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(
         0, name, OBJ_RECTANGLE, 0,
         z.waktu, z.batasAtas,
         t2, z.batasBawah
      );
   }
   else
   {
      ObjectMove(0, name, 0, z.waktu, z.batasAtas);
      ObjectMove(0, name, 1, t2, z.batasBawah);
   }

   color clr = z.bullish ? clrDarkSeaGreen : clrLightCoral;

   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_DOT);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
   ObjectSetInteger(0, name, OBJPROP_FILL, true);
   ObjectSetInteger(0, name, OBJPROP_BACK, true);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);

   string cat = "SUPER";

   if(z.kategori == ZONA_BIASA) cat = "BIASA";
   if(z.kategori == ZONA_RETEST) cat = "RETEST";
   if(z.kategori == ZONA_RBR) cat = "RBR";
   if(z.kategori == ZONA_DBD) cat = "DBD";

   string label = name + "_TXT";

   string txt = cat +
      (z.bullish ? " BUY" : " SELL") +
      " | CE50 " +
      DoubleToString(
         z.ce50,
         (int)SymbolInfoInteger(SymbolKerja, SYMBOL_DIGITS)
      );

   if(ObjectFind(0, label) < 0)
      ObjectCreate(0, label, OBJ_TEXT, 0, t2, z.ce50);
   else
      ObjectMove(0, label, 0, t2, z.ce50);

   ObjectSetString(0, label, OBJPROP_TEXT, txt);
   ObjectSetInteger(0, label, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, label, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, label, OBJPROP_SELECTABLE, false);
}

int CariZonaRegistry(DataZona &z, double tol)
{
   if(!MathIsValidNumber(tol) ||
      tol < 0 ||
      !ZonaRegistryValid(z))
      return -1;

   for(int i = 0; i < JumlahZonaRegistry; i++)
   {
      if(!RegistryZona[i].valid)
         continue;

      if(RegistryZona[i].bullish != z.bullish ||
         RegistryZona[i].kategori != z.kategori ||
         RegistryZona[i].waktu != z.waktu)
         continue;

      if(MathAbs(
         RegistryZona[i].batasBawah - z.batasBawah
      ) > tol)
         continue;

      if(MathAbs(
         RegistryZona[i].batasAtas - z.batasAtas
      ) > tol)
         continue;

      return i;
   }

   return -1;
}

int CariSlotKosongRegistry()
{
   for(int i = 0; i < JumlahZonaRegistry; i++)
   {
      if(!RegistryZona[i].valid)
         return i;
   }

   if(JumlahZonaRegistry < MAX_ZONA_REGISTRY)
      return JumlahZonaRegistry;

   return -1;
}

bool SimpanSatuZonaRegistry(int idx)
{
   if(RegistryGVPrefix == "" ||
      idx < 0 ||
      idx >= MAX_ZONA_REGISTRY)
      return false;

   string k = IntegerToString(idx) + "_";

   DataZona z = RegistryZona[idx];

   bool ok = true;

   if(GlobalVariableSet(
      RegistryGVPrefix + k + "v",
      z.valid ? 1.0 : 0.0) == 0)
      ok = false;

   if(GlobalVariableSet(
      RegistryGVPrefix + k + "b",
      z.bullish ? 1.0 : 0.0) == 0)
      ok = false;

   if(GlobalVariableSet(
      RegistryGVPrefix + k + "k",
      (double)z.kategori) == 0)
      ok = false;

   if(GlobalVariableSet(
      RegistryGVPrefix + k + "lo",
      z.batasBawah) == 0)
      ok = false;

   if(GlobalVariableSet(
      RegistryGVPrefix + k + "hi",
      z.batasAtas) == 0)
      ok = false;

   if(GlobalVariableSet(
      RegistryGVPrefix + k + "ce",
      z.ce50) == 0)
      ok = false;

   if(GlobalVariableSet(
      RegistryGVPrefix + k + "tm",
      (double)z.waktu) == 0)
      ok = false;

   return ok;
}

bool SimpanSemuaZonaRegistry()
{
   if(RegistryGVPrefix == "" ||
      JumlahZonaRegistry < 0 ||
      JumlahZonaRegistry > MAX_ZONA_REGISTRY)
      return false;

   bool ok = true;

   for(int i = 0; i < JumlahZonaRegistry; i++)
   {
      if(!SimpanSatuZonaRegistry(i))
         ok = false;
   }

   if(GlobalVariableSet(
      RegistryGVPrefix + "count",
      (double)JumlahZonaRegistry) == 0)
      ok = false;

   GlobalVariablesFlush();

   return ok;
}

bool SimpanZonaRegistry(DataZona &z, double tol)
{
   if(!ZonaRegistryValid(z) ||
      !MathIsValidNumber(tol) ||
      tol < 0)
      return false;

   int idx = CariZonaRegistry(z, tol);

   if(idx < 0)
      idx = CariSlotKosongRegistry();

   if(idx < 0 || idx >= MAX_ZONA_REGISTRY)
      return false;

   int oldCount = JumlahZonaRegistry;
   bool isNew = (idx == oldCount);

   DataZona old;

   if(!isNew)
      old = RegistryZona[idx];

   RegistryZona[idx] = z;

   if(isNew)
      JumlahZonaRegistry++;

   if(!SimpanSemuaZonaRegistry())
   {
      if(isNew)
         JumlahZonaRegistry = oldCount;
      else
         RegistryZona[idx] = old;

      Print("Registry save gagal; perubahan dibatalkan.");

      return false;
   }

   GambarZona(z);

   return true;
}

bool PulihkanZonaRegistry()
{
   if(RegistryGVPrefix == "")
      return false;

   JumlahZonaRegistry = 0;

   for(int i = 0; i < MAX_ZONA_REGISTRY; i++)
   {
      RegistryZona[i].valid = false;
      RegistryZona[i].bullish = false;
      RegistryZona[i].kategori = ZONA_SUPER;
      RegistryZona[i].batasBawah = 0;
      RegistryZona[i].batasAtas = 0;
      RegistryZona[i].ce50 = 0;
      RegistryZona[i].waktu = 0;
   }

   if(!GlobalVariableCheck(RegistryGVPrefix + "count"))
   {
      if(GlobalVariableSet(
         RegistryGVPrefix + "count",
         0.0) == 0)
         return false;

      GlobalVariablesFlush();

      return true;
   }

   double cv = 0;

   if(!GlobalVariableGet(RegistryGVPrefix + "count", cv) ||
      !MathIsValidNumber(cv) ||
      cv < 0 ||
      cv > MAX_ZONA_REGISTRY)
      return false;

   int count = (int)cv;

   for(int i = 0; i < count; i++)
   {
      string k = IntegerToString(i) + "_";

      double v, b, cat, lo, hi, ce, tm;

      if(!GlobalVariableGet(RegistryGVPrefix + k + "v", v) ||
         !GlobalVariableGet(RegistryGVPrefix + k + "b", b) ||
         !GlobalVariableGet(RegistryGVPrefix + k + "k", cat) ||
         !GlobalVariableGet(RegistryGVPrefix + k + "lo", lo) ||
         !GlobalVariableGet(RegistryGVPrefix + k + "hi", hi) ||
         !GlobalVariableGet(RegistryGVPrefix + k + "ce", ce) ||
         !GlobalVariableGet(RegistryGVPrefix + k + "tm", tm))
         return false;

      if(v < 0.5)
         continue;

      if(cat < ZONA_SUPER || cat > ZONA_DBD)
         return false;

      DataZona z;

      z.valid = true;
      z.bullish = (b >= 0.5);
      z.kategori = (KategoriZona)(int)cat;
      z.batasBawah = lo;
      z.batasAtas = hi;
      z.ce50 = ce;
      z.waktu = (datetime)tm;

      if(!ZonaRegistryValid(z))
         return false;

      RegistryZona[i] = z;

      if(i >= JumlahZonaRegistry)
         JumlahZonaRegistry = i + 1;

      GambarZona(RegistryZona[i]);
   }

   Print(
      "Registry dipulihkan. Slot terpakai=",
      JumlahZonaRegistry
   );

   return true;
}

bool NonaktifkanZonaRegistry(int idx)
{
   if(idx < 0 || idx >= JumlahZonaRegistry)
      return false;

   bool old = RegistryZona[idx].valid;

   RegistryZona[idx].valid = false;

   if(!SimpanSemuaZonaRegistry())
   {
      RegistryZona[idx].valid = old;
      return false;
   }

   return true;
}

int HitungZonaAktif(KategoriZona cat, bool bullish)
{
   int n = 0;

   for(int i = 0; i < JumlahZonaRegistry; i++)
   {
      if(RegistryZona[i].valid &&
         RegistryZona[i].kategori == cat &&
         RegistryZona[i].bullish == bullish)
         n++;
   }

   return n;
}

//==================================================
// MODUL 1: SWING
//==================================================

bool DeteksiSwingHigh(ENUM_TIMEFRAMES tf, int shift)
{
   int total = Bars(SymbolKerja, tf);

   if(SwingLookback < 1 ||
      shift <= SwingLookback ||
      shift + SwingLookback >= total)
      return false;

   double v = iHigh(SymbolKerja, tf, shift);

   if(v <= 0)
      return false;

   for(int i = 1; i <= SwingLookback; i++)
   {
      if(iHigh(SymbolKerja, tf, shift - i) >= v ||
         iHigh(SymbolKerja, tf, shift + i) > v)
         return false;
   }

   return true;
}

bool DeteksiSwingLow(ENUM_TIMEFRAMES tf, int shift)
{
   int total = Bars(SymbolKerja, tf);

   if(SwingLookback < 1 ||
      shift <= SwingLookback ||
      shift + SwingLookback >= total)
      return false;

   double v = iLow(SymbolKerja, tf, shift);

   if(v <= 0)
      return false;

   for(int i = 1; i <= SwingLookback; i++)
   {
      if(iLow(SymbolKerja, tf, shift - i) <= v ||
         iLow(SymbolKerja, tf, shift + i) < v)
         return false;
   }

   return true;
}

double AmbilSwingTerakhir(ENUM_TIMEFRAMES tf, bool cariHigh)
{
   int total = Bars(SymbolKerja, tf);

   if(total <= SwingLookback * 2 + 2)
      return 0;

   int batas = (int)MathMin(
      SwingScanBars,
      total - SwingLookback - 1
   );

   for(int shift = SwingLookback + 1; shift < batas; shift++)
   {
      if(cariHigh && DeteksiSwingHigh(tf, shift))
         return iHigh(SymbolKerja, tf, shift);

      if(!cariHigh && DeteksiSwingLow(tf, shift))
         return iLow(SymbolKerja, tf, shift);
   }

   return 0;
}