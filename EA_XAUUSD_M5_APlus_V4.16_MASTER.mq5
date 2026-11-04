#property strict
#property version   "4.162"
#property description "APlus V4.16.2 MASTER - SIGNAL_ONLY monitoring build"

#include <Trade/Trade.mqh>
CTrade trade;

//==================================================
// EA XAUUSD M5 APLUS V4.16.2 MASTER
// SAFE MODE: SIGNAL_ONLY - TIDAK MENGIRIM ORDER
//==================================================

input string InpSymbol = "XAUUSD";
input ENUM_TIMEFRAMES InpEntryTF = PERIOD_M5;
enum ModeOperasiEA { SIGNAL_ONLY = 0, AUTO_TRADE = 1 };
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

input double TargetProfitHarian = 1000.0; // unit nominal mata uang akun; hanya milestone
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
   int need = MathMax(ATRPeriod + 10, SwingLookback * 2 + 20);
   return (Bars(SymbolKerja, tf) >= need);
}

double AmbilATR(ENUM_TIMEFRAMES tf)
{
   int handle = INVALID_HANDLE;
   if(tf == InpEntryTF && atrHandle != INVALID_HANDLE)
      handle = atrHandle;
   else
      handle = iATR(SymbolKerja, tf, ATRPeriod);

   if(handle == INVALID_HANDLE) return 0.0;

   double buffer[];
   ArraySetAsSeries(buffer, true);
   int copied = CopyBuffer(handle, 0, 1, 1, buffer);
   double value = (copied == 1 ? buffer[0] : 0.0);

   if(tf != InpEntryTF) IndicatorRelease(handle);
   if(!MathIsValidNumber(value) || value <= 0.0) return 0.0;
   return value;
}

bool ValidasiATR()
{
   double atr = AmbilATR(InpEntryTF);
   return (atr > 0.0 && MathIsValidNumber(atr));
}

bool ValidasiHargaDanSpread()
{
   if(SymbolKerja == "") return false;
   MqlTick tick;
   if(!SymbolInfoTick(SymbolKerja, tick)) return false;
   double point = SymbolInfoDouble(SymbolKerja, SYMBOL_POINT);
   if(point <= 0.0 || tick.ask <= 0.0 || tick.bid <= 0.0 || tick.ask < tick.bid)
      return false;
   double spreadPoints = (tick.ask - tick.bid) / point;
   return (MathIsValidNumber(spreadPoints) && spreadPoints <= SpreadMaxPoints);
}

bool ValidasiSemuaTimeframe()
{
   ENUM_TIMEFRAMES tfs[] =
   {
      PERIOD_M1, PERIOD_M5, PERIOD_M15,
      PERIOD_H1, PERIOD_H4, PERIOD_D1
   };
   for(int i=0; i<ArraySize(tfs); i++)
      if(!DataCandleTersedia(tfs[i])) return false;
   return true;
}

bool AkhiranSimbolDiizinkan(string suffix)
{
   if(suffix == "") return true;
   string allowed[] = {"c","m",".pro",".raw",".ecn",".a",".i","_pro","-pro"};
   string low = suffix;
   StringToLower(low);
   for(int i=0; i<ArraySize(allowed); i++)
      if(low == allowed[i]) return true;
   return false;
}

string CariSimbolKerja()
{
   string base = InpSymbol;
   StringToUpper(base);
   if(base != "XAUUSD") return "";

   string chart = _Symbol, upper = _Symbol;
   StringToUpper(upper);
   if(StringFind(upper, "XAUUSD") == 0 &&
      AkhiranSimbolDiizinkan(StringSubstr(chart, 6)) &&
      SymbolSelect(chart, true))
      return chart;

   if(SymbolSelect(InpSymbol, true)) return InpSymbol;

   int total = SymbolsTotal(false);
   for(int i=0; i<total; i++)
   {
      string candidate = SymbolName(i, false);
      string u = candidate;
      StringToUpper(u);
      if(StringFind(u, "XAUUSD") != 0) continue;
      if(!AkhiranSimbolDiizinkan(StringSubstr(candidate, 6))) continue;
      if(SymbolSelect(candidate, true)) return candidate;
   }
   return "";
}

string BuatGVPrefix()
{
   long login = AccountInfoInteger(ACCOUNT_LOGIN);
   string server = AccountInfoString(ACCOUNT_SERVER);
   StringReplace(server, " ", "_");
   string sym = SymbolKerja;
   StringReplace(sym, ".", "_");
   StringReplace(sym, "-", "_");
   string key = StringFormat("A416_%I64d_%s_%s_%I64u",
                             login, server, sym, MagicNumber);
   if(StringLen(key) > 60) key = StringSubstr(key, 0, 60);
   return key;
}

bool SimpanGV(string nama, double nilai)
{
   ResetLastError();
   datetime result = GlobalVariableSet(GVPrefix + nama, nilai);
   if(result == 0)
   {
      Print("State save gagal: ", nama, " err=", GetLastError());
      return false;
   }
   GlobalVariablesFlush();
   return true;
}

bool BacaGV(string nama, double &nilai)
{
   if(!GlobalVariableCheck(GVPrefix + nama)) return false;
   return GlobalVariableGet(GVPrefix + nama, nilai);
}

datetime AwalHariServer()
{
   datetime now = TimeTradeServer();
   if(now <= 0) now = TimeCurrent();
   MqlDateTime t;
   TimeToStruct(now, t);
   t.hour=0; t.min=0; t.sec=0;
   return StructToTime(t);
}

//==================================================
// REGISTRY ZONA DAN VISUAL
//==================================================
bool ZonaRegistryValid(DataZona &z)
{
   if(!z.valid || !MathIsValidNumber(z.batasBawah) ||
      !MathIsValidNumber(z.batasAtas) || !MathIsValidNumber(z.ce50) ||
      z.batasBawah <= 0.0 || z.batasAtas <= z.batasBawah ||
      z.ce50 < z.batasBawah || z.ce50 > z.batasAtas || z.waktu <= 0)
      return false;
   if(z.kategori < ZONA_SUPER || z.kategori > ZONA_DBD) return false;
   return true;
}

string NamaObjekZona(DataZona &z)
{
   string arah = z.bullish ? "BUY" : "SELL";
   return StringFormat("A416_%I64u_%s_%d_%I64d",
                       MagicNumber, arah, (int)z.kategori, (long)z.waktu);
}

void GambarZona(DataZona &z)
{
   if(!TampilkanZonaChart || !ZonaRegistryValid(z)) return;
   string name = NamaObjekZona(z);
   int sec = PeriodSeconds(InpEntryTF);
   if(sec <= 0) sec = 300;
   datetime t2 = TimeCurrent() + sec * 30;
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_RECTANGLE, 0, z.waktu, z.batasAtas, t2, z.batasBawah);
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
   if(z.kategori == ZONA_BIASA) cat="BIASA";
   if(z.kategori == ZONA_RETEST) cat="RETEST";
   if(z.kategori == ZONA_RBR) cat="RBR";
   if(z.kategori == ZONA_DBD) cat="DBD";
   string label = name + "_TXT";
   string txt = cat + (z.bullish ? " BUY" : " SELL") +
                " | CE50 " + DoubleToString(z.ce50, (int)SymbolInfoInteger(SymbolKerja,SYMBOL_DIGITS));
   if(ObjectFind(0,label)<0) ObjectCreate(0,label,OBJ_TEXT,0,t2,z.ce50);
   else ObjectMove(0,label,0,t2,z.ce50);
   ObjectSetString(0,label,OBJPROP_TEXT,txt);
   ObjectSetInteger(0,label,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,label,OBJPROP_FONTSIZE,8);
   ObjectSetInteger(0,label,OBJPROP_SELECTABLE,false);
}

int CariZonaRegistry(DataZona &z, double tol)
{
   if(!MathIsValidNumber(tol) || tol < 0 || !ZonaRegistryValid(z)) return -1;
   for(int i=0; i<JumlahZonaRegistry; i++)
   {
      if(!RegistryZona[i].valid) continue;
      if(RegistryZona[i].bullish != z.bullish ||
         RegistryZona[i].kategori != z.kategori ||
         RegistryZona[i].waktu != z.waktu) continue;
      if(MathAbs(RegistryZona[i].batasBawah-z.batasBawah)>tol) continue;
      if(MathAbs(RegistryZona[i].batasAtas-z.batasAtas)>tol) continue;
      return i;
   }
   return -1;
}

int CariSlotKosongRegistry()
{
   for(int i=0; i<JumlahZonaRegistry; i++)
      if(!RegistryZona[i].valid) return i;
   if(JumlahZonaRegistry < MAX_ZONA_REGISTRY) return JumlahZonaRegistry;
   return -1;
}

bool SimpanSatuZonaRegistry(int idx)
{
   if(RegistryGVPrefix=="" || idx<0 || idx>=MAX_ZONA_REGISTRY) return false;
   string k=IntegerToString(idx)+"_";
   DataZona z=RegistryZona[idx];
   bool ok=true;
   if(GlobalVariableSet(RegistryGVPrefix+k+"v",z.valid?1.0:0.0)==0) ok=false;
   if(GlobalVariableSet(RegistryGVPrefix+k+"b",z.bullish?1.0:0.0)==0) ok=false;
   if(GlobalVariableSet(RegistryGVPrefix+k+"k",(double)z.kategori)==0) ok=false;
   if(GlobalVariableSet(RegistryGVPrefix+k+"lo",z.batasBawah)==0) ok=false;
   if(GlobalVariableSet(RegistryGVPrefix+k+"hi",z.batasAtas)==0) ok=false;
   if(GlobalVariableSet(RegistryGVPrefix+k+"ce",z.ce50)==0) ok=false;
   if(GlobalVariableSet(RegistryGVPrefix+k+"tm",(double)z.waktu)==0) ok=false;
   return ok;
}

bool SimpanSemuaZonaRegistry()
{
   if(RegistryGVPrefix=="" || JumlahZonaRegistry<0 ||
      JumlahZonaRegistry>MAX_ZONA_REGISTRY) return false;
   bool ok=true;
   for(int i=0; i<JumlahZonaRegistry; i++)
      if(!SimpanSatuZonaRegistry(i)) ok=false;
   if(GlobalVariableSet(RegistryGVPrefix+"count",(double)JumlahZonaRegistry)==0) ok=false;
   GlobalVariablesFlush();
   return ok;
}

bool SimpanZonaRegistry(DataZona &z, double tol)
{
   if(!ZonaRegistryValid(z) || !MathIsValidNumber(tol) || tol<0)
   return false;

int idx=CariZonaRegistry(z,tol);

if(idx<0)
   idx=CariSlotKosongRegistry();

if(idx<0 || idx>=MAX_ZONA_REGISTRY)
   return false;

int oldCount=JumlahZonaRegistry;
bool isNew=(idx==oldCount);

DataZona old;

if(!isNew)
   old=RegistryZona[idx];

RegistryZona[idx]=z;

if(isNew)
   JumlahZonaRegistry++;

if(!SimpanSemuaZonaRegistry())
{
   if(isNew)
   {
      JumlahZonaRegistry=oldCount;
   }
   else
   {
      RegistryZona[idx]=old;
   }

   Print("Registry save gagal; perubahan dibatalkan.");
   return false;
}

GambarZona(z);
return true;
}
   GambarZona(z);
   return true;
}

bool PulihkanZonaRegistry()
{
   if(RegistryGVPrefix=="") return false;
   JumlahZonaRegistry=0;
   for(int i=0;i<MAX_ZONA_REGISTRY;i++)
   {
      RegistryZona[i].valid=false;
      RegistryZona[i].bullish=false;
      RegistryZona[i].kategori=ZONA_SUPER;
      RegistryZona[i].batasBawah=0;
      RegistryZona[i].batasAtas=0;
      RegistryZona[i].ce50=0;
      RegistryZona[i].waktu=0;
   }
   if(!GlobalVariableCheck(RegistryGVPrefix+"count"))
   {
      if(GlobalVariableSet(RegistryGVPrefix+"count",0.0)==0) return false;
      GlobalVariablesFlush();
      return true;
   }
   double cv=0;
   if(!GlobalVariableGet(RegistryGVPrefix+"count",cv) ||
      !MathIsValidNumber(cv) || cv<0 || cv>MAX_ZONA_REGISTRY) return false;
   int count=(int)cv;
   for(int i=0;i<count;i++)
   {
      string k=IntegerToString(i)+"_";
      double v,b,cat,lo,hi,ce,tm;
      if(!GlobalVariableGet(RegistryGVPrefix+k+"v",v) ||
         !GlobalVariableGet(RegistryGVPrefix+k+"b",b) ||
         !GlobalVariableGet(RegistryGVPrefix+k+"k",cat) ||
         !GlobalVariableGet(RegistryGVPrefix+k+"lo",lo) ||
         !GlobalVariableGet(RegistryGVPrefix+k+"hi",hi) ||
         !GlobalVariableGet(RegistryGVPrefix+k+"ce",ce) ||
         !GlobalVariableGet(RegistryGVPrefix+k+"tm",tm)) return false;
      if(v<0.5) continue;
      if(cat<ZONA_SUPER || cat>ZONA_DBD) return false;
      DataZona z;
      z.valid=true; z.bullish=(b>=0.5); z.kategori=(KategoriZona)(int)cat;
      z.batasBawah=lo; z.batasAtas=hi; z.ce50=ce; z.waktu=(datetime)tm;
      if(!ZonaRegistryValid(z)) return false;
      RegistryZona[i]=z;
      if(i>=JumlahZonaRegistry) JumlahZonaRegistry=i+1;
      GambarZona(RegistryZona[i]);
   }
   Print("Registry dipulihkan. Slot terpakai=",JumlahZonaRegistry);
   return true;
}

bool NonaktifkanZonaRegistry(int idx)
{
   if(idx<0 || idx>=JumlahZonaRegistry) return false;
   bool old=RegistryZona[idx].valid;
   RegistryZona[idx].valid=false;
   if(!SimpanSemuaZonaRegistry())
   {
      RegistryZona[idx].valid=old;
      return false;
   }
   return true;
}

int HitungZonaAktif(KategoriZona cat,bool bullish)
{
   int n=0;
   for(int i=0;i<JumlahZonaRegistry;i++)
      if(RegistryZona[i].valid && RegistryZona[i].kategori==cat &&
         RegistryZona[i].bullish==bullish) n++;
   return n;
}

//==================================================
// MODUL 1: SWING
//==================================================
bool DeteksiSwingHigh(ENUM_TIMEFRAMES tf,int shift)
{
   int total=Bars(SymbolKerja,tf);
   if(SwingLookback<1 || shift<=SwingLookback || shift+SwingLookback>=total) return false;
   double v=iHigh(SymbolKerja,tf,shift);
   if(v<=0) return false;
   for(int i=1;i<=SwingLookback;i++)
      if(iHigh(SymbolKerja,tf,shift-i)>=v || iHigh(SymbolKerja,tf,shift+i)>v) return false;
   return true;
}
bool DeteksiSwingLow(ENUM_TIMEFRAMES tf,int shift)
{
   int total=Bars(SymbolKerja,tf);
   if(SwingLookback<1 || shift<=SwingLookback || shift+SwingLookback>=total) return false;
   double v=iLow(SymbolKerja,tf,shift);
   if(v<=0) return false;
   for(int i=1;i<=SwingLookback;i++)
      if(iLow(SymbolKerja,tf,shift-i)<=v || iLow(SymbolKerja,tf,shift+i)<v) return false;
   return true;
}
double AmbilSwingTerakhir(ENUM_TIMEFRAMES tf,bool cariHigh)
{
   int total=Bars(SymbolKerja,tf);
   if(total<=SwingLookback*2+2) return 0;
   int batas=(int)MathMin(SwingScanBars,total-SwingLookback-1);
   for(int shift=SwingLookback+1;shift<batas;shift++)
   {
      if(cariHigh && DeteksiSwingHigh(tf,shift)) return iHigh(SymbolKerja,tf,shift);
      if(!cariHigh && DeteksiSwingLow(tf,shift)) return iLow(SymbolKerja,tf,shift);
   }
   return 0;
}

//==================================================
// MODUL 2-8: SWEEP, DISPLACEMENT, MSS, FVG, OB, MTF
//==================================================
bool DeteksiSweepHigh(ENUM_TIMEFRAMES tf)
{
   double s=AmbilSwingTerakhir(tf,true);
   return (s>0 && iHigh(SymbolKerja,tf,1)>s && iClose(SymbolKerja,tf,1)<s);
}
bool DeteksiSweepLow(ENUM_TIMEFRAMES tf)
{
   double s=AmbilSwingTerakhir(tf,false);
   return (s>0 && iLow(SymbolKerja,tf,1)<s && iClose(SymbolKerja,tf,1)>s);
}
bool DeteksiDisplacement(ENUM_TIMEFRAMES tf,bool bullish)
{
   double atr=AmbilATR(tf);
   if(atr<=0) return false;
   double o=iOpen(SymbolKerja,tf,1),c=iClose(SymbolKerja,tf,1);
   double h=iHigh(SymbolKerja,tf,1),l=iLow(SymbolKerja,tf,1);
   double range=h-l,body=MathAbs(c-o);
   if(range<=0 || body<atr*DisplacementATRMultiplier ||
      body/range<MinBodyToRangeRatio) return false;
   return bullish ? c>o : c<o;
}
bool DeteksiMSS(ENUM_TIMEFRAMES tf,bool bullish)
{
   double c=iClose(SymbolKerja,tf,1);
   if(c<=0) return false;
   double s=AmbilSwingTerakhir(tf,!bullish);
   return (s>0 && (bullish ? c>s : c<s));
}
ZonaFVG DeteksiFVG(ENUM_TIMEFRAMES tf)
{
   ZonaFVG z; z.valid=false; z.bullish=false;
   z.batasBawah=0; z.batasAtas=0; z.ce50=0;
   if(Bars(SymbolKerja,tf)<10) return z;
   double h3=iHigh(SymbolKerja,tf,3),l3=iLow(SymbolKerja,tf,3);
   double h1=iHigh(SymbolKerja,tf,1),l1=iLow(SymbolKerja,tf,1);
   if(h3<=0 || l3<=0 || h1<=0 || l1<=0) return z;
   if(l1>h3) { z.batasBawah=h3; z.batasAtas=l1; z.bullish=true; z.valid=true; }
   else if(h1<l3) { z.batasBawah=h1; z.batasAtas=l3; z.bullish=false; z.valid=true; }
   if(z.valid)
   {
      double atr=AmbilATR(tf);
      if(atr<=0 || z.batasAtas-z.batasBawah<atr*MinFVG_ATR) z.valid=false;
      else z.ce50=(z.batasBawah+z.batasAtas)/2.0;
   }
   return z;
}
ZonaOB DeteksiOB(ENUM_TIMEFRAMES tf,bool bullish)
{
   ZonaOB z; z.valid=false; z.bullish=bullish;
   z.batasBawah=0; z.batasAtas=0; z.waktu=0;
   int total=Bars(SymbolKerja,tf);
   if(total<20) return z;
   for(int shift=2;shift<=10 && shift<total;shift++)
   {
      double o=iOpen(SymbolKerja,tf,shift),c=iClose(SymbolKerja,tf,shift);
      double h=iHigh(SymbolKerja,tf,shift),l=iLow(SymbolKerja,tf,shift);
      if(h<=l || o<=0 || c<=0) continue;
      bool opposite=bullish ? c<o : c>o;
      if(opposite)
      {
         z.valid=true; z.batasBawah=l; z.batasAtas=h;
         z.waktu=iTime(SymbolKerja,tf,shift); return z;
      }
   }
   return z;
}
bool BiasBullish(ENUM_TIMEFRAMES tf)
{
   double a=iClose(SymbolKerja,tf,1),b=iClose(SymbolKerja,tf,2);
   return (a>0 && b>0 && a>b);
}
bool BiasBearish(ENUM_TIMEFRAMES tf)
{
   double a=iClose(SymbolKerja,tf,1),b=iClose(SymbolKerja,tf,2);
   return (a>0 && b>0 && a<b);
}
bool KonfirmasiBiasMTF(bool bullish)
{
   if(!DataCandleTersedia(PERIOD_H1) || !DataCandleTersedia(PERIOD_M15)) return false;
   return bullish ? (BiasBullish(PERIOD_H1)&&BiasBullish(PERIOD_M15))
                  : (BiasBearish(PERIOD_H1)&&BiasBearish(PERIOD_M15));
}

// Validasi FVG: hanya candle setelah FVG terbentuk yang diperiksa.
// Shift 1 adalah candle terakhir tertutup; shift 2 adalah candle tengah FVG.
bool ZonaMasihLayak(ENUM_TIMEFRAMES tf,bool bullish,double bawah,double atas,int shiftZona)
{
   if(bawah<=0 || atas<=bawah || shiftZona<1) return false;
   int total=Bars(SymbolKerja,tf);
   if(total<=shiftZona+1) return false;
   for(int shift=shiftZona-1;shift>=1;shift--)
   {
      double c=iClose(SymbolKerja,tf,shift),h=iHigh(SymbolKerja,tf,shift),l=iLow(SymbolKerja,tf,shift);
      if(c<=0 || h<=0 || l<=0) return false;
      if(bullish && c<bawah) return false;
      if(!bullish && c>atas) return false;
      // Mitigasi penuh/penetrasi ke zona membuat FVG tidak lagi fresh.
      if(bullish && l<=atas) return false;
      if(!bullish && h>=bawah) return false;
   }
   return true;
}

//==================================================
// MODUL 9-10: KATEGORI DAN VALIDASI SINYAL
//==================================================
int BatasEntryKategori(KategoriZona k)
{
   if(k==ZONA_SUPER) return MaxSuper;
   if(k==ZONA_BIASA) return MaxBiasa;
   if(k==ZONA_RETEST) return MaxRetest;
   if(k==ZONA_RBR) return MaxRBR;
   if(k==ZONA_DBD) return MaxDBD;
   return 0;
}
KategoriZona KlasifikasiZona(bool sweep,bool displacement,bool mss,bool fvg,bool ob)
{
   int score=(int)sweep+(int)displacement+(int)mss+(int)fvg+(int)ob;
   return (score>=5 ? ZONA_SUPER : ZONA_BIASA);
}
bool ValidasiSinyalDasar(bool bullish)
{
   bool sweep=bullish ? DeteksiSweepLow(InpEntryTF) : DeteksiSweepHigh(InpEntryTF);
   bool displacement=DeteksiDisplacement(InpEntryTF,bullish);
   bool mss=DeteksiMSS(InpEntryTF,bullish);
   ZonaFVG fvg=DeteksiFVG(InpEntryTF);
   ZonaOB ob=DeteksiOB(InpEntryTF,bullish);
   bool fvgSearah=(fvg.valid && fvg.bullish==bullish);
   bool bias=KonfirmasiBiasMTF(bullish);
   if(!sweep || !mss || !fvgSearah || !bias) return false;
   if(!ZonaMasihLayak(InpEntryTF,bullish,fvg.batasBawah,fvg.batasAtas,2)) return false;

   DataZona z;
   z.valid=true; z.bullish=bullish; z.batasBawah=fvg.batasBawah;
   z.batasAtas=fvg.batasAtas; z.ce50=fvg.ce50;
   z.waktu=iTime(SymbolKerja,InpEntryTF,2);
   z.kategori=KlasifikasiZona(sweep,displacement,mss,fvgSearah,ob.valid);
   double point=SymbolInfoDouble(SymbolKerja,SYMBOL_POINT);
   if(z.waktu<=0 || point<=0 || !SimpanZonaRegistry(z,point*2.0)) return false;
   Print("Zona valid: ",(bullish?"BUY":"SELL")," kategori=",(int)z.kategori,
         " sweep=",sweep," displacement=",displacement," MSS=",mss,
         " FVG=",fvgSearah," OB=",ob.valid);
   return true;
}

//==================================================
// MODUL 11-12: RBR / DBD BASE PATTERN (deteksi dasar)
//==================================================
bool DeteksiRBR_DBD(ENUM_TIMEFRAMES tf,bool bullish,DataZona &z)
{
   z.valid=false;
   if(!AktifkanRBR_DBD || BaseMinCandles<1 || BaseMaxCandles<BaseMinCandles) return false;
   double atr=AmbilATR(tf);
   if(atr<=0) return false;

   // Pola sederhana: impuls awal, base sempit, lalu impuls keluar.
   // Ini kandidat monitoring, bukan validasi institusional lengkap.
   int baseCount=BaseMinCandles;
   if(baseCount>BaseMaxCandles) baseCount=BaseMaxCandles;
   int baseStart=2;
   int baseEnd=baseStart+baseCount-1;
   double baseHigh=-DBL_MAX,baseLow=DBL_MAX;
   for(int s=baseStart;s<=baseEnd;s++)
   {
      baseHigh=MathMax(baseHigh,iHigh(SymbolKerja,tf,s));
      baseLow=MathMin(baseLow,iLow(SymbolKerja,tf,s));
   }
   if(baseHigh<=baseLow || baseHigh-baseLow>atr*BaseMaxRangeATR) return false;

   double preOpen=iOpen(SymbolKerja,tf,baseEnd+1);
   double preClose=iClose(SymbolKerja,tf,baseEnd+1);
   double postOpen=iOpen(SymbolKerja,tf,1);
   double postClose=iClose(SymbolKerja,tf,1);
   if(preOpen<=0 || preClose<=0 || postOpen<=0 || postClose<=0) return false;

   bool preImpulse=bullish ? preClose>preOpen : preClose<preOpen;
   bool postImpulse=bullish ? postClose>postOpen : postClose<postOpen;
   if(!preImpulse || !postImpulse) return false;

   z.valid=true; z.bullish=bullish;
   z.kategori=(bullish?ZONA_RBR:ZONA_DBD);
   z.batasBawah=baseLow; z.batasAtas=baseHigh;
   z.ce50=(baseLow+baseHigh)/2.0;
   z.waktu=iTime(SymbolKerja,tf,baseStart);
   return ZonaRegistryValid(z);
}

bool EvaluasiRBR_DBD()
{
   if(!AktifkanRBR_DBD) return false;
   bool found=false;
   DataZona z;
   if(DeteksiRBR_DBD(InpEntryTF,true,z))
   {
      double p=SymbolInfoDouble(SymbolKerja,SYMBOL_POINT);
      if(p>0 && SimpanZonaRegistry(z,p*2)) found=true;
   }
   if(DeteksiRBR_DBD(InpEntryTF,false,z))
   {
      double p=SymbolInfoDouble(SymbolKerja,SYMBOL_POINT);
      if(p>0 && SimpanZonaRegistry(z,p*2)) found=true;
   }
   return found;
}

//==================================================
// MODUL 13: TP ZONA SEJENIS - TARGET REFERENSI SAJA
//==================================================
bool CariTargetZonaSejenis(DataZona &entry,double harga,DataZona &target)
{
   if(!ZonaRegistryValid(entry) || harga<=0) return false;
   double best=DBL_MAX; int bestIndex=-1;
   int limit=MathMin(JumlahZonaRegistry,MAX_ZONA_REGISTRY);
   for(int i=0;i<limit;i++)
   {
      if(!ZonaRegistryValid(RegistryZona[i])) continue;
      if(RegistryZona[i].kategori!=entry.kategori ||
         RegistryZona[i].bullish==entry.bullish ||
         RegistryZona[i].waktu==entry.waktu) continue;
      double p=RegistryZona[i].ce50;
      if(entry.bullish && p<=harga) continue;
      if(!entry.bullish && p>=harga) continue;
      double d=MathAbs(p-harga);
      if(d>0 && d<best) { best=d; bestIndex=i; }
   }
   if(bestIndex<0) return false;
   target=RegistryZona[bestIndex];
   return true;
}

//==================================================
// MODUL 14-15: RISK GUARDIAN / DAILY LOSS
//==================================================
bool RiskGuardianValid()
{
   return (MaxRiskPerBasketPct>0 && MaxRiskPerBasketPct<=100 &&
           MaxDailyLossPct>0 && MaxDailyLossPct<=100);
}
int HitungPosisiEA()
{
   int n=0;
   for(int i=0;i<PositionsTotal();i++)
   {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      if(PositionGetString(POSITION_SYMBOL)==SymbolKerja &&
         (ulong)PositionGetInteger(POSITION_MAGIC)==MagicNumber) n++;
   }
   return n;
}
double HitungFloatingEA()
{
   double total=0;
   for(int i=0;i<PositionsTotal();i++)
   {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=SymbolKerja ||
         (ulong)PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      total+=PositionGetDouble(POSITION_PROFIT)+PositionGetDouble(POSITION_SWAP);
   }
   return total;
}
double HitungProfitRealisasiEASejak(datetime mulai)
{
   datetime now=TimeTradeServer(); if(now<=0) now=TimeCurrent();
   if(mulai<=0 || now<mulai || !HistorySelect(mulai,now)) return EMPTY_VALUE;
   double total=0;
   for(int i=0;i<HistoryDealsTotal();i++)
   {
      ulong ticket=HistoryDealGetTicket(i);
      if(ticket==0) continue;
      if(HistoryDealGetString(ticket,DEAL_SYMBOL)!=SymbolKerja ||
         (ulong)HistoryDealGetInteger(ticket,DEAL_MAGIC)!=MagicNumber) continue;
      total+=HistoryDealGetDouble(ticket,DEAL_PROFIT)+
             HistoryDealGetDouble(ticket,DEAL_SWAP)+
             HistoryDealGetDouble(ticket,DEAL_COMMISSION);
   }
   return total;
}
bool PerbaruiMetrikHarianEA()
{
   datetime day=AwalHariServer();
   if(day<=0 || GVPrefix=="") return false;
   double savedDay=0,base=0,peak=0,tripped=0;
   bool same=BacaGV("day",savedDay) && (datetime)savedDay==day;
   if(!same)
   {
      base=AccountInfoDouble(ACCOUNT_BALANCE);
      peak=base;
      if(base<=0 || !SimpanGV("day",(double)day) ||
         !SimpanGV("dBase",base) || !SimpanGV("dPeak",peak) ||
         !SimpanGV("dTrip",0)) return false;
      DailyLossTerpicu=false;
   }
   else
   {
      if(!BacaGV("dBase",base) || !BacaGV("dPeak",peak) ||
         !BacaGV("dTrip",tripped)) return false;
      DailyLossTerpicu=(tripped>=1);
   }
   double realized=HitungProfitRealisasiEASejak(day);
   if(realized==EMPTY_VALUE) return false;
   double metric=base+realized+HitungFloatingEA();
   if(!MathIsValidNumber(metric) || metric<=0 || peak<=0) return false;
   if(metric>peak)
   {
      peak=metric;
      if(!SimpanGV("dPeak",peak)) return false;
   }
   double dd=(peak-metric)/peak*100.0;
   if(dd>=MaxDailyLossPct && !DailyLossTerpicu)
   {
      DailyLossTerpicu=true;
      if(!SimpanGV("dTrip",1.0)) return false;
      Print("Daily Loss Guard aktif: drawdown metrik EA=",DoubleToString(dd,2),"%");
   }
   MetrikAwalHariEA=base; PuncakMetrikHariEA=peak;
   return true;
}
bool BatasRugiHarianTercapai()
{
   if(!PerbaruiMetrikHarianEA())
   {
      Print("Daily Loss Guard: data tidak valid; sinyal diblokir.");
      return true;
   }
   return DailyLossTerpicu;
}
bool RiskGuardianBolehLanjut()
{
   if(!RiskGuardianValid()) return false;
   double balance=AccountInfoDouble(ACCOUNT_BALANCE);
   if(balance<=0) return false;
   double floatingLoss=0;
   for(int i=0;i<PositionsTotal();i++)
   {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=SymbolKerja ||
         (ulong)PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      double p=PositionGetDouble(POSITION_PROFIT)+PositionGetDouble(POSITION_SWAP);
      if(p<0) floatingLoss-=p;
   }
   double limit=balance*MaxDailyLossPct/100.0;
   return (limit>0 && floatingLoss<limit);
}

//==================================================
// MODUL 16: NEWS FILTER MANUAL FAIL-SAFE
//==================================================
bool NewsFilterBolehLanjut()
{
   if(!AktifkanNewsFilter) return true;
   if(NewsMulai<=0 || NewsSelesai<=0 || NewsSelesai<=NewsMulai)
   {
      Print("News Filter aktif tetapi jadwal invalid; sinyal diblokir.");
      return false;
   }
   datetime now=TimeTradeServer();
   if(now<=0) return false;
   return !(now>=NewsMulai && now<=NewsSelesai);
}

//==================================================
// MODUL 17-19: EXECUTION / POSITION GUARD (CHECK ONLY)
//==================================================
bool ValidasiEksekusiPasar()
{
   return (ValidasiHargaDanSpread() &&
           TerminalInfoInteger(TERMINAL_CONNECTED) &&
           MQLInfoInteger(MQL_TRADE_ALLOWED) &&
           DeviasiMaksimalPoints>=0);
}
bool ValidasiVolumeOrder(double volume)
{
   double minLot=SymbolInfoDouble(SymbolKerja,SYMBOL_VOLUME_MIN);
   double maxLot=SymbolInfoDouble(SymbolKerja,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(SymbolKerja,SYMBOL_VOLUME_STEP);
   if(volume<=0 || minLot<=0 || maxLot<minLot || step<=0 ||
      volume<minLot || volume>maxLot) return false;
   return (MathAbs((volume-minLot)/step-MathRound((volume-minLot)/step))<0.000001);
}
bool BatasPosisiEAValid()
{
   if(MaxPosisiEA<1) return false;
   return (HitungPosisiEA()<MaxPosisiEA);
}

//==================================================
// MODUL 20: PROFIT LOCK - SIGNAL LOCK ONLY
//==================================================
void PerbaruiProfitLock()
{
   if(!AktifkanProfitLock || GVPrefix=="") return;
   datetime day=AwalHariServer();
   if(day<=0) return;
   double savedDay=0,base=0,peak=0,tripped=0;
   bool same=BacaGV("plDay",savedDay) && (datetime)savedDay==day;
   if(!same)
   {
      base=0; peak=0; tripped=0;
      if(!SimpanGV("plDay",(double)day) || !SimpanGV("plBase",base) ||
         !SimpanGV("plPeak",peak) || !SimpanGV("plTrip",tripped)) return;
   }
   else if(!BacaGV("plBase",base) || !BacaGV("plPeak",peak) ||
           !BacaGV("plTrip",tripped))
   {
      ProfitLockTerpicu=true;
      Print("Profit Lock: state tidak lengkap; fail-safe blokir sinyal.");
      return;
   }
   ProfitLockTerpicu=(tripped>=1);
   if(ProfitLockTerpicu) return;
   double realized=HitungProfitRealisasiEASejak(day);
   if(realized==EMPTY_VALUE) return;
   double pnl=realized+HitungFloatingEA();
   if(pnl>peak)
   {
      peak=pnl;
      if(!SimpanGV("plPeak",peak)) return;
   }
   if(peak>=ProfitLockAktifUSD && peak-pnl>=ProfitLockMundurUSD)
   {
      ProfitLockTerpicu=true;
      SimpanGV("plTrip",1.0);
      Print("Profit Lock aktif: sinyal dikunci. Posisi tidak ditutup pada SIGNAL_ONLY.");
   }
}
bool ProfitLockBolehLanjut()
{
   PerbaruiProfitLock();
   return !ProfitLockTerpicu;
}

//==================================================
// MODUL 21: SAFETY GATE DAN M1 CONFIRMATION
//==================================================
bool SafetyGateLolos()
{
   if(!ValidasiEksekusiPasar()) return false;
   if(!ValidasiSemuaTimeframe() || !ValidasiATR()) return false;
   if(!RiskGuardianBolehLanjut()) return false;
   if(BatasRugiHarianTercapai()) return false;
   if(!NewsFilterBolehLanjut()) return false;
   if(!BatasPosisiEAValid()) return false;
   if(!ProfitLockBolehLanjut()) return false;
   return true;
}
bool KonfirmasiM1(bool bullish)
{
   if(!DataCandleTersedia(PERIOD_M1)) return false;
   double o=iOpen(SymbolKerja,PERIOD_M1,1),c=iClose(SymbolKerja,PERIOD_M1,1);
   double h=iHigh(SymbolKerja,PERIOD_M1,1),l=iLow(SymbolKerja,PERIOD_M1,1);
   if(o<=0 || c<=0 || h<=l) return false;
   return bullish ? c>o : c<o;
}

//==================================================
// DAILY PROFIT MILESTONE - TIDAK MENGHENTIKAN TRADING
//==================================================
double ProfitHarianEA()
{
   datetime day=AwalHariServer();
   double r=HitungProfitRealisasiEASejak(day);
   if(r==EMPTY_VALUE) return EMPTY_VALUE;
   return r+HitungFloatingEA();
}
bool TargetProfitHarianTercapai()
{
   double p=ProfitHarianEA();
   if(p==EMPTY_VALUE) return false;
   return (p>=TargetProfitHarian);
}

//==================================================
// INITIALIZATION / DEINITIALIZATION
//==================================================
int OnInit()
{
   if(ModeOperasi!=SIGNAL_ONLY)
   {
      Print("AUTO_TRADE belum tersedia. Pilih SIGNAL_ONLY.");
      return INIT_PARAMETERS_INCORRECT;
   }
   if(RiskNormalPct<=0 || RiskNormalPct>100 ||
      RiskSuperPct<=0 || RiskSuperPct>100 ||
      DailyLossLimitPct<=0 || DailyLossLimitPct>100 ||
      MaxDailyLossPct<=0 || MaxDailyLossPct>100 ||
      MaxRiskPerBasketPct<=0 || MaxRiskPerBasketPct>100 ||
      SpreadMaxPoints<=0 || ATRPeriod<2 ||
      MaxSuper<1 || MaxBiasa<1 || MaxRetest<1 ||
      MaxRBR<1 || MaxDBD<1 || SwingLookback<1 ||
      SwingScanBars<=SwingLookback*2 ||
      DisplacementATRMultiplier<=0 || MinBodyToRangeRatio<=0 ||
      MinBodyToRangeRatio>1 || MinFVG_ATR<0 ||
      MaxPosisiEA<1 || DeviasiMaksimalPoints<0 ||
      ProfitLockAktifUSD<0 || ProfitLockMundurUSD<0 ||
      ZonaExtendBars<1 || TargetProfitHarian<0 ||
      LotSuperMinimum<=0 || LotBiasaMinimum<=0 ||
      LotRetestMinimum<=0 || LotRBRMinimum<=0 || LotDBDMinimum<=0)
   {
      Print("ERROR: parameter EA tidak valid.");
      return INIT_PARAMETERS_INCORRECT;
   }

   SymbolKerja=CariSimbolKerja();
   if(SymbolKerja=="")
   {
      Print("ERROR: simbol XAUUSD tidak ditemukan / suffix tidak diizinkan.");
      return INIT_FAILED;
   }

   GVPrefix=BuatGVPrefix();
   StatePersistenceOK=(GVPrefix!="");
   RegistryGVPrefix=StringSubstr(GVPrefix,0,24)+"_ZR_";
   if(!StatePersistenceOK || !PulihkanZonaRegistry())
   {
      Print("ERROR: state / registry gagal dipulihkan.");
      return INIT_FAILED;
   }

   atrHandle=iATR(SymbolKerja,InpEntryTF,ATRPeriod);
   if(atrHandle==INVALID_HANDLE)
   {
      Print("ERROR: gagal membuat handle ATR.");
      return INIT_FAILED;
   }

   trade.SetExpertMagicNumber(MagicNumber);
   Print("APlus V4.16.2 MASTER aktif | SYMBOL=",SymbolKerja,
         " | MODE=SIGNAL_ONLY | ACCOUNT_CURRENCY=",AccountInfoString(ACCOUNT_CURRENCY));
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(atrHandle!=INVALID_HANDLE)
   {
      IndicatorRelease(atrHandle);
      atrHandle=INVALID_HANDLE;
   }
   // Objek zona dipertahankan di chart dan registry persisten.
}

//==================================================
// ONTICK - MONITORING ONLY
//==================================================
void OnTick()
{
   // Guard keras: build ini tidak mengirim order, tidak menutup posisi.
   if(ModeOperasi!=SIGNAL_ONLY) return;
   if(!SafetyGateLolos()) return;

   datetime barTime=iTime(SymbolKerja,InpEntryTF,0);
   if(barTime<=0 || barTime==lastBarTime) return;
   lastBarTime=barTime;

   bool buyValid=ValidasiSinyalDasar(true) && KonfirmasiM1(true);
   bool sellValid=ValidasiSinyalDasar(false) && KonfirmasiM1(false);
   bool rbrDbdFound=EvaluasiRBR_DBD();

   double dailyPnl=ProfitHarianEA();
   string targetStatus=(dailyPnl!=EMPTY_VALUE && dailyPnl>=TargetProfitHarian)
                       ? "TARGET_MINIMUM_TERCAPAI - EA TETAP MEMANTAU"
                       : "TARGET BELUM TERCAPAI";

   string status=StringFormat(
      "APlus V4.16.2 | SIGNAL_ONLY | BUY=%s | SELL=%s | PosisiEA=%d | "
      "Zona Super B/S=%d/%d | RBR/DBD=%d/%d | P/L Hari=%s %s | "
      "Fundamental=UNAVAILABLE | News=MANUAL",
      buyValid?"VALID":"-",
      sellValid?"VALID":"-",
      HitungPosisiEA(),
      HitungZonaAktif(ZONA_SUPER,true),
      HitungZonaAktif(ZONA_SUPER,false),
      HitungZonaAktif(ZONA_RBR,true),
      HitungZonaAktif(ZONA_DBD,false),
      dailyPnl==EMPTY_VALUE?"N/A":DoubleToString(dailyPnl,2),
      targetStatus
   );
   Print(status);
   if(AktifkanAlertSinyal && (buyValid || sellValid || rbrDbdFound))
      Alert(status);
}