Berikut adalah panduan lengkap dan presisi baris demi baris berdasarkan file terakhir yang Anda unggah () untuk merakit seluruh fitur yang sudah kita sepakati hingga 100% matang:
1. Jalur VIP Scalping Satu Pintu + Refresh 3 Detik + Pemotongan Posisi 1 di +42 Pips (untuk melunasi 2x SL sambil membiarkan Posisi 2 utuh berlari).
2. Sensor Manipulasi (Stop Hunt Ekor > 55% + RSI Ekstrem) → Otomatis pasang Order Limit di pucuk/ujung ekor.
3. Pemindaian 9 Timeframe Lengkap (M1 sampai MN1) + Pattern Miner (Candle Kejepit, Sweep, OB/FVG) + Koreksi Kedalaman Entry Pasca-SL (Post-SL Watch).
4. Buku Otak Portabel (APlus_Brain_Master.csv) di folder MQL5\Files agar kepintaran EA bisa dipindahkan dari Winlator ke VPS.
5. Mode Sniper Full Margin (FM) + News Spike & NFP (75% Free Margin + Micro-SL 12–15 pips + SL+ kilat di +6 pips).
Aturan Wajib: Lakukan penggantian mulai dari Langkah 1 (paling bawah) naik ke Langkah 7 (paling atas) agar nomor baris bagian atas tidak bergeser saat Anda mengedit di MetaEditor.

LANGKAH 1: Perbarui OnInit() & OnDeinit() (Muat/Simpan Buku Otak Portabel & 9 Timeframe)

• Lokasi A — Baris 2630 – 2641 (di dalam OnInit()):
	• Cari:mql5
   for(int h=0;h<7;h++)
   {
      maHandles[h]=INVALID_HANDLE; rsiHandles[h]=INVALID_HANDLE;
      fractalHandles[h]=INVALID_HANDLE; atrScanHandles[h]=INVALID_HANDLE;
   }
   for(int z=0;z<MAX_ZONA_REGISTRY;z++) { lastZoneStatusCheck[z]=0; zNextEval[z]=0; }
   if(MaxRiskPerBasketPct>10.0) Print("PERINGATAN: MaxRiskPerBasketPct > 10.00% melampaui nilai wajib spesifikasi pengguna.");
   for(int t=0;t<ArraySize(ScanTFs);t++) lastScanBarByTF[t]=0;
Gunakan kode dengan hati-hati.
	• Ganti h<7 menjadi h<9 (karena kita menambah W1 dan MN1 sehingga total 9 timeframe):mql5
   for(int h=0;h<9;h++)
   {
      maHandles[h]=INVALID_HANDLE; rsiHandles[h]=INVALID_HANDLE;
      fractalHandles[h]=INVALID_HANDLE; atrScanHandles[h]=INVALID_HANDLE;
   }
   for(int z=0;z<MAX_ZONA_REGISTRY;z++) { lastZoneStatusCheck[z]=0; zNextEval[z]=0; }
   if(MaxRiskPerBasketPct>10.0) Print("PERINGATAN: MaxRiskPerBasketPct > 10.00% melampaui nilai wajib spesifikasi pengguna.");
   for(int t=0;t<ArraySize(ScanTFs);t++) lastScanBarByTF[t]=0;
Gunakan kode dengan hati-hati.
• Lokasi B — Baris 2714 – 2717 (akhir OnInit()):
	• Cari:mql5
      V24_InitBase(); V24_UpdateEquityState(); V24_CheckBalanceOps();
      Print("V24_INIT | pip=",DoubleToString(g_pip,5)," SaldoUtama=",DoubleToString(V24_BaseBal(),2)," target=",DoubleToString(V24_TargetLevel(),2));
Gunakan kode dengan hati-hati.
	• Ganti menjadi (agar memuat APlus_Brain_Master.csv saat menyala di Winlator/VPS):mql5
      V24_InitBase(); V24_MuatBukuOtak(); V24_UpdateEquityState(); V24_CheckBalanceOps();
      Print("V24_INIT | pip=",DoubleToString(g_pip,5)," SaldoUtama=",DoubleToString(V24_BaseBal(),2)," target=",DoubleToString(V24_TargetLevel(),2));
Gunakan kode dengan hati-hati.
• Lokasi C — Baris 2807 – 2809 (di dalam OnDeinit()):
	• Cari:mql5
   GlobalVariablesFlush();
Gunakan kode dengan hati-hati.
	• Tambahkan tepat di atasnya:mql5
   V24_SimpanBukuOtak();
Gunakan kode dengan hati-hati.

LANGKAH 2: Perbarui V24_JagaSiklusReverse() & V24_KelolaSemua() (VIP Scalping 3 Detik, Sensor Manipulasi, Potong P1 +42 Pips, & Sniper FM)

• Lokasi: Baris 2012 sampai 2295 (Mulai dari void V24_JagaSiklusReverse() hingga akhir void V24_KelolaSemua()).
• Ganti seluruh blok tersebut dengan kode berikut:
mql5
// SIKLUS SCALPING JALUR VIP 24 JAM NON-STOP (3 DETIK REFRESH):
// 1. Manipulasi (Stop Hunt) -> Order Limit di pucuk/ujung ekor
// 2. Sideways / Netral -> Order Limit di atap & lantai kotak (TP 14 pips)
// 3. Trending / Breakout -> Buy Stop + Sell Stop 2 Posisi Tanpa TP (Potong P1 di +42 pips untuk tutup 2x SL, P2 Runner SL+)
void V24_JagaSiklusReverse()
{
   if(!ScalpReverseAktif || ModeOperasi!=AUTO_TRADE || g_TargetMenungguTutup)
   {
      HapusSemuaPendingReverseScalp();
      HapusPendingInitScalp();
      return;
   }

   int adaPosisiScalp = 0;
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(tk>0 && PositionGetString(POSITION_SYMBOL)==SymbolKerja &&
         (ulong)PositionGetInteger(POSITION_MAGIC)==MagicNumber &&
         StringFind(PositionGetString(POSITION_COMMENT), "|S=5|")>=0)
         adaPosisiScalp++;
   }
   if(adaPosisiScalp > 0) return;

   // Refresh pending order setiap 3 detik agar perangkap selalu menempel segar di harga berjalan
   static datetime lastRefresh3s = 0;
   if(TimeCurrent() - lastRefresh3s >= 3)
   {
      lastRefresh3s = TimeCurrent();
      HapusPendingInitScalp();
   }

   MqlTick tick;
   if(!SymbolInfoTick(SymbolKerja, tick) || tick.bid<=0.0) return;

   int limSpread=(ScalpSpreadMaxPoints>0 ? (int)MathMin((double)ScalpSpreadMaxPoints*V24_SpreadScale(),(double)SpreadMaxPoints) : SpreadMaxPoints);
   if((int)SymbolInfoInteger(SymbolKerja,SYMBOL_SPREAD)>limSpread) { HapusPendingInitScalp(); return; }

   // Rem darurat istirahat 3 detik setelah siklus flip selesai
   double tCool=0.0;
   if(V24G_Get("v24FlipCool",tCool) && TimeCurrent()<(datetime)tCool) { HapusPendingInitScalp(); return; }

   double pt  = SymbolInfoDouble(SymbolKerja, SYMBOL_POINT);
   double stl = (double)MathMax(SymbolInfoInteger(SymbolKerja, SYMBOL_TRADE_STOPS_LEVEL),
                                SymbolInfoInteger(SymbolKerja, SYMBOL_TRADE_FREEZE_LEVEL)) * pt;

   bool konteksM1 = MS_SiapkanKonteksM1();
   bool manipulasiAtas = false, manipulasiBawah = false;
   if(konteksM1 && gM1n >= 5)
   {
      double rng1 = gM1[1].high - gM1[1].low;
      if(rng1 > 0.0)
      {
         double upWick = gM1[1].high - MathMax(gM1[1].open, gM1[1].close);
         double dnWick = MathMin(gM1[1].open, gM1[1].close) - gM1[1].low;
         if(upWick / rng1 >= 0.55) manipulasiAtas = true;
         if(dnWick / rng1 >= 0.55) manipulasiBawah = true;
      }
   }

   bool modeRange = (!konteksM1 || MS_M1SedangRange() || manipulasiAtas || manipulasiBawah);

   // --- MODE 2 & MODE MANIPULASI: ORDER LIMIT DI PUCUK / UJUNG / BATAS KOTAK ---
   if(modeRange)
   {
      for(int j=OrdersTotal()-1; j>=0; j--)
      {
         ulong otk = OrderGetTicket(j);
         if(otk>0 && OrderGetString(ORDER_SYMBOL)==SymbolKerja && (ulong)OrderGetInteger(ORDER_MAGIC)==MagicNumber)
         {
            ENUM_ORDER_TYPE ty=(ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE);
            if(ty==ORDER_TYPE_BUY_STOP || ty==ORDER_TYPE_SELL_STOP) trade.OrderDelete(otk);
         }
      }

      double atap   = (manipulasiAtas  ? gM1[1].high : MS_MaxHigh(gM1, gM1n, 1, 30));
      double lantai = (manipulasiBawah ? gM1[1].low  : MS_MinLow(gM1, gM1n, 1, 30));
      if(atap<=lantai || (atap-lantai)<V24_Pip(18.0)) return;

      double slDist = MathMax(V24_Pip(manipulasiAtas || manipulasiBawah ? 16.0 : ScalpSLMinPips), stl + 2.0*pt);
      double tpDist = V24_Pip(manipulasiAtas || manipulasiBawah ? 20.0 : 14.0);

      double buyLim  = AlignHargaTick(lantai + V24_Pip(1.0), true);
      double slBuyL  = AlignHargaTick(buyLim - slDist, false);
      double tpBuyL  = AlignHargaTick(buyLim + tpDist, true);
      double sellLim = AlignHargaTick(atap - V24_Pip(1.0), false);
      double slSellL = AlignHargaTick(sellLim + slDist, true);
      double tpSellL = AlignHargaTick(sellLim - tpDist, false);

      bool adaBuyLim=false, adaSellLim=false;
      for(int j2=OrdersTotal()-1; j2>=0; j2--)
      {
         ulong otk2 = OrderGetTicket(j2);
         if(otk2>0 && OrderGetString(ORDER_SYMBOL)==SymbolKerja && (ulong)OrderGetInteger(ORDER_MAGIC)==MagicNumber)
         {
            string cm=OrderGetString(ORDER_COMMENT);
            if(StringFind(cm,"REV_INIT_BL")==0) adaBuyLim=true;
            if(StringFind(cm,"REV_INIT_SL")==0) adaSellLim=true;
         }
      }
      if(adaBuyLim && adaSellLim) return;

      double volL=0.0; string infoL="";
      if(!V24_Lot(true, buyLim, slBuyL, 5, volL, infoL)) return;
      if(HitungPosisiEA()+1>MaxPosisiEA) return;

      if(!adaBuyLim && buyLim < tick.ask - stl - pt)
         trade.BuyLimit(volL, buyLim, SymbolKerja, slBuyL, tpBuyL, ORDER_TIME_GTC, 0, "REV_INIT_BL_|S=5|_0");
      if(!adaSellLim && sellLim > tick.bid + stl + pt)
         trade.SellLimit(volL, sellLim, SymbolKerja, slSellL, tpSellL, ORDER_TIME_GTC, 0, "REV_INIT_SL_|S=5|_0");
      return;
   }

   // --- MODE 1: ORDER STOP 2 ARAH TANPA TP (POTONG P1 DI +42 PIPS, P2 RUNNER) ---
   for(int j3=OrdersTotal()-1; j3>=0; j3--)
   {
      ulong otk3 = OrderGetTicket(j3);
      if(otk3>0 && OrderGetString(ORDER_SYMBOL)==SymbolKerja && (ulong)OrderGetInteger(ORDER_MAGIC)==MagicNumber)
      {
         ENUM_ORDER_TYPE ty3=(ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE);
         if(ty3==ORDER_TYPE_BUY_LIMIT || ty3==ORDER_TYPE_SELL_LIMIT) trade.OrderDelete(otk3);
      }
   }

   double jarakStop = MathMax(V24_Pip(16.0), stl + 2.0*pt);
   double jarakSL   = MathMax(V24_Pip(ScalpSLMinPips), stl + 2.0*pt);

   double hargaBuyStop  = AlignHargaTick(tick.ask + jarakStop, true);
   double slBuyStop     = AlignHargaTick(hargaBuyStop - jarakSL, false);
   double hargaSellStop = AlignHargaTick(tick.bid - jarakStop, false);
   double slSellStop    = AlignHargaTick(hargaSellStop + jarakSL, true);

   double vol=0.0; string info="";
   if(!V24_Lot(true, hargaBuyStop, slBuyStop, 5, vol, info)) return;

   int jumlah = MathMax(1, ScalpMaxPosisi); // Jalur VIP selalu konsisten 2 posisi
   bool adaBuyStop=false, adaSellStop=false;
   for(int j4=OrdersTotal()-1; j4>=0; j4--)
   {
      ulong otk4 = OrderGetTicket(j4);
      if(otk4>0 && OrderGetString(ORDER_SYMBOL)==SymbolKerja && (ulong)OrderGetInteger(ORDER_MAGIC)==MagicNumber)
      {
         string cm4=OrderGetString(ORDER_COMMENT);
         if(StringFind(cm4,"REV_INIT_B_")==0) adaBuyStop=true;
         if(StringFind(cm4,"REV_INIT_S_")==0) adaSellStop=true;
      }
   }
   if(adaBuyStop && adaSellStop) return;
   if(HitungPosisiEA()+jumlah>MaxPosisiEA) return;

   for(int k=0; k<jumlah; k++)
   {
      // Kedua posisi dipasang TANPA TP (0.0); Posisi 1 (k==0) akan dipotong otomatis di +42 pips untuk melunasi 2x SL
      if(!adaBuyStop)
         trade.BuyStop(vol, hargaBuyStop, SymbolKerja, slBuyStop, 0.0, ORDER_TIME_GTC, 0, "REV_INIT_B_|S=5|_" + IntegerToString(k));
      if(!adaSellStop)
         trade.SellStop(vol, hargaSellStop, SymbolKerja, slSellStop, 0.0, ORDER_TIME_GTC, 0, "REV_INIT_S_|S=5|_" + IntegerToString(k));
   }
}

void V24_KelolaSemua()
{
   MqlTick tick; if(!SymbolInfoTick(SymbolKerja,tick) || tick.bid<=0.0) return;
   double point=SymbolInfoDouble(SymbolKerja,SYMBOL_POINT); int digits=(int)SymbolInfoInteger(SymbolKerja,SYMBOL_DIGITS);
   double dmin=(double)MathMax(SymbolInfoInteger(SymbolKerja,SYMBOL_TRADE_STOPS_LEVEL),SymbolInfoInteger(SymbolKerja,SYMBOL_TRADE_FREEZE_LEVEL))*point;
   double minLot=SymbolInfoDouble(SymbolKerja,SYMBOL_VOLUME_MIN);
   double comm=MS_KomisiJarak(), nilai=MS_NilaiPerHarga();

   int scCnt[2]={0,0}; double scV[2]={0.0,0.0}, scX[2]={0.0,0.0}, scR[2]={0.0,0.0}; datetime scT[2]={0,0};
   bool adaScalpTanpaTP=false;

   // Hitung jumlah posisi scalping aktif per arah untuk aturan "Potong 1 Posisi di +42 Pips"
   int totalScalpBuy = 0, totalScalpSell = 0;
   for(int cIdx=PositionsTotal()-1; cIdx>=0; cIdx--)
   {
      ulong ctk = PositionGetTicket(cIdx);
      if(ctk>0 && PositionGetString(POSITION_SYMBOL)==SymbolKerja && (ulong)PositionGetInteger(POSITION_MAGIC)==MagicNumber &&
         StringFind(PositionGetString(POSITION_COMMENT),"|S=5|")>=0 && PositionGetDouble(POSITION_TP)==0.0)
      {
         if((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY) totalScalpBuy++;
         else totalScalpSell++;
      }
   }

   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong tk=PositionGetTicket(i); if(tk==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=SymbolKerja || (ulong)PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      string cm=PositionGetString(POSITION_COMMENT);
      bool scalp=(StringFind(cm,"|S=5|")>=0);
      bool isFM =(StringFind(cm,"|FM=1|")>=0);
      long pid=PositionGetInteger(POSITION_IDENTIFIER); string sp=IntegerToString(pid);
      bool buy=((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY);
      double opn=PositionGetDouble(POSITION_PRICE_OPEN), sl=PositionGetDouble(POSITION_SL), tp=PositionGetDouble(POSITION_TP);
      double vol=PositionGetDouble(POSITION_VOLUME), swap=PositionGetDouble(POSITION_SWAP);
      double rd=0.0;
      if(!BacaGV("SR"+sp,rd) || rd<=0.0) { if(sl<=0.0) continue; rd=MathAbs(opn-sl); SimpanGV("SR"+sp,rd); }
      double px=buy?tick.bid:tick.ask;
      double R=((buy?px-opn:opn-px)/rd);
      double sb=0.0; BacaGV("SB"+sp,sb); int bits=(int)sb;
      bool sudahSLPlus = (sl > 0.0 && (buy ? sl > opn : sl < opn));

      if(scalp && !sudahSLPlus && TimeCurrent()-(datetime)PositionGetInteger(POSITION_TIME)>=ScalpMaxHoldMenit*60)
      { if(ThrottleKey((ulong)pid*8+6,5) && trade.PositionClose(tk)) Print("V24_TIMESTOP scalp pos=",pid); continue; }

      if(scalp)
      {
         double profitPips=(buy ? (px-opn) : (opn-px))/g_pip;
         double slPipsAwal = rd / g_pip;

         // ATURAN PEMOTONGAN PROFIT VIP: Jika ada 2 posisi tanpa TP berjalan & profit menyentuh >= 2.1x SL (~42 pips),
         // potong 1 posisi penuh untuk menutup nilai rugi 2 posisi SL, biarkan 1 posisi sisanya utuh jadi runner!
Gunakan kode dengan hati-hati.
if(tp == 0.0 && ((buy && totalScalpBuy >= 2) || (!buy && totalScalpSell >= 2)) && profitPips >= slPipsAwal * 2.1)
{
if(ModifikasiDiizinkan() && trade.PositionClose(tk))
{
if(buy) totalScalpBuy--; else totalScalpSell--;
Print("VIP_SCALP_CUT_1_POS | pos=", pid, " ditutup di +", DoubleToString(profitPips, 1),
" pips (melunasi 2x SL), 1 posisi sisanya dibiarkan utuh berlari!");
continue;
}
}
double slTerbaru=sl;
double trigPips =(tp>0.0 ? 8.0 : ScalpMulaiSLPlusPips);
double kunciPips=(tp>0.0 ? 2.0 : ScalpKunciAwalPips);
if(profitPips>=trigPips)
{
double slAwalPlus=buy ? (opn+V24_Pip(kunciPips)) : (opn-V24_Pip(kunciPips));
double slTrail=(tp>0.0 ? slAwalPlus : (buy ? (px-V24_Pip(ScalpTrailingPips)) : (px+V24_Pip(ScalpTrailingPips))));
double targetSL=buy ? MathMax(slAwalPlus,slTrail) : MathMin(slAwalPlus,slTrail);
targetSL=AlignHargaTick(targetSL,buy);
bool lebihBaik=(sl<=0.0 || (buy ? targetSL>sl+point : targetSL<sl-point));
bool jarakAman=(buy ? targetSL<=px-dmin : targetSL>=px+dmin);
if(lebihBaik && jarakAman && ModifikasiDiizinkan())
{
if(trade.PositionModify(tk,targetSL,tp)) slTerbaru=targetSL;
}
}
if(tp==0.0) adaScalpTanpaTP=true;
int dI=(buy?1:0);
datetime tOpen=0; if(PositionSelectByTicket(tk)) tOpen=(datetime)PositionGetInteger(POSITION_TIME);
scCnt[dI]++; scV[dI]+=vol; scR[dI]=rd;
if(tOpen>scT[dI]) scT[dI]=tOpen;
if(slTerbaru>0.0)
{
if(scX[dI]==0.0) scX[dI]=slTerbaru;
else scX[dI]=(buy ? MathMax(scX[dI],slTerbaru) : MathMin(scX[dI],slTerbaru));
}
continue;
}
// --- STRATEGI UTAMA (SNIPER & FULL MARGIN): TP DINAMIS + SL+ KILAT ---
if(!scalp && UtamaSLPlusAktif)
{
double profitPipsUtama = (buy ? (px - opn) : (opn - px)) / g_pip;
// TP dinamis: TP hampir kena & sudah profit cukup -> majukan TP +25 pips beruntun
double mulaiTrig = (isFM ? 6.0 : UtamaMulaiSLPlusPips);
double kunciAwal = (isFM ? 2.0 : UtamaKunciAwalPips);
double trailDist = (isFM ? 10.0 : UtamaTrailingPips);
if(tp>0.0 && MathAbs(tp-px)<=V24_Pip(10.0) && profitPipsUtama>=mulaiTrig)
{
double tpBaru=AlignHargaTick(buy ? tp+V24_Pip(25.0) : tp-V24_Pip(25.0), buy);
if(JarakStopValid(buy,tpBaru) && ModifikasiDiizinkan())
{
if(trade.PositionModify(tk,sl,tpBaru))
{
tp=tpBaru;
Print("SNIPER_TP_EXTEND | pos=",pid," TP dimajukan +25 pips ke ",DoubleToString(tpBaru,digits));
}
}
}
if(profitPipsUtama >= mulaiTrig)
{
double slAwalPlusU = buy ? (opn + V24_Pip(kunciAwal)) : (opn - V24_Pip(kunciAwal));
double slTrailU    = buy ? (px - V24_Pip(trailDist))  : (px + V24_Pip(trailDist));
double targetSLU   = buy ? MathMax(slAwalPlusU, slTrailU) : MathMin(slAwalPlusU, slTrailU);
targetSLU          = AlignHargaTick(targetSLU, buy);
bool lebihBaikU = (sl <= 0.0 || (buy ? targetSLU > sl + point : targetSLU < sl - point));
bool jarakAmanU = (buy ? targetSLU <= px - dmin : targetSLU >= px + dmin);
if(lebihBaikU && jarakAmanU && ModifikasiDiizinkan())
{
if(trade.PositionModify(tk, targetSLU, tp))
{
sl = targetSLU;
Print((isFM ? "FM_SL+_KILAT | pos=" : "UTAMA_SL+_OK | pos="), pid,
" Profit=", DoubleToString(profitPipsUtama, 1), " pips | SL+ -> ", DoubleToString(targetSLU, digits));
}
}
}
}
// Partial 50% pada RR 1.5 untuk strategi utama (non-FM)
if(!isFM && (bits&1)==0 && MSPartialR>0.0 && MSPartialPct>0.0 && R>=MSPartialR)
{
double cv=NormalisasiVolumeBawah(vol*MSPartialPct/100.0);
if(cv>=minLot-1e-9 && vol-cv>=minLot-1e-9 && ModifikasiDiizinkan())
{
bool ok=(AkunNetting()?trade.PositionClosePartial(SymbolKerja,cv):trade.PositionClosePartial(tk,cv));
uint rc=trade.ResultRetcode();
if(ok && (rc==TRADE_RETCODE_DONE||rc==TRADE_RETCODE_DONE_PARTIAL)){ bits|=1; SimpanGV("SB"+sp,(double)bits); }
}
}
}
int dW=-1;
if(scCnt[1]>0 && scCnt[0]>0) dW=(scT[1]>=scT[0] ? 1 : 0);
else if(scCnt[1]>0)          dW=1;
else if(scCnt[0]>0)          dW=0;
double flipNow=0.0; V24G_Get("v24Flip",flipNow);
if(dW>=0 && scX[dW]>0.0 && adaScalpTanpaTP && (int)flipNow<ScalpMaxFlip)
{
HapusPendingInitScalp();
KelolaReverseGelombangScalp((dW==1),scX[dW],scV[dW],scR[dW]);
}
else
{
HapusSemuaPendingReverseScalp();
if((int)flipNow>=ScalpMaxFlip && dW<0)
{
V24G_Set("v24Flip",0.0);
V24G_Set("v24FlipCool",(double)(TimeCurrent()+3)); // Jeda 3 detik lalu langsung lanjut!
Print("REM_DARURAT_3_DETIK | Batas flip tercapai, jeda 3 detik lalu lanjut.");
}
}
}

---

### LANGKAH 3: Tambahkan Buku Otak Portabel (`APlus_Brain_Master.csv`) & Mode Full Margin (FM) di `V24_Lot()`
* **Lokasi:** **Baris 1859 sampai 1916** (Fungsi `V24_Lot()`).
* **Ganti fungsi `V24_Lot()` dengan kode berikut** (sudah dilengkapi penyimpanan/pemuatan file portabel `APlus_Brain_Master.csv` untuk Winlator ↔ VPS, dukungan **Full Margin 75% Free Margin** saat `isFullMargin = true`, serta belajar sambil jalan tanpa menahan order):

```mql5
void V24_SimpanBukuOtak()
{
   int h = FileOpen("APlus_Brain_Master.csv", FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(h == INVALID_HANDLE) return;
   FileWriteString(h, "BASE;" + DoubleToString(V24_BaseBal(), 2) + ";" + DoubleToString(V24_TargetStep(), 2) + "\r\n");
   FileWriteString(h, "DEPTH;" + DoubleToString(g_SniperDepthPct, 3) + "\r\n");
   string scLine = "SCORE";
   for(int i=0; i<6; i++) scLine += ";" + DoubleToString(g_LearnScore[i], 2);
   FileWriteString(h, scLine + "\r\n");
   string jamLine = "JAM";
   for(int j=0; j<24; j++) jamLine += ";" + IntegerToString(g_JamRawan[j]);
   FileWriteString(h, jamLine + "\r\n");
   FileClose(h);
}

void V24_MuatBukuOtak()
{
   int h = FileOpen("APlus_Brain_Master.csv", FILE_READ|FILE_TXT|FILE_ANSI);
   if(h == INVALID_HANDLE) return;
   while(!FileIsEnding(h))
   {
      string ln = FileReadString(h);
      StringTrimLeft(ln); StringTrimRight(ln);
      string p[]; int n = StringSplit(ln, ';', p);
      if(n < 2) continue;
      if(p[0] == "DEPTH") g_SniperDepthPct = MathMax(0.25, MathMin(0.80, StringToDouble(p[1])));
      else if(p[0] == "SCORE" && n >= 7)
      {
         for(int i=0; i<6; i++) g_LearnScore[i] = MathMax(45.0, MathMin(100.0, StringToDouble(p[i+1])));
      }
      else if(p[0] == "JAM" && n >= 25)
      {
         for(int j=0; j<24; j++) g_JamRawan[j] = (int)StringToInteger(p[j+1]);
      }
   }
   FileClose(h);
   Print("BRAIN_LOADED | Buku Otak APlus_Brain_Master.csv berhasil dipulihkan! SniperDepth=", DoubleToString(g_SniperDepthPct*100.0, 0), "%");
}

bool V24_Lot(bool bull, double entry, double sl, int cat, double &vol, string &info, int stratIdx, bool isFullMargin)
{
   vol = 0.0; info = "";
   double bal = AccountInfoDouble(ACCOUNT_BALANCE);
   if(bal <= 0.0) { info = "balance<=0"; return false; }

   double mn = SymbolInfoDouble(SymbolKerja, SYMBOL_VOLUME_MIN);
   double mx = SymbolInfoDouble(SymbolKerja, SYMBOL_VOLUME_MAX);
   double st = SymbolInfoDouble(SymbolKerja, SYMBOL_VOLUME_STEP);
   if(st <= 0.0 || mn <= 0.0) { info = "spesifikasi volume broker tidak valid"; return false; }

   ENUM_ORDER_TYPE oty = (bull ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   int vd = (int)MathMax(0.0, MathRound(-MathLog10(st)));

   // MODE FULL MARGIN (FM): Dipakai khusus pantulan raksasa H1/H4/W1/MN1 atau News Spike/NFP
   if(isFullMargin)
   {
      double freeM = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
      double m1Lot = 0.0;
      if(!OrderCalcMargin(oty, SymbolKerja, 1.0, entry, m1Lot) || m1Lot <= 0.0) { info = "margin FM gagal"; return false; }
      double rawFM = (freeM * 0.75) / m1Lot; // Gunakan 75% Free Margin, sisakan 25% cadangan anti-StopOut
      double vFM = NormalizeDouble(MathFloor(rawFM / st + 1e-9) * st, vd);
      vFM = MathMax(mn, MathMin(mx, vFM));
      if(!ValidasiVolumeOrder(vFM)) { info = "vol FM invalid"; return false; }
      vol = vFM;
      info = "FULL_MARGIN_75% FreeMargin=" + DoubleToString(freeM, 0) + " Lot=" + DoubleToString(vFM, 2);
      return true;
   }

   double riskPct = RiskWaveBiasaPct;
   int jmlPosisi  = MathMax(1, MaxEntryBiasa);

   if(cat == 0)      { riskPct = RiskWaveSuperPct;    jmlPosisi = MathMax(1, MaxEntrySuper); }
   else if(cat == 1) { riskPct = RiskWaveBiasaPct;    jmlPosisi = MathMax(1, MaxEntryBiasa); }
   else if(cat == 5)
   {
      riskPct = RiskWaveScalpPct;
      bool isRange = MS_M1SedangRange();
      jmlPosisi = (isRange ? 1 : MathMax(1, ScalpMaxPosisi));
   }
   else { riskPct = RiskWaveBreakoutPct; jmlPosisi = MathMax(1, MaxEntryBreakout); }

   int sIdx = (stratIdx >= 0 && stratIdx < 6 ? stratIdx : (cat == 5 ? ST_SCALP : ST_SMC));
   double scoreMult = 1.0;
   if(g_LearnScore[sIdx] < 50.0)      scoreMult = 0.50;
   else if(g_LearnScore[sIdx] < 80.0) scoreMult = 0.75;

   double throttle = scoreMult;
   double pnlHari = V24_ProfitHarian();
   if(pnlHari < 0 && MathAbs(pnlHari) > bal * 0.08) throttle *= 0.5;
   if(g_ConsecSL >= 2) throttle *= 0.5;
   MqlDateTime dtNow; TimeToStruct(TimeTradeServer(), dtNow);
   if(g_JamRawan[dtNow.hour] == 1) throttle *= 0.5;

   double riskPerLot = V24_RiskMoney(oty, 1.0, entry, sl);
   if(riskPerLot <= 0.0) { info = "jarak SL tidak valid"; return false; }

   double budgetGelombang = bal * (riskPct / 100.0) * throttle;
   double budgetPerPosisi = budgetGelombang / (double)jmlPosisi;
   double rawLot = budgetPerPosisi / riskPerLot;

   double v = NormalizeDouble(MathFloor(rawLot / st + 1e-9) * st, vd);
   if(v < mn) v = mn;
   if(v > mx) v = mx;
   if(!ValidasiVolumeOrder(v)) { info = "volume tidak sesuai step/limit broker"; return false; }
   vol = v;
   info = "Bal=" + DoubleToString(bal, 0) + " Risk=" + DoubleToString(riskPct * throttle, 2) + "% (Learn=" + DoubleToString(g_LearnScore[sIdx], 0) + ") Lot=" + DoubleToString(v, 2);
   return true;
}

LANGKAH 4: Jadikan Scalping Jalur VIP Satu Pintu & Hapus Pemblokiran Order Saat Belajar

1. Di Baris 1646 – 1675 (di dalam MS_Jalankan()):
	• Cari seluruh blok if(scalpBoleh && MS_SiapkanKonteksM1()) { ... } (baris 1646–1675) dan ganti menjadi 1 baris komentar agar Scalping 100% dikendalikan satu pintu VIP oleh V24_JagaSiklusReverse():mql5
   // Jalur VIP Scalping 100% satu pintu di V24_JagaSiklusReverse() tanpa bentrok!
Gunakan kode dengan hati-hati.
2. Di Baris 1581 – 1589 (di dalam MS_Pilih()):
	• Cari: if(g_LearnScore[ls] < 50.0) thrSel += 5.0;
	• Hapus baris tersebut agar EA belajar sambil jalan dengan mengecilkan lot tanpa menahan orderan!

LANGKAH 5: Aktifkan Sniper Full Margin (FM), News Spike/NFP, & Koreksi Kedalaman Pasca-SL

1. Di Baris 746 – 902 (di dalam EksekusiSatuSinyal()):
	• Di Baris 781: Ganti double titikSniper=(bullish ? entry.batasAtas - (0.25 * tinggiZona) : entry.batasBawah + (0.25 * tinggiZona)); menjadi menggunakan variabel belajar g_SniperDepthPct (yang otomatis bergeser lebih dalam jika sebelumnya terkena SL lalu memantul):mql5
   double titikSniper=(bullish ? entry.batasAtas - (g_SniperDepthPct * tinggiZona) : entry.batasBawah + (g_SniperDepthPct * tinggiZona));
Gunakan kode dengan hati-hati.
	• Di Baris 827: Ubah SL Sniper agar memakai Micro-SL 15 pips jika kategori SUPER pada zona raksasa (H1/H4/W1/MN1 dengan skor belajar >= 85%):mql5
   bool bolehFM = (kat == ZONA_SUPER && entry.timeframe >= PERIOD_H1 && g_LearnScore[ST_SMC] >= 85.0 && !g_FMTerpakaiHariIni);
   if(bolehFM)
   {
      sl = AlignHargaTick(bullish ? entryPrice - V24_Pip(15.0) : entryPrice + V24_Pip(15.0), !bullish);
   }
Gunakan kode dengan hati-hati.
	• Di Baris 862: Panggil V24_Lot dengan parameter bolehFM:mql5
   if(!V24_Lot(bullish, entryPrice, sl, (int)kat, volume, linfo, ST_SMC, bolehFM))
Gunakan kode dengan hati-hati.
	• Di Baris 884: Tambahkan tanda |FM=1| pada komentar jika bolehFM aktif:mql5
   string comment="A418|K="+IntegerToString((int)kat)+"|TF="+IntegerToString((int)entry.timeframe)+"|Z="+IntegerToString(entry.sumber)+"|Q="+IntegerToString(entry.skor)+(bolehFM?"|FM=1|":"");
   if(bolehFM) g_FMTerpakaiHariIni = true;
Gunakan kode dengan hati-hati.
2. Di Baris 965 – 972 (di dalam OnTradeTransaction()):
	• Tambahkan kode Post-SL Watch (menggeser g_SniperDepthPct lebih dalam saat kena SL dan menyimpan V24_SimpanBukuOtak()):mql5
   if(posSelesai && sidMS>=0 && sidMS<6)
   {
      if(profit>0.0)      g_LearnScore[sidMS]=MathMin(100.0,g_LearnScore[sidMS]+8.0);
      else if(profit<0.0)
      {
         g_LearnScore[sidMS]=MathMax(45.0,g_LearnScore[sidMS]-7.0);
         if(sidMS == ST_SMC) g_SniperDepthPct = MathMin(0.80, g_SniperDepthPct + 0.10); // Koreksi bidikan lebih dalam!
      }
      V24_SimpanBukuOtak();
   }
Gunakan kode dengan hati-hati.

LANGKAH 6: Perluas Pemindaian Menjadi 9 Timeframe (M1 sampai MN1) & Perbarui Array

1. Baris 341 (ScanTFs):
	• Cari: ENUM_TIMEFRAMES ScanTFs[7] = {PERIOD_M1,PERIOD_M5,PERIOD_M15,PERIOD_M30,PERIOD_H1,PERIOD_H4,PERIOD_D1};
	• Ganti menjadi:mql5
ENUM_TIMEFRAMES ScanTFs[9] = {PERIOD_M1,PERIOD_M5,PERIOD_M15,PERIOD_M30,PERIOD_H1,PERIOD_H4,PERIOD_D1,PERIOD_W1,PERIOD_MN1};
Gunakan kode dengan hati-hati.
2. Baris 322 – 330 (maHandles, rsiHandles, fractalHandles, atrScanHandles, lastScanBarByTF, lastEntryBarTime, dll.):
	• Ganti ukuran array [7] pada baris 322–330 dan baris 1236 (datetime lc[7];) menjadi [9], serta di ValidasiSemuaTimeframe() (baris 512) dan BuatHandleIndikatorMTF() / LepasHandleIndikatorMTF() (baris 983–1005) otomatis mengikuti ArraySize(ScanTFs) (9 timeframe).
3. Baris 63 & 84 (Sabuk Pengaman Basket & Drawdown):
	• Ubah MaxRiskPerBasketPct = 6.0; dan MaxDrawdownPct = 30.0; dan MaxPosisiEA = 10; (baris 158).

LANGKAH 7: Perbarui Prototipe & Variabel Global di Bagian Paling Atas (Baris 9 & Baris 45)

1. Baris 9:mql5
bool   V24_Lot(bool bull,double entry,double sl,int cat,double &vol,string &info,int stratIdx=-1,bool isFullMargin=false);
Gunakan kode dengan hati-hati.
2. Baris 45 – 51 (tambahkan variabel Buku Otak & Full Margin):mql5
double g_LearnScore[6] = {100.0, 100.0, 100.0, 100.0, 100.0, 100.0};
int    g_ConsecSL = 0;
int    g_JamRawan[24];
bool   g_TargetMenungguTutup = false;
double g_SniperDepthPct = 0.45;
bool   g_FMTerpakaiHariIni = false;
void   V24_SimpanBukuOtak();
void   V24_MuatBukuOtak();
Gunakan kode dengan hati-hati.

Verifikasi Akhir

Setelah ke-7 langkah di atas diterapkan berurutan dari bawah ke atas, tekan F7 (Compile) di MetaEditor hingga muncul 0 errors, 0 warnings.
Apakah setelah menerapkan ketujuh langkah perakitan di atas hasil Compile (F7) sudah 0 errors, dan apakah Anda siap mengujinya di Strategy Tester MT5 sekarang?
