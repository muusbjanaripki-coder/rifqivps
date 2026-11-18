Kita masuk ke TAHAP 3: Mesin VIP Scalp Agresif (Limit & Stop Tanpa Henti).
Pada tahap ini kita menyatukan seluruh kesepakatan scalping kita:
1. Memisahkan CHAOS NGANTUK vs CHAOS NGAMUK:
	• CHAOS NGANTUK (candle kecil-kecil rapat < 15 pips) & RANGE → Masuk ke Kubu Limit Order (2 lapis Dual-Limit + tembakan instan ping-pong, SL adaptif mengikuti lebar kotak, dan TP diletakkan 1.5 pips di depan Limit Order lawan arah).
	• CHAOS NGAMUK (candle liar besar ≥ 22 pips & ≥ 1.8x ATR M1), TRENDING, SQUEEZE, & VIP NEWS → Masuk ke Kubu Stop Order (entry awal instan tanpa jeda, 2 posisi tanpa TP, dan Reverse Stop selalu menempel di SL & SL+ tanpa batas flip).
2. Auto-Trendline Channel Lock Anti-Goyang: Saluran M1 dikunci selama harga masih di dalam lorong dan otomatis merata menjadi kotak horizontal jika kemiringan tidak jelas.
Lakukan 4 penggantian blok berikut di MetaEditor:

3A. Perbarui Cuaca Pasar (CHAOS NGANTUK vs CHAOS NGAMUK) & Auto-Trendline Channel Lock

Cari bagian deklarasi variabel bool g_MarketChaos = false; dan fungsi DS_EvaluasiCuacaPasar(), TL_Bangun(), serta TL_GambarChart() (sekitar baris 1150–1275), lalu ganti bagian tersebut dengan blok kode di bawah ini:
mql5
bool     g_MarketChaos = false;       // Chaos Ngamuk (candle besar/liar -> Stop Order)
bool     g_MarketChaosNgantuk = false;// Chaos Ngantuk (candle kecil rapat -> Limit Order)
bool     g_MarketSqueeze = false;
double   g_VaultLockedUSD = 0.0;
datetime g_VaultDayStart = 0;

void DS_EvaluasiCuacaPasar()
{
   datetime vaultDay = AwalHariServer();
   if(vaultDay > 0 && vaultDay != g_VaultDayStart)
   { g_VaultDayStart = vaultDay; g_VaultLockedUSD = 0.0; }

   g_MarketChaos = false;
   g_MarketChaosNgantuk = false;
   g_MarketSqueeze = false;
   if(gM1n < 20 || g_atr1 <= 0.0) return;

   int candleNgamuk = 0;
   int candleNgantuk = 0;
   for(int i = 1; i <= 5; i++)
   {
      double rng = gM1[i].high - gM1[i].low;
      double body = MathAbs(gM1[i].close - gM1[i].open);
      if(rng <= 0.0) continue;
      double wickRatio = (rng - body) / rng;

      // Chaos Ngamuk: candle liar besar (>= 22 pips dan >= 1.8x ATR M1) dengan ekor panjang
      if(wickRatio >= 0.65 && rng >= V24_Pip(22.0) && rng >= g_atr1 * 1.8)
         candleNgamuk++;
      // Chaos Ngantuk: candle kecil-kecil rapat (< 15 pips) yang bolak-balik di tempat
      else if(wickRatio >= 0.55 && rng < V24_Pip(15.0))
         candleNgantuk++;
   }

   if(candleNgamuk >= 3) g_MarketChaos = true;
   else if(candleNgantuk >= 3) g_MarketChaosNgantuk = true;

   double sumRng = 0.0;
   for(int k = 1; k <= 5; k++) sumRng += (gM1[k].high - gM1[k].low);
   if((sumRng / 5.0) < g_atr1 * 0.55 && !g_MarketChaosNgantuk) g_MarketSqueeze = true;

   double pnlH = V24_ProfitHarian();
   double bal = AccountInfoDouble(ACCOUNT_BALANCE);
   if(bal > 0.0 && pnlH > bal * 0.03)
      g_VaultLockedUSD = MathMax(g_VaultLockedUSD, pnlH * 0.70);
}

// Channel Lock: saluran M1 dikunci agar tidak goyang selama harga masih di dalam lorong
datetime g_TLLockTime = 0;

bool TL_Bangun(ENUM_TIMEFRAMES tf, int scanBars, int lb, TrendlineChannel &out)
{
   if(tf == PERIOD_M1 && g_TL_M1.valid && g_TLLockTime > 0)
   {
      datetime nowT = iTime(SymbolKerja, PERIOD_M1, 0);
      double c1 = iClose(SymbolKerja, PERIOD_M1, 1);
      double upNow = TL_HargaPadaWaktu(g_TL_M1.tA1, g_TL_M1.pA1, g_TL_M1.tA2, g_TL_M1.pA2, nowT);
      double dnNow = TL_HargaPadaWaktu(g_TL_M1.tB1, g_TL_M1.pB1, g_TL_M1.tB2, g_TL_M1.pB2, nowT);
      double padBreak = V24_Pip(3.0);
      // Pertahankan saluran lama jika harga belum jebol > 3 pips dan umur saluran < 35 menit
      if(c1 <= upNow + padBreak && c1 >= dnNow - padBreak && (TimeCurrent() - g_TLLockTime) < 2100 && (upNow - dnNow) >= V24_Pip(10.0))
      {
         out = g_TL_M1;
         return true;
      }
   }

   out.valid = false; out.isFlat = false;
   MqlRates r[]; ArraySetAsSeries(r, true);
   int got = CopyRates(SymbolKerja, tf, 0, scanBars + lb + 5, r);
   if(got < lb * 2 + 10) return false;
   int idxH[2] = {-1, -1}, nh = 0;
   int idxL[2] = {-1, -1}, nl = 0;
   for(int i = lb + 1; i <= scanBars && i + lb < got; i++)
   {
      if(nh < 2)
      {
         bool sh = true;
         for(int k = 1; k <= lb; k++) if(r[i].high <= r[i-k].high || r[i].high <= r[i+k].high) { sh = false; break; }
         if(sh) idxH[nh++] = i;
      }
      if(nl < 2)
      {
         bool sl = true;
         for(int k = 1; k <= lb; k++) if(r[i].low >= r[i-k].low || r[i].low >= r[i+k].low) { sl = false; break; }
         if(sl) idxL[nl++] = i;
      }
      if(nh == 2 && nl == 2) break;
   }
   if(nh < 2 || nl < 2) return false;
   out.tA1 = r[idxH[1]].time; out.pA1 = r[idxH[1]].high;
   out.tA2 = r[idxH[0]].time; out.pA2 = r[idxH[0]].high;
   out.tB1 = r[idxL[1]].time; out.pB1 = r[idxL[1]].low;
   out.tB2 = r[idxL[0]].time; out.pB2 = r[idxL[0]].low;

   // Auto-Snap ke kotak mendatar jika arah miring tidak jelas (< 6 pips) atau berlawanan (segitiga sempit)
   double diffA = out.pA2 - out.pA1;
   double diffB = out.pB2 - out.pB1;
   if((MathAbs(diffA) < V24_Pip(6.0) && MathAbs(diffB) < V24_Pip(6.0)) || (diffA * diffB < 0))
   {
      double hiBox = MS_MaxHigh(r, got, 1, 20);
      double loBox = MS_MinLow(r, got, 1, 20);
      out.pA1 = out.pA2 = hiBox;
      out.pB1 = out.pB2 = loBox;
      out.isFlat = true;
   }

   datetime nowT = r[0].time;
   double upNow = TL_HargaPadaWaktu(out.tA1, out.pA1, out.tA2, out.pA2, nowT);
   double dnNow = TL_HargaPadaWaktu(out.tB1, out.pB1, out.tB2, out.pB2, nowT);
   if(upNow - dnNow < V24_Pip(10.0) || upNow - dnNow > V24_Pip(50.0))
   {
      out.pA1 = out.pA2 = MS_MaxHigh(r, got, 1, 15);
      out.pB1 = out.pB2 = MS_MinLow(r, got, 1, 15);
      out.isFlat = true;
      upNow = out.pA1; dnNow = out.pB1;
   }
   if(upNow <= dnNow + V24_Pip(6.0)) return false;

   out.valid = true;
   if(tf == PERIOD_M1) { g_TL_M1 = out; g_TLLockTime = TimeCurrent(); }
   return true;
}

void TL_GambarChart()
{
   ENUM_TIMEFRAMES ctf = (ENUM_TIMEFRAMES)_Period;
   TrendlineChannel tl;
   int barsScan = (ctf == PERIOD_M1 ? 30 : 85), lb = (ctf == PERIOD_M1 ? 2 : 3);
   if(!TL_Bangun(ctf, barsScan, lb, tl))
   {
      ObjectDelete(0, "A24_TL_UP"); ObjectDelete(0, "A24_TL_DN");
      ObjectDelete(0, "A24_TL_MID"); ObjectDelete(0, "A24_TL_HUD"); return;
   }
   int sec = PeriodSeconds(ctf); if(sec <= 0) sec = 60;
   datetime tEnd = iTime(SymbolKerja, ctf, 0) + (datetime)(sec * 12);
   double pUpEnd = TL_HargaPadaWaktu(tl.tA1, tl.pA1, tl.tA2, tl.pA2, tEnd);
   double pDnEnd = TL_HargaPadaWaktu(tl.tB1, tl.pB1, tl.tB2, tl.pB2, tEnd);
   string nUp="A24_TL_UP", nDn="A24_TL_DN", nMid="A24_TL_MID", nHud="A24_TL_HUD";
   if(ObjectFind(0,nUp)<0) ObjectCreate(0,nUp,OBJ_TREND,0,tl.tA1,tl.pA1,tEnd,pUpEnd);
   else { ObjectMove(0,nUp,0,tl.tA1,tl.pA1); ObjectMove(0,nUp,1,tEnd,pUpEnd); }
   ObjectSetInteger(0,nUp,OBJPROP_COLOR,clrAqua); ObjectSetInteger(0,nUp,OBJPROP_WIDTH,2);
   ObjectSetInteger(0,nUp,OBJPROP_STYLE,tl.isFlat?STYLE_DASH:STYLE_SOLID);
   ObjectSetInteger(0,nUp,OBJPROP_RAY_RIGHT,false); ObjectSetInteger(0,nUp,OBJPROP_SELECTABLE,false);
   if(ObjectFind(0,nDn)<0) ObjectCreate(0,nDn,OBJ_TREND,0,tl.tB1,tl.pB1,tEnd,pDnEnd);
   else { ObjectMove(0,nDn,0,tl.tB1,tl.pB1); ObjectMove(0,nDn,1,tEnd,pDnEnd); }
   ObjectSetInteger(0,nDn,OBJPROP_COLOR,clrGold); ObjectSetInteger(0,nDn,OBJPROP_WIDTH,2);
   ObjectSetInteger(0,nDn,OBJPROP_STYLE,tl.isFlat?STYLE_DASH:STYLE_SOLID);
   ObjectSetInteger(0,nDn,OBJPROP_RAY_RIGHT,false); ObjectSetInteger(0,nDn,OBJPROP_SELECTABLE,false);
   datetime tMidStart=MathMax(tl.tA1,tl.tB1);
   double pMid1=0.5*(TL_HargaPadaWaktu(tl.tA1,tl.pA1,tl.tA2,tl.pA2,tMidStart)+TL_HargaPadaWaktu(tl.tB1,tl.pB1,tl.tB2,tl.pB2,tMidStart));
   double pMid2=0.5*(pUpEnd+pDnEnd);
   if(ObjectFind(0,nMid)<0) ObjectCreate(0,nMid,OBJ_TREND,0,tMidStart,pMid1,tEnd,pMid2);
   else { ObjectMove(0,nMid,0,tMidStart,pMid1); ObjectMove(0,nMid,1,tEnd,pMid2); }
   ObjectSetInteger(0,nMid,OBJPROP_COLOR,C'110,125,145'); ObjectSetInteger(0,nMid,OBJPROP_WIDTH,1);
   ObjectSetInteger(0,nMid,OBJPROP_STYLE,STYLE_DOT); ObjectSetInteger(0,nMid,OBJPROP_RAY_RIGHT,false);
   ObjectSetInteger(0,nMid,OBJPROP_SELECTABLE,false);
   if(ObjectFind(0,nHud)<0) ObjectCreate(0,nHud,OBJ_TEXT,0,tEnd,pUpEnd); else ObjectMove(0,nHud,0,tEnd,pUpEnd);
   string hudTxt=(g_MarketChaos?"[CHAOS NGAMUK • STOP]":(g_MarketChaosNgantuk?"[CHAOS NGANTUK • LIMIT]":(g_MarketSqueeze?"[SQUEEZE • SIAP STOP]":(tl.isFlat?"[RANGE BOX • LIMIT]":"[TREND CHANNEL]"))));
   color hudClr=(g_MarketChaos?clrTomato:(g_MarketChaosNgantuk?clrAqua:(g_MarketSqueeze?clrGold:clrSpringGreen)));
   ObjectSetString(0,nHud,OBJPROP_TEXT,hudTxt);
   ObjectSetInteger(0,nHud,OBJPROP_COLOR,hudClr);
   ObjectSetString(0,nHud,OBJPROP_FONT,"Consolas Bold"); ObjectSetInteger(0,nHud,OBJPROP_FONTSIZE,8);
   ObjectSetInteger(0,nHud,OBJPROP_ANCHOR,ANCHOR_LEFT_LOWER); ObjectSetInteger(0,nHud,OBJPROP_SELECTABLE,false);
}
Gunakan kode dengan hati-hati.

3B. Perbarui Penentu Mode (MS_M1SedangRange)

Cari fungsi bool MS_M1SedangRange() (sekitar baris 1280), lalu ganti seluruh fungsi tersebut dengan kode ini agar CHAOS NGANTUK dan RANGE masuk ke kubu Limit Order, sedangkan CHAOS NGAMUK, TRENDING, SQUEEZE, dan VIP NEWS langsung masuk ke kubu Stop Order tanpa jeda:
mql5
bool MS_M1SedangRange()
{
   // Kubu Stop Order: VIP News, Chaos Ngamuk, atau Squeeze -> langsung FALSE (masuk Stop Order)
   if(g_NewsModeVIP > 0 || g_MarketChaos || g_MarketSqueeze)
   {
      g_ScalpModeRangeTerkunci = false;
      g_WaktuKunciScalpMode = TimeCurrent();
      return false;
   }
   // Kubu Limit Order: Chaos Ngantuk -> langsung TRUE (masuk Limit Order)
   if(g_MarketChaosNgantuk)
   {
      g_ScalpModeRangeTerkunci = true;
      g_WaktuKunciScalpMode = TimeCurrent();
      return true;
   }
   if(!TL_Bangun(PERIOD_M1, 30, 2, g_TL_M1)) return true;
   datetime t1 = iTime(SymbolKerja, PERIOD_M1, 1);
   double c1 = iClose(SymbolKerja, PERIOD_M1, 1);
   double up1 = TL_HargaPadaWaktu(g_TL_M1.tA1, g_TL_M1.pA1, g_TL_M1.tA2, g_TL_M1.pA2, t1);
   double dn1 = TL_HargaPadaWaktu(g_TL_M1.tB1, g_TL_M1.pB1, g_TL_M1.tB2, g_TL_M1.pB2, t1);
   bool diDalamLorong = (c1 <= up1 + V24_Pip(3.0) && c1 >= dn1 - V24_Pip(3.0));
   g_ScalpModeRangeTerkunci = diDalamLorong;
   return g_ScalpModeRangeTerkunci;
}
Gunakan kode dengan hati-hati.

3C. Ganti V24_JagaSiklusReverse() (Kubu Limit Order Agresif + Kubu Stop Order Instan Tanpa Jeda)

Cari fungsi void V24_JagaSiklusReverse() (sekitar baris 2495), lalu ganti seluruh fungsi tersebut dengan blok kode final ini:
mql5
void V24_JagaSiklusReverse()
{
   if(!ScalpReverseAktif || ModeOperasi != AUTO_TRADE || g_TargetMenungguTutup)
   {
      HapusSemuaPendingReverseScalp(); HapusPendingInitScalp(); return;
   }
   MqlTick tick;
   if(!SymbolInfoTick(SymbolKerja,tick) || tick.bid<=0.0 || tick.ask<=0.0) return;
   DS_CatatTick(tick.bid,(double)SymbolInfoInteger(SymbolKerja,SYMBOL_SPREAD));
   if(DS_SpreadShock()) return;

   datetime nowJ=TimeTradeServer(); if(nowJ<=0) nowJ=TimeCurrent();
   bool newsOK=NewsFilterBolehLanjut(), modeNewsVIP=false;
   if(newsOK) g_SpikeDetectedTime=0;
   else if(g_NewsModeVIP==1 && g_NewsEventTime>0 && nowJ>=g_NewsEventTime-15 && nowJ<=g_NewsEventTime+60) modeNewsVIP=true;
   else if(g_NewsModeVIP==2 && g_NewsEventTime>0 && nowJ>g_NewsEventTime)
   {
      double rngM1=iHigh(SymbolKerja,PERIOD_M1,0)-iLow(SymbolKerja,PERIOD_M1,0);
      if(rngM1>=V24_Pip(25.0) && g_SpikeDetectedTime==0) g_SpikeDetectedTime=nowJ;
      if(g_SpikeDetectedTime>0 && nowJ>=g_SpikeDetectedTime+3) modeNewsVIP=true;
   }
   if(!newsOK && !modeNewsVIP) { HapusPendingInitScalp(); return; }

   int limSpread=(ScalpSpreadMaxPoints>0?(int)MathMin((double)ScalpSpreadMaxPoints*V24_SpreadScale(),(double)SpreadMaxPoints):SpreadMaxPoints);
   if((int)SymbolInfoInteger(SymbolKerja,SYMBOL_SPREAD)>limSpread) { HapusPendingInitScalp(); return; }

   {
      double balR=AccountInfoDouble(ACCOUNT_BALANCE), rl=HitungProfitRealisasiEASejak(AwalHariServer());
      double baseD=(MetrikAwalHariEA>0.0?MetrikAwalHariEA:balR);
      double limitMoney=baseD*MathMin(DailyLossLimitPct,MaxDailyLossPct)/100.0;
      if(rl!=EMPTY_VALUE && rl<0.0 && -rl>=limitMoney) { HapusPendingInitScalp(); return; }
      if(g_VaultLockedUSD>0.0 && V24_ProfitHarian()<=g_VaultLockedUSD) { HapusPendingInitScalp(); return; }
      double br=HitungRisikoTerbukaEA();
      if(balR>0.0 && br>=0.0 && (br/balR*100.0)>=MaxRiskPerBasketPct) { HapusPendingInitScalp(); return; }
   }

   bool konteksM1=MS_SiapkanKonteksM1(); if(!konteksM1 || gM1n<25) return;
   DS_EvaluasiCuacaPasar();
   bool sedangRange=MS_M1SedangRange();
   double pt=SymbolInfoDouble(SymbolKerja,SYMBOL_POINT);
   double stl=(double)MathMax(SymbolInfoInteger(SymbolKerja,SYMBOL_TRADE_STOPS_LEVEL),SymbolInfoInteger(SymbolKerja,SYMBOL_TRADE_FREEZE_LEVEL))*pt;

   int adaPosisiScalp=0;
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong tk=PositionGetTicket(i);
      if(tk>0 && PositionGetString(POSITION_SYMBOL)==SymbolKerja && (ulong)PositionGetInteger(POSITION_MAGIC)==MagicNumber && StringFind(PositionGetString(POSITION_COMMENT),"|S=5|")>=0) adaPosisiScalp++;
   }
   if(adaPosisiScalp>0) { HapusPendingInitScalp(); return; }

   double upPress=50.0; int t3s=0,tPrev=0; DS_AnalisaOrderFlow(upPress,t3s,tPrev);
   bool tickExhaustion=(tPrev>=8 && t3s<=4);
   double rsiArr[]; ArraySetAsSeries(rsiArr,true); int ix1=IndexTimeframe(PERIOD_M1); double rsi1=50.0;
   if(ix1>=0 && CopyBuffer(rsiHandles[ix1],0,1,1,rsiArr)==1) rsi1=rsiArr[0];

   datetime tNow=iTime(SymbolKerja,PERIOD_M1,0);
   double garisAtas=0.0, garisBawah=0.0;
   if(g_TL_M1.valid)
   {
      garisAtas=TL_HargaPadaWaktu(g_TL_M1.tA1,g_TL_M1.pA1,g_TL_M1.tA2,g_TL_M1.pA2,tNow);
      garisBawah=TL_HargaPadaWaktu(g_TL_M1.tB1,g_TL_M1.pB1,g_TL_M1.tB2,g_TL_M1.pB2,tNow);
   }
   else
   {
      garisAtas=MS_MaxHigh(gM1,gM1n,1,15);
      garisBawah=MS_MinLow(gM1,gM1n,1,15);
   }

   // =========================================================================
   // KUBU 1: RANGE & CHAOS NGANTUK -> DUAL-LIMIT + PING-PONG INSTAN
   // =========================================================================
   if(sedangRange && !modeNewsVIP && (garisAtas - garisBawah >= V24_Pip(8.0)))
   {
      HapusSemuaPendingReverseScalp();
      double lebarKotak = garisAtas - garisBawah;
      double spr = tick.ask - tick.bid;

      // SL adaptif mengikuti cuaca: Chaos Ngantuk lebih rapat (6-10 pips), Range normal (10-15 pips)
      double slPipsAdaptif = (g_MarketChaosNgantuk ? MathMax(6.0, MathMin(10.0, (lebarKotak / g_pip) * 0.75))
                                                   : MathMax(10.0, MathMin(15.0, (lebarKotak / g_pip) * 0.85)));
      double slDistL = MathMax(V24_Pip(slPipsAdaptif), stl + 2.0 * pt);

      double bufJemput = V24_Pip(1.5) + spr;
      double buyLim1  = AlignHargaTick(garisBawah + bufJemput, true);
      double buyLim2  = AlignHargaTick(garisBawah - V24_Pip(3.5), true);
      double sellLim1 = AlignHargaTick(garisAtas - bufJemput, false);
      double sellLim2 = AlignHargaTick(garisAtas + V24_Pip(3.5), false);

      // TP diletakkan dekat lawan arah Limit Order (1.5 pips di depan Limit lawan)
      double tpBuyL  = AlignHargaTick(sellLim1 - V24_Pip(1.5), false);
      double tpSellL = AlignHargaTick(buyLim1 + V24_Pip(1.5), true);
      double slBuyL  = AlignHargaTick(buyLim2 - slDistL, false);
      double slSellL = AlignHargaTick(sellLim2 + slDistL, true);

      // 1) Tembakan Instan Ping-Pong saat harga menyentuh tepi saluran & mulai berbalik
      double low0=iLow(SymbolKerja,PERIOD_M1,0), high0=iHigh(SymbolKerja,PERIOD_M1,0), open0=iOpen(SymbolKerja,PERIOD_M1,0);
      int buktiBuy=1;  if(DS_DekatAngkaPsikologis(garisBawah)) buktiBuy++;  if(rsi1<=38.0) buktiBuy++; if(tickExhaustion) buktiBuy++; if(upPress>=55.0) buktiBuy++;
      int buktiSell=1; if(DS_DekatAngkaPsikologis(garisAtas)) buktiSell++;  if(rsi1>=62.0) buktiSell++; if(tickExhaustion) buktiSell++; if(upPress<=45.0) buktiSell++;

      static datetime lastInstanRange=0;
      if(TimeCurrent()-lastInstanRange>=2)
      {
         if(buktiBuy>=2 && low0<=garisBawah+V24_Pip(2.0) && tick.bid>open0 && upPress>=55.0)
         {
            double slB=AlignHargaTick(MathMin(low0,garisBawah)-slDistL*0.5,false);
            if(tick.ask-slB<V24_Pip(6.0)) slB=AlignHargaTick(tick.ask-V24_Pip(6.0),false);
            double volB=0.0; string infB="";
            if(V24_Lot(true,tick.ask,slB,5,volB,infB) && tpBuyL>tick.ask+stl && HitungPosisiEA()<MaxPosisiEA && DS_RisikoBasketLolos(true,volB,tick.ask,slB))
            {
               if(trade.Buy(volB,SymbolKerja,0.0,slB,tpBuyL,"PINGPONG_B|S=5|0"))
               { lastInstanRange=TimeCurrent(); HapusPendingInitScalp(); return; }
            }
         }
         if(buktiSell>=2 && high0>=garisAtas-V24_Pip(2.0) && tick.bid<open0 && upPress<=45.0)
         {
            double slS=AlignHargaTick(MathMax(high0,garisAtas)+slDistL*0.5,true);
            if(slS-tick.bid<V24_Pip(6.0)) slS=AlignHargaTick(tick.bid+V24_Pip(6.0),true);
            double volS=0.0; string infS="";
            if(V24_Lot(false,tick.bid,slS,5,volS,infS) && tpSellL<tick.bid-stl && HitungPosisiEA()<MaxPosisiEA && DS_RisikoBasketLolos(false,volS,tick.bid,slS))
            {
               if(trade.Sell(volS,SymbolKerja,0.0,slS,tpSellL,"PINGPONG_S|S=5|0"))
               { lastInstanRange=TimeCurrent(); HapusPendingInitScalp(); return; }
            }
         }
      }

      // 2) Pemasangan & Auto-Sync 2 Lapis Dual-Limit mengikuti garis Trendline
      if(sellLim1 - buyLim1 < V24_Pip(6.0)) return;
      datetime nowS=TimeTradeServer(); if(nowS<=0) nowS=TimeCurrent();
      ulong tkBL1=0,tkBL2=0,tkSL1=0,tkSL2=0;
      for(int js=OrdersTotal()-1;js>=0;js--)
      {
         ulong ots=OrderGetTicket(js);
         if(ots==0 || OrderGetString(ORDER_SYMBOL)!=SymbolKerja || (ulong)OrderGetInteger(ORDER_MAGIC)!=MagicNumber) continue;
         string cms=OrderGetString(ORDER_COMMENT);
         if(nowS-(datetime)OrderGetInteger(ORDER_TIME_SETUP)>=600 && StringFind(cms,"REV_INIT_")==0) { trade.OrderDelete(ots); continue; }
         if(cms=="REV_INIT_BL|S=5|0") { tkBL1=ots; if(MathAbs(OrderGetDouble(ORDER_PRICE_OPEN)-buyLim1)>=V24_Pip(2.0)) trade.OrderModify(ots,buyLim1,slBuyL,tpBuyL,ORDER_TIME_GTC,0); }
         if(cms=="REV_INIT_BL|S=5|1") { tkBL2=ots; if(MathAbs(OrderGetDouble(ORDER_PRICE_OPEN)-buyLim2)>=V24_Pip(2.0)) trade.OrderModify(ots,buyLim2,slBuyL,tpBuyL,ORDER_TIME_GTC,0); }
         if(cms=="REV_INIT_SL|S=5|0") { tkSL1=ots; if(MathAbs(OrderGetDouble(ORDER_PRICE_OPEN)-sellLim1)>=V24_Pip(2.0)) trade.OrderModify(ots,sellLim1,slSellL,tpSellL,ORDER_TIME_GTC,0); }
         if(cms=="REV_INIT_SL|S=5|1") { tkSL2=ots; if(MathAbs(OrderGetDouble(ORDER_PRICE_OPEN)-sellLim2)>=V24_Pip(2.0)) trade.OrderModify(ots,sellLim2,slSellL,tpSellL,ORDER_TIME_GTC,0); }
      }

      double volL=0.0; string infoL=""; if(!V24_Lot(true,buyLim1,slBuyL,5,volL,infoL)) return;
      double volHalf=NormalisasiVolumeBawah(volL*0.5); if(volHalf<SymbolInfoDouble(SymbolKerja,SYMBOL_VOLUME_MIN)) volHalf=volL;
      if(HitungPosisiEA()+2>MaxPosisiEA) return;
      if(tkBL1==0 && buyLim1<tick.ask-stl-pt && DS_RisikoBasketLolos(true,volHalf,buyLim1,slBuyL)) trade.BuyLimit(volHalf,buyLim1,SymbolKerja,slBuyL,tpBuyL,ORDER_TIME_GTC,0,"REV_INIT_BL|S=5|0");
      if(tkBL2==0 && buyLim2<tick.ask-stl-pt && DS_RisikoBasketLolos(true,volHalf,buyLim2,slBuyL)) trade.BuyLimit(volHalf,buyLim2,SymbolKerja,slBuyL,tpBuyL,ORDER_TIME_GTC,0,"REV_INIT_BL|S=5|1");
      if(tkSL1==0 && sellLim1>tick.bid+stl+pt && DS_RisikoBasketLolos(false,volHalf,sellLim1,slSellL)) trade.SellLimit(volHalf,sellLim1,SymbolKerja,slSellL,tpSellL,ORDER_TIME_GTC,0,"REV_INIT_SL|S=5|0");
      if(tkSL2==0 && sellLim2>tick.bid+stl+pt && DS_RisikoBasketLolos(false,volHalf,sellLim2,slSellL)) trade.SellLimit(volHalf,sellLim2,SymbolKerja,slSellL,tpSellL,ORDER_TIME_GTC,0,"REV_INIT_SL|S=5|1");
      return;
   }

   // =========================================================================
   // KUBU 2: TRENDING, CHAOS NGAMUK, SQUEEZE, & VIP NEWS -> ENTRY INSTAN TANPA JEDA
   // =========================================================================
   HapusPendingInitScalp();
   double ema8=MS_EMA(PERIOD_M1,8,0), ema21=MS_EMA(PERIOD_M1,21,0); if(ema8<=0.0 || ema21<=0.0) return;
   int dirM5=MS_DirM5();
   bool arahBuy =(ema8>ema21 && (modeNewsVIP || g_MarketChaos || dirM5>=0) && tick.ask>gM1[1].high && upPress>=55.0);
Gunakan kode dengan hati-hati.
bool arahSell=(ema8<ema21 && (modeNewsVIP || g_MarketChaos || dirM5<=0) && tick.bid<gM1[1].low  && upPress<=45.0);
if(!arahBuy && !arahSell) return;
bool bull=arahBuy;
double entry=(bull?tick.ask:tick.bid);
double jarakSL=MathMax(V24_Pip(ScalpSLMinPips),stl+2.0*pt);
double sl=AlignHargaTick(bull?entry-jarakSL:entry+jarakSL,!bull);
double vol=0.0; string info=""; if(!V24_Lot(bull,entry,sl,5,vol,info)) return;
int jumlah=MathMax(1,ScalpMaxPosisi); // 2 posisi instan tanpa TP
if(!DS_RisikoBasketLolos(bull,vol*jumlah,entry,sl)) return;
if(HitungPosisiEA()+jumlah>MaxPosisiEA) return;
int berhasil=0;
for(int k=0;k<jumlah;k++)
{
bool ok=(bull?trade.Buy(vol,SymbolKerja,0.0,sl,0.0,"VIP_STOP|S=5|"+IntegerToString(k))
:trade.Sell(vol,SymbolKerja,0.0,sl,0.0,"VIP_STOP|S=5|"+IntegerToString(k)));
if(ok)
{
berhasil++; long pid=0; ulong d=trade.ResultDeal();
if(d>0 && HistoryDealSelect(d)) pid=HistoryDealGetInteger(d,DEAL_POSITION_ID);
if(pid==0) pid=(long)trade.ResultOrder();
if(pid>0) { string sp=IntegerToString(pid); SimpanGV("SR"+sp,jarakSL); SimpanGV("SB"+sp,0.0); SimpanGV("SV"+sp,vol); }
}
}
if(berhasil>0)
Print("VIP_STOP_INSTAN | ",(bull?"BUY":"SELL")," ",berhasil,"x lot=",DoubleToString(vol,2)," di ",DoubleToString(entry,_Digits)," SL=",DoubleToString(sl,_Digits));
}

---

#### 3D. Aktifkan *Reverse Stop* Tanpa Henti di `V24_KelolaSemua()` & `EksekusiCadanganSLKeseret()`
Agar **Stop Order selalu menempel di garis SL biasa & SL+ tanpa batas *flip* dan tanpa jeda** (kecuali saat masuk *Range* atau *Chaos Ngantuk*):

1. Cari bagian bawah fungsi `void V24_KelolaSemua()` (sekitar baris 2675), lalu **ganti bagian sinkronisasi Reverse Stop** menjadi:
   ```mql5
   // Sinkronkan Reverse Stop Order pada SL biasa maupun SL+ gelombang scalping (TANPA HENTI selama bukan Range/Chaos Ngantuk)
   int dW=-1;
   if(scCnt[1]>0 && scCnt[0]>0) dW=(scT[1]>=scT[0] ? 1 : 0);
   else if(scCnt[1]>0)          dW=1;
   else if(scCnt[0]>0)          dW=0;

   bool sedangRangeSekarang = MS_M1SedangRange();

   // Terus tempelkan Order Stop di garis SL/SL+ selama Kubu Stop Order aktif (termasuk VIP News & Chaos Ngamuk)
   if(!sedangRangeSekarang && dW>=0 && scX[dW]>0.0 && adaScalpTanpaTP)
   {
      HapusPendingInitScalp();
      KelolaReverseGelombangScalp((dW==1),scX[dW],scV[dW],scR[dW]);
   }
   else
   {
      HapusSemuaPendingReverseScalp();
   }
2. Di dalam void EksekusiCadanganSLKeseret(...) (sekitar baris 2405), hapus dua baris pengecekan batas flip (double flipNow=0.0... if((int)flipNow>=ScalpMaxFlip) return;) agar sensor anti-SL keseret juga terus menembak cadangan tanpa terhenti oleh batas flip.
Silakan tempel 4 blok Tahap 3 di atas ke MetaEditor Anda. Jika sudah selesai, balas "Lanjut Tahap 4" untuk bagian penutup (Kokpit Dashboard HUD Canggih + Bar Meter Order Flow + Nama Baru 4. VIP Scalp (Limit & Stop) + Pembersihan Objek).
