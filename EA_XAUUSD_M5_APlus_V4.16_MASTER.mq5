#property strict
#property version "4.16"
#property description "APlus V4.16 MASTER - safe monitoring build; does not send or close orders"

#include <Trade/Trade.mqh>
CTrade trade;

//==================================================
// EA XAUUSD M5 APLUS V4.16 MASTER
// MODE AMAN: TIDAK MEMBUKA / MENUTUP TRANSAKSI
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

input double MaxRiskPerBasketPct = 0.50;
input double MaxDailyLossPct = 4.0;

input bool AktifkanNewsFilter = true;
input datetime NewsMulai = 0;
input datetime NewsSelesai = 0;

input int DeviasiMaksimalPoints = 30;
input int MaxPosisiEA = 8;

input bool AktifkanProfitLock = true;
input double ProfitLockAktifUSD = 10.0;
input double ProfitLockMundurUSD = 3.0;

datetime lastBarTime = 0;
int atrHandle = INVALID_HANDLE;
double EkuitasAwalHari = 0.0;
datetime HariTercatat = 0;
double PuncakEkuitasEA = 0.0;
double EkuitasAwalProfitLock = 0.0;
bool ProfitLockTerpicu = false;

enum KategoriZona { ZONA_SUPER = 0, ZONA_BIASA = 1, ZONA_RETEST = 2 };

struct ZonaFVG {
   bool valid;
   bool bullish;
   double batasBawah;
   double batasAtas;
   double ce50;
};

struct ZonaOB {
   bool valid;
   bool bullish;
   double batasBawah;
   double batasAtas;
   datetime waktu;
};

struct DataZona {
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

//--------------------------------------------------
// REGISTRY ZONA
//--------------------------------------------------
bool ZonaRegistryValid(DataZona &zona) {
   if(!zona.valid || zona.batasBawah <= 0.0 ||
      zona.batasAtas <= zona.batasBawah ||
      zona.ce50 < zona.batasBawah || zona.ce50 > zona.batasAtas ||
      zona.waktu <= 0) return false;
   if(zona.kategori != ZONA_SUPER && zona.kategori != ZONA_BIASA &&
      zona.kategori != ZONA_RETEST) return false;
   return true;
}

int CariZonaRegistry(DataZona &zona, double toleransiHarga) {
   if(toleransiHarga < 0.0) return -1;
   for(int i=0; i<JumlahZonaRegistry; i++) {
      if(!RegistryZona[i].valid ||
         RegistryZona[i].bullish != zona.bullish ||
         RegistryZona[i].kategori != zona.kategori ||
         RegistryZona[i].waktu != zona.waktu) continue;
      if(MathAbs(RegistryZona[i].batasBawah-zona.batasBawah)>toleransiHarga) continue;
      if(MathAbs(RegistryZona[i].batasAtas-zona.batasAtas)>toleransiHarga) continue;
      return i;
   }
   return -1;
}

bool SimpanZonaRegistry(DataZona &zona, double toleransiHarga) {
   if(!ZonaRegistryValid(zona)) {
      Print("Zone Registry: zona tidak valid.");
      return false;
   }
   int idx=CariZonaRegistry(zona,toleransiHarga);
   if(idx>=0) { RegistryZona[idx]=zona; return true; }
   if(JumlahZonaRegistry>=MAX_ZONA_REGISTRY) {
      Print("Zone Registry penuh."); return false;
   }
   RegistryZona[JumlahZonaRegistry++]=zona;
   Print("Zone Registry: zona disimpan. Total=",JumlahZonaRegistry);
   return true;
}

bool NonaktifkanZonaRegistry(int indeks) {
   if(indeks<0 || indeks>=JumlahZonaRegistry) return false;
   RegistryZona[indeks].valid=false;
   return true;
}

int HitungZonaAktif(KategoriZona kategori, bool bullish) {
   int total=0;
   for(int i=0;i<JumlahZonaRegistry;i++)
      if(RegistryZona[i].valid && RegistryZona[i].kategori==kategori &&
         RegistryZona[i].bullish==bullish) total++;
   return total;
}

//--------------------------------------------------
// INISIALISASI
//--------------------------------------------------
int OnInit() {
   if(RiskNormalPct<=0 || RiskNormalPct>100 || RiskSuperPct<=0 || RiskSuperPct>100 ||
      DailyLossLimitPct<=0 || DailyLossLimitPct>100 ||
      MaxDailyLossPct<=0 || MaxDailyLossPct>100 ||
      MaxRiskPerBasketPct<=0 || MaxRiskPerBasketPct>100 ||
      SpreadMaxPoints<=0 || ATRPeriod<2 || MaxSuper<1 || MaxBiasa<1 ||
      MaxRetest<1 || SwingLookback<1 || SwingScanBars<=SwingLookback*2 ||
      DisplacementATRMultiplier<=0 || MinBodyToRangeRatio<=0 ||
      MinBodyToRangeRatio>1 || MinFVG_ATR<0 || MaxPosisiEA<1 ||
      DeviasiMaksimalPoints<0 || ProfitLockAktifUSD<0 || ProfitLockMundurUSD<0) {
      Print("ERROR: Parameter EA tidak valid.");
      return INIT_PARAMETERS_INCORRECT;
   }
   if(!SymbolSelect(InpSymbol,true)) {
      Print("ERROR: Simbol tidak tersedia: ",InpSymbol);
      return INIT_FAILED;
   }
   atrHandle=iATR(InpSymbol,InpEntryTF,ATRPeriod);
   if(atrHandle==INVALID_HANDLE) {
      Print("ERROR: Gagal membuat indikator ATR.");
      return INIT_FAILED;
   }
   trade.SetExpertMagicNumber(MagicNumber);
   Print("APlus V4.16 MASTER diinisialisasi. MODE AMAN aktif; tidak ada transaksi otomatis.");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) {
   if(atrHandle!=INVALID_HANDLE) {
      IndicatorRelease(atrHandle);
      atrHandle=INVALID_HANDLE;
   }
}

//--------------------------------------------------
// DATA PASAR DAN INDIKATOR
//--------------------------------------------------
bool ValidasiHargaDanSpread() {
   MqlTick tick;
   if(!SymbolInfoTick(InpSymbol,tick) || tick.bid<=0 || tick.ask<=0 || tick.ask<tick.bid)
      return false;
   double point=SymbolInfoDouble(InpSymbol,SYMBOL_POINT);
   if(point<=0) return false;
   return ((tick.ask-tick.bid)/point)<=SpreadMaxPoints;
}

bool DataCandleTersedia(ENUM_TIMEFRAMES tf) {
   long synchronized=0;
   if(!SeriesInfoInteger(InpSymbol,tf,SERIES_SYNCHRONIZED,synchronized) || synchronized==0)
      return false;
   return Bars(InpSymbol,tf)>=100;
}

bool ValidasiATR() {
   if(atrHandle==INVALID_HANDLE || BarsCalculated(atrHandle)<ATRPeriod+2) return false;
   double a[1];
   if(CopyBuffer(atrHandle,0,1,1,a)!=1) return false;
   return a[0]>0 && MathIsValidNumber(a[0]);
}

double AmbilATR(ENUM_TIMEFRAMES tf) {
   int h=iATR(InpSymbol,tf,ATRPeriod);
   if(h==INVALID_HANDLE) return 0.0;
   double b[1];
   bool ok=BarsCalculated(h)>=ATRPeriod+2 && CopyBuffer(h,0,1,1,b)==1;
   IndicatorRelease(h);
   if(!ok || b[0]<=0 || !MathIsValidNumber(b[0])) return 0.0;
   return b[0];
}

bool ValidasiDataIndikator(ENUM_TIMEFRAMES tf) {
   if(!DataCandleTersedia(tf)) return false;
   int h=iATR(InpSymbol,tf,ATRPeriod);
   if(h==INVALID_HANDLE) return false;
   bool ok=false;
   if(BarsCalculated(h)>=ATRPeriod+2) {
      double b[2];
      if(CopyBuffer(h,0,1,2,b)==2)
         ok=b[0]>0 && b[1]>0 && MathIsValidNumber(b[0]) && MathIsValidNumber(b[1]);
   }
   IndicatorRelease(h);
   if(!ok) Print("Validasi indikator gagal pada timeframe ",EnumToString(tf));
   return ok;
}

bool ValidasiSemuaTimeframe() {
   return ValidasiDataIndikator(PERIOD_M1) && ValidasiDataIndikator(PERIOD_M5) &&
          ValidasiDataIndikator(PERIOD_M15) && ValidasiDataIndikator(PERIOD_H1) &&
          ValidasiDataIndikator(PERIOD_H4) && ValidasiDataIndikator(PERIOD_D1);
}

//--------------------------------------------------
// MODUL 1: SWING
//--------------------------------------------------
bool DeteksiSwingHigh(ENUM_TIMEFRAMES tf,int shift) {
   int total=Bars(InpSymbol,tf);
   if(SwingLookback<1 || shift<=SwingLookback || shift+SwingLookback>=total) return false;
   double v=iHigh(InpSymbol,tf,shift);
   if(v<=0) return false;
   for(int i=1;i<=SwingLookback;i++) {
      if(iHigh(InpSymbol,tf,shift-i)>=v || iHigh(InpSymbol,tf,shift+i)>v) return false;
   }
   return true;
}

bool DeteksiSwingLow(ENUM_TIMEFRAMES tf,int shift) {
   int total=Bars(InpSymbol,tf);
   if(SwingLookback<1 || shift<=SwingLookback || shift+SwingLookback>=total) return false;
   double v=iLow(InpSymbol,tf,shift);
   if(v<=0) return false;
   for(int i=1;i<=SwingLookback;i++) {
      if(iLow(InpSymbol,tf,shift-i)<=v || iLow(InpSymbol,tf,shift+i)<v) return false;
   }
   return true;
}

double AmbilSwingTerakhir(ENUM_TIMEFRAMES tf,bool cariHigh) {
   int total=Bars(InpSymbol,tf);
   if(total<=SwingLookback*2+2) return 0.0;
   int batas=(int)MathMin(SwingScanBars,total-SwingLookback-1);
   for(int shift=SwingLookback+1;shift<batas;shift++) {
      if(cariHigh && DeteksiSwingHigh(tf,shift)) return iHigh(InpSymbol,tf,shift);
      if(!cariHigh && DeteksiSwingLow(tf,shift)) return iLow(InpSymbol,tf,shift);
   }
   return 0.0;
}

//--------------------------------------------------
// MODUL 2: LIQUIDITY SWEEP
//--------------------------------------------------
bool DeteksiSweepHigh(ENUM_TIMEFRAMES tf) {
   double s=AmbilSwingTerakhir(tf,true);
   if(s<=0) return false;
   return iHigh(InpSymbol,tf,1)>s && iClose(InpSymbol,tf,1)<s;
}
bool DeteksiSweepLow(ENUM_TIMEFRAMES tf) {
   double s=AmbilSwingTerakhir(tf,false);
   if(s<=0) return false;
   return iLow(InpSymbol,tf,1)<s && iClose(InpSymbol,tf,1)>s;
}

//--------------------------------------------------
// MODUL 3: DISPLACEMENT
//--------------------------------------------------
bool DeteksiDisplacement(ENUM_TIMEFRAMES tf,bool bullish) {
   double atr=AmbilATR(tf);
   if(atr<=0) return false;
   double o=iOpen(InpSymbol,tf,1), c=iClose(InpSymbol,tf,1);
   double h=iHigh(InpSymbol,tf,1), l=iLow(InpSymbol,tf,1);
   double range=h-l, body=MathAbs(c-o);
   if(range<=0 || body<atr*DisplacementATRMultiplier || body/range<MinBodyToRangeRatio)
      return false;
   return bullish ? c>o : c<o;
}

//--------------------------------------------------
// MODUL 4: MARKET STRUCTURE SHIFT
//--------------------------------------------------
bool DeteksiMSS(ENUM_TIMEFRAMES tf,bool bullish) {
   double c=iClose(InpSymbol,tf,1);
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
   if(Bars(InpSymbol,tf)<10) return z;
   double h3=iHigh(InpSymbol,tf,3), l3=iLow(InpSymbol,tf,3);
   double h1=iHigh(InpSymbol,tf,1), l1=iLow(InpSymbol,tf,1);
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
   int total=Bars(InpSymbol,tf);
   if(total<20) return z;
   for(int shift=2;shift<=10 && shift<total;shift++) {
      double o=iOpen(InpSymbol,tf,shift), c=iClose(InpSymbol,tf,shift);
      double h=iHigh(InpSymbol,tf,shift), l=iLow(InpSymbol,tf,shift);
      if(h<=l || o<=0 || c<=0) continue;
      bool opposite=bullish ? c<o : c>o;
      if(!opposite) continue;
      z.valid=true; z.batasBawah=l; z.batasAtas=h; z.waktu=iTime(InpSymbol,tf,shift);
      return z;
   }
   return z;
}

//--------------------------------------------------
// MODUL 7: BIAS MULTI-TIMEFRAME
//--------------------------------------------------
bool BiasBullish(ENUM_TIMEFRAMES tf) {
   double c1=iClose(InpSymbol,tf,1), c2=iClose(InpSymbol,tf,2);
   return c1>0 && c2>0 && c1>c2;
}
bool BiasBearish(ENUM_TIMEFRAMES tf) {
   double c1=iClose(InpSymbol,tf,1), c2=iClose(InpSymbol,tf,2);
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
   int total=Bars(InpSymbol,tf);
   if(total<=shiftZona+1) return false;
   for(int shift=shiftZona-1;shift>=1;shift--) {
      double c=iClose(InpSymbol,tf,shift), h=iHigh(InpSymbol,tf,shift), l=iLow(InpSymbol,tf,shift);
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
   return MaxRetest;
}
KategoriZona KlasifikasiZona(bool sweep,bool displacement,bool mss,bool fvg,bool ob) {
   int score=0;
   if(sweep) score++; if(displacement) score++; if(mss) score++; if(fvg) score++; if(ob) score++;
   if(score>=5) return ZONA_SUPER;
   if(score>=3) return ZONA_BIASA;
   return ZONA_RETEST;
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
   if(!sweep || !displacement || !mss || !fvgSearah || !ob.valid || !bias) return false;
   // FVG dihasilkan dari candle 3 dan 1; validasi mitigasi dari pembentukan zona.
   if(!ZonaMasihLayak(InpEntryTF,fvg.bullish,fvg.batasBawah,fvg.batasAtas,3)) return false;
   DataZona z;
   z.valid=true; z.bullish=bullish; z.batasBawah=fvg.batasBawah;
   z.batasAtas=fvg.batasAtas; z.ce50=fvg.ce50;
   z.waktu=iTime(InpSymbol,InpEntryTF,1);
   z.kategori=KlasifikasiZona(sweep,displacement,mss,fvgSearah,ob.valid);
   double point=SymbolInfoDouble(InpSymbol,SYMBOL_POINT);
   if(point<=0 || !SimpanZonaRegistry(z,point*2.0)) return false;
   Print("Zona tervalidasi dan diregistrasi. Kategori=",(int)z.kategori,
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
   for(int i=0;i<JumlahZonaRegistry;i++) {
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
      if(PositionGetString(POSITION_SYMBOL)!=InpSymbol ||
         (ulong)PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      double p=PositionGetDouble(POSITION_PROFIT)+PositionGetDouble(POSITION_SWAP);
      if(p<0) floatingLoss+=-p;
   }
   if(floatingLoss>=limit) { Print("Risk Guardian: batas floating loss EA tercapai."); return false; }
   return true;
}

//--------------------------------------------------
// MODUL 15: DAILY LOSS GUARD (baseline tersimpan saat sesi berjalan)
//--------------------------------------------------
datetime AwalHariServer() {
   MqlDateTime t; TimeToStruct(TimeCurrent(),t);
   t.hour=0; t.min=0; t.sec=0;
   return StructToTime(t);
}
bool PerbaruiEkuitasAwalHari() {
   datetime day=AwalHariServer();
   if(day<=0) return false;
   if(HariTercatat!=day) {
      double eq=AccountInfoDouble(ACCOUNT_EQUITY);
      if(eq<=0) return false;
      EkuitasAwalHari=eq; HariTercatat=day;
      Print("Daily Loss Guard: baseline ekuitas hari ini dicatat.");
   }
   return EkuitasAwalHari>0;
}
bool BatasRugiHarianTercapai() {
   if(!PerbaruiEkuitasAwalHari()) return true;
   double eq=AccountInfoDouble(ACCOUNT_EQUITY);
   if(eq<=0) return true;
   double limit=EkuitasAwalHari*MaxDailyLossPct/100.0;
   if(EkuitasAwalHari-eq>=limit) {
      Print("Daily Loss Guard: batas kerugian harian tercapai."); return true;
   }
   return false;
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
   double minLot=SymbolInfoDouble(InpSymbol,SYMBOL_VOLUME_MIN);
   double maxLot=SymbolInfoDouble(InpSymbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(InpSymbol,SYMBOL_VOLUME_STEP);
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
      if(PositionGetString(POSITION_SYMBOL)==InpSymbol &&
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
// MODUL 20: PROFIT LOCK (pemantauan saja)
//--------------------------------------------------
void PerbaruiProfitLock() {
   if(!AktifkanProfitLock || ProfitLockTerpicu) return;
   double eq=AccountInfoDouble(ACCOUNT_EQUITY);
   if(eq<=0) return;
   if(EkuitasAwalProfitLock<=0) { EkuitasAwalProfitLock=eq; PuncakEkuitasEA=eq; return; }
   if(eq>PuncakEkuitasEA) PuncakEkuitasEA=eq;
   double profit=eq-EkuitasAwalProfitLock;
   double drawdown=PuncakEkuitasEA-eq;
   if(profit>=ProfitLockAktifUSD && drawdown>=ProfitLockMundurUSD) {
      ProfitLockTerpicu=true;
      Print("Profit Lock terpicu. Mode aman: tidak ada posisi ditutup.");
   }
}
bool ProfitLockBolehLanjut() {
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
   double o=iOpen(InpSymbol,PERIOD_M1,1), c=iClose(InpSymbol,PERIOD_M1,1);
   double h=iHigh(InpSymbol,PERIOD_M1,1), l=iLow(InpSymbol,PERIOD_M1,1);
   if(o<=0 || c<=0 || h<=l) return false;
   return bullish ? c>o : c<o;
}

//--------------------------------------------------
// ONTICK: PEMANTAUAN SINYAL SAJA
//--------------------------------------------------
void OnTick() {
   // Tidak ada trade.Buy, trade.Sell, PositionClose atau order send di build ini.
   if(!SafetyGateLolos()) return;
   if(!ValidasiATR()) return;
   datetime barTime=iTime(InpSymbol,InpEntryTF,0);
   if(barTime<=0 || barTime==lastBarTime) return;
   lastBarTime=barTime;

   bool buyValid=ValidasiSinyalDasar(true) && KonfirmasiM1(true);
   bool sellValid=ValidasiSinyalDasar(false) && KonfirmasiM1(false);

   Print("APlus V4.16 MASTER | BUY=",buyValid,
         " | SELL=",sellValid,
         " | Posisi EA=",HitungPosisiEA(),
         " | Zona aktif BUY Super=",HitungZonaAktif(ZONA_SUPER,true),
         " | Zona aktif SELL Super=",HitungZonaAktif(ZONA_SUPER,false),
         " | MODE AMAN.");
}