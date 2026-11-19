Berikut adalah panduan lokasi yang presisi dan kode MQL5 lengkap untuk setiap modul yang telah kita rancang, sehingga Anda bisa langsung menempelkannya ke dalam file EA APlus V24.18 Anda tanpa merusak struktur utamanya.

Peta Lokasi Pemasangan Kode


Bagian	Lokasi di File V24.18 Anda	Perkiraan Baris	Tindakan
1. Variabel Global & Cuaca Baru	Setelah deklarasi bool g_ShadowActive = false;	Baris ±80	Tambahkan kode variabel baru.
2. Detektor Cuaca & Sudden Breakout M15	Menggantikan void DS_EvaluasiCuacaPasar() hingga akhir bool MS_M1SedangRange()	Baris ±1330 – 1495	Ganti blok fungsi lama dengan blok baru.
3. VIP Scalping (Instant Range, Trend, & Chaos Reverse)	Menggantikan void V24_JagaSiklusReverse()	Baris ±1885 – 2030	Ganti seluruh fungsi V24_JagaSiklusReverse.
4. Pengawalan SL+, Reverse Chaos, & Re-Entry 2 Detik	Di dalam void V24_KelolaSemua() (bagian akhir) & void OnTradeTransaction()	Baris ±1070 & ±2185	Tambahkan deteksi SL+ dan pemicu 2 detik.
5. Metode Utama 3-Layer Zone-to-Zone	Menggantikan logika eksekusi di bool EksekusiSatuSinyal()	Baris ±770 – 890	Ganti bagian penembakan burst menjadi 3-Layer bertingkat.


Bagian 1: Variabel Global & Status Cuaca Baru

Lokasi: Tepat di bawah baris bool g_ShadowActive = false; (sekitar baris 80).
mql5
// =========================================================================
// V25 HYBRID UPGRADE: CUACA AKURAT, 3-LAYER Z2Z, RE-ENTRY 2 DETIK
// =========================================================================
enum CuacaPasarEnum { CUACA_RANGE=0, CUACA_TREND=1, CUACA_BREAKOUT=2, CUACA_CHAOS_NGAMUK=3, CUACA_CHAOS_NGANTUK=4, CUACA_SQUEEZE=5 };
CuacaPasarEnum g_CuacaSekarang = CUACA_RANGE;
datetime g_KunciCuacaSampai = 0;

// Variabel Smart Re-Entry Pasca-SL+ (Jeda 2 Detik)
datetime g_WaktuKenaSLPlus = 0;
bool     g_MenungguReEntrySLPlus = false;
int      g_HitunganReEntryGelombang = 0;
bool     g_ArahTerakhirSLPlus = true;

// Input Tambahan (Opsional di panel input EA)
input int    JedaReEntrySLPlusDetik = 2;    // Jeda 2 detik pasca kena SL+
input int    MaxReEntryGelombang    = 3;    // Maksimal sambung gelombang pasca SL+
input double RiskLayerZonePct       = 1.50; // Total risiko 1 gelombang 3-Layer (% balance)
Gunakan kode dengan hati-hati.

Bagian 2: Detektor Cuaca Akurat & Sudden Breakout M15

Lokasi: Cari fungsi void DS_EvaluasiCuacaPasar() hingga akhir bool MS_M1SedangRange() (sekitar baris 1330 – 1495), lalu ganti seluruh bagian tersebut dengan kode berikut:
mql5
// Detektor Sudden Breakout M15 (Pilar TrendMatrix Hybrid)
int DS_CekSuddenBreakoutM15()
{
   if(gM15n < 20 || g_atr15 <= 0.0) return 0;
   double body1 = MathAbs(gM15[1].close - gM15[1].open);
   double rng1  = gM15[1].high - gM15[1].low;
   if(rng1 <= 0.0 || body1 < 1.1 * g_atr15 || body1 / rng1 < 0.65) return 0;

   double hh = MS_MaxHigh(gM15, gM15n, 2, 12);
   double ll = MS_MinLow(gM15, gM15n, 2, 12);
   if(gM15[1].close > hh + V24_Pip(3.0)) return 1;  // Sudden Breakout BUY
   if(gM15[1].close < ll - V24_Pip(3.0)) return -1; // Sudden Breakout SELL
   return 0;
}

void DS_EvaluasiCuacaPasar()
{
   DS_ResetVaultHarian();
   if(gM1n < 35 || g_atr1 <= 0.0) return;

   // Update Vault Lock (Kunci 70% profit jika harian > 3%)
   double pnlH = V24_ProfitHarian();
   double bal = AccountInfoDouble(ACCOUNT_BALANCE);
   if(bal > 0.0 && pnlH > bal * 0.03)
      g_VaultLockedUSD = MathMax(g_VaultLockedUSD, pnlH * 0.70);

   // 1. Cek Chaos Ngantuk (Pasar Mati: rata-rata range 6 candle M1 < 6 pip & kotak 30m < 12 pip)
   double sumRng6 = 0.0;
   for(int i = 1; i <= 6; i++) sumRng6 += (gM1[i].high - gM1[i].low);
   double avgRng6 = sumRng6 / 6.0;
   double lebar30 = MS_MaxHigh(gM1, gM1n, 1, 30) - MS_MinLow(gM1, gM1n, 1, 30);

   if(avgRng6 < V24_Pip(6.0) && lebar30 < V24_Pip(12.0))
   {
      g_CuacaSekarang = CUACA_CHAOS_NGANTUK;
      g_MarketChaosNgantuk = true; g_MarketChaos = false; g_MarketSqueeze = false;
      HapusSemuaPendingReverseScalp();
      return;
   }

   // 2. Cek Chaos Ngamuk (Whipsaw: candle lebar >= 20 pip, ekor >= 60%, dan arah bolak-balik)
   int whipsawCount = 0;
   for(int j = 1; j <= 5; j++)
   {
      double rng  = gM1[j].high - gM1[j].low;
      double body = MathAbs(gM1[j].close - gM1[j].open);
      if(rng >= V24_Pip(20.0) && (rng - body) / rng >= 0.60) whipsawCount++;
   }
   bool bolakBalik = ((gM1.close > gM1.open) != (gM1.close > gM1.open)) &&
                     ((gM1.close > gM1.open) != (gM1.close > gM1.open));

   if(whipsawCount >= 3 || (whipsawCount >= 2 && bolakBalik))
   {
      g_CuacaSekarang = CUACA_CHAOS_NGAMUK;
      g_MarketChaos = true; g_MarketChaosNgantuk = false; g_MarketSqueeze = false;
      g_KunciCuacaSampai = TimeCurrent() + 30;
      return;
   }

   // 3. Cek Sudden Breakout (Candle M1 tertutup jebol channel >= 5 pip dengan body penuh >= 65% ATAU M15 Breakout)
   int boM15 = DS_CekSuddenBreakoutM15();
   bool boM1 = false;
   if(g_TL_M1.valid)
   {
      datetime t1 = gM1.time;
      double up1 = TL_HargaPadaWaktu(g_TL_M1.tA1, g_TL_M1.pA1, g_TL_M1.tA2, g_TL_M1.pA2, t1);
      double dn1 = TL_HargaPadaWaktu(g_TL_M1.tB1, g_TL_M1.pB1, g_TL_M1.tB2, g_TL_M1.pB2, t1);
      double rng1 = gM1.high - gM1.low;
      double body1 = MathAbs(gM1.close - gM1.open);
      if(rng1 > 0.0 && body1 / rng1 >= 0.65 && body1 >= V24_Pip(8.0) &&
         (gM1.close > up1 + V24_Pip(5.0) || gM1.close < dn1 - V24_Pip(5.0))) boM1 = true;
   }
   if(boM1 || boM15 != 0)
   {
      g_CuacaSekarang = CUACA_BREAKOUT;
      g_MarketChaos = false; g_MarketChaosNgantuk = false; g_MarketSqueeze = false;
      g_KunciCuacaSampai = TimeCurrent() + 20;
      HapusSemuaPendingReverseScalp(); // Bersihkan reverse stop sisa chaos
      return;
   }

   if(TimeCurrent() < g_KunciCuacaSampai) return;

   // 4. Cek ATR Squeeze
   if(avgRng6 < g_atr1 * 0.50 && lebar30 >= V24_Pip(12.0))
   {
      g_CuacaSekarang = CUACA_SQUEEZE;
      g_MarketSqueeze = true; g_MarketChaos = false; g_MarketChaosNgantuk = false;
      HapusSemuaPendingReverseScalp();
      return;
   }

   // 5. Pisahkan Trending Sehat vs Range Sehat
   double net25  = MathAbs(gM1.close - gM1.close);
   double path25 = 0.0;
   for(int k = 1; k <= 25; k++) path25 += MathAbs(gM1[k].close - gM1[k+1].close);
   double erM1 = (path25 > 0.0 ? net25 / path25 : 0.0);
   double jarakEMA = MathAbs(MS_EMA(PERIOD_M1, 8, 1) - MS_EMA(PERIOD_M1, 21, 1));

   g_MarketChaos = false; g_MarketChaosNgantuk = false; g_MarketSqueeze = false;
   HapusSemuaPendingReverseScalp(); // Pastikan pending reverse tidak tertinggal di mode normal

   if(erM1 >= 0.42 && jarakEMA >= V24_Pip(5.0))
      g_CuacaSekarang = CUACA_TREND;
   else
      g_CuacaSekarang = CUACA_RANGE;

   g_KunciCuacaSampai = TimeCurrent() + 15;
}

bool MS_M1SedangRange()
{
   return (g_CuacaSekarang == CUACA_RANGE);
}
Gunakan kode dengan hati-hati.

Bagian 3: VIP Scalping (Order Instan Range, Trend, & Reverse Stop Khusus Chaos Ngamuk)

Lokasi: Ganti seluruh fungsi void V24_JagaSiklusReverse() (sekitar baris 1885 – 2030) dengan kode berikut:
mql5
void V24_JagaSiklusReverse()
{
   if(!ScalpReverseAktif || ModeOperasi != AUTO_TRADE || g_TargetMenungguTutup)
   {
      HapusSemuaPendingReverseScalp(); HapusPendingInitScalp(); return;
   }
   MqlTick tick;
   if(!SymbolInfoTick(SymbolKerja, tick) || tick.bid <= 0.0 || tick.ask <= 0.0) return;
   DS_CatatTick(tick.bid, (double)SymbolInfoInteger(SymbolKerja, SYMBOL_SPREAD));
   if(DS_SpreadShock()) return;
   DS_ResetVaultHarian();

   // Cek Filter Berita & VIP News
   datetime nowJ = TimeTradeServer(); if(nowJ <= 0) nowJ = TimeCurrent();
   bool newsOK = NewsFilterBolehLanjut(), modeNewsVIP = false;
   if(newsOK) g_SpikeDetectedTime = 0;
   else if(g_NewsModeVIP == 1 && g_NewsEventTime > 0 && nowJ >= g_NewsEventTime - 15 && nowJ <= g_NewsEventTime + 60) modeNewsVIP = true;
   else if(g_NewsModeVIP == 2 && g_NewsEventTime > 0 && nowJ > g_NewsEventTime)
   {
      double rngM1 = iHigh(SymbolKerja, PERIOD_M1, 0) - iLow(SymbolKerja, PERIOD_M1, 0);
      if(rngM1 >= V24_Pip(25.0) && g_SpikeDetectedTime == 0) g_SpikeDetectedTime = nowJ;
      if(g_SpikeDetectedTime > 0 && nowJ >= g_SpikeDetectedTime + 3) modeNewsVIP = true;
   }
   if(!newsOK && !modeNewsVIP) { HapusPendingInitScalp(); return; }

   int limSpread = (ScalpSpreadMaxPoints > 0 ? (int)MathMin((double)ScalpSpreadMaxPoints * V24_SpreadScale(), (double)SpreadMaxPoints) : SpreadMaxPoints);
   if((int)SymbolInfoInteger(SymbolKerja, SYMBOL_SPREAD) > limSpread) return;

   // Cek Batas Rugi Harian & Vault
   double balR = AccountInfoDouble(ACCOUNT_BALANCE), rl = HitungProfitRealisasiEASejak(AwalHariServer());
   double baseD = (MetrikAwalHariEA > 0.0 ? MetrikAwalHariEA : balR);
   if(rl != EMPTY_VALUE && rl < 0.0 && -rl >= baseD * MathMin(DailyLossLimitPct, MaxDailyLossPct) / 100.0) return;
   if(g_VaultLockedUSD > 0.0 && V24_ProfitHarian() <= g_VaultLockedUSD) return;

   if(!MS_SiapkanKonteksM1() || gM1n < 25) return;
   DS_EvaluasiCuacaPasar();

   // 1. Jika Chaos Ngantuk (Pasar Mati) -> Standby Total
   if(g_CuacaSekarang == CUACA_CHAOS_NGANTUK && !modeNewsVIP) return;

   // 2. Cek apakah harga sedang di dalam Zona Besar Metode Utama -> Scalping Mengalah
   for(int z = 0; z < JumlahZonaRegistry; z++)
   {
      if(ZonaRegistryValid(RegistryZona[z]) && zStatus[z] < ZS_BREACHED && RegistryZona[z].timeframe >= PERIOD_M15)
         if(HargaSedangMenyentuhZona(RegistryZona[z])) return;
   }

   // Cek posisi scalping aktif
   int adaPosisiScalp = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(tk > 0 && PositionGetString(POSITION_SYMBOL) == SymbolKerja && (ulong)PositionGetInteger(POSITION_MAGIC) == MagicNumber && StringFind(PositionGetString(POSITION_COMMENT), "|S=5|") >= 0) adaPosisiScalp++;
   }
   if(adaPosisiScalp > 0) return;

   // Hapus semua Limit Order lama (sekarang 100% Order Instan)
   HapusPendingInitScalp();

   double pt = SymbolInfoDouble(SymbolKerja, SYMBOL_POINT);
   double stl = (double)MathMax(SymbolInfoInteger(SymbolKerja, SYMBOL_TRADE_STOPS_LEVEL), SymbolInfoInteger(SymbolKerja, SYMBOL_TRADE_FREEZE_LEVEL)) * pt;
   double upPress = 50.0; int t3s = 0, tPrev = 0;
   DS_AnalisaOrderFlow(upPress, t3s, tPrev);

   datetime tNow = iTime(SymbolKerja, PERIOD_M1, 0);
   double garisAtas = (g_TL_M1.valid ? TL_HargaPadaWaktu(g_TL_M1.tA1, g_TL_M1.pA1, g_TL_M1.tA2, g_TL_M1.pA2, tNow) : MS_MaxHigh(gM1, gM1n, 1, 15));
   double garisBawah = (g_TL_M1.valid ? TL_HargaPadaWaktu(g_TL_M1.tB1, g_TL_M1.pB1, g_TL_M1.tB2, g_TL_M1.pB2, tNow) : MS_MinLow(gM1, gM1n, 1, 15));

   static datetime lastInstanExec = 0;
   if(TimeCurrent() - lastInstanExec < 2) return;

   // =====================================================================
   // MODE A: RANGE / SIDEWAYS -> ORDER INSTAN PANTULAN (TANPA LIMIT ORDER)
   // =====================================================================
   if(g_CuacaSekarang == CUACA_RANGE && !modeNewsVIP && (garisAtas - garisBawah >= V24_Pip(10.0)))
   {
      double low0 = iLow(SymbolKerja, PERIOD_M1, 0), high0 = iHigh(SymbolKerja, PERIOD_M1, 0), open0 = iOpen(SymbolKerja, PERIOD_M1, 0);
      double slDistR = MathMax(V24_Pip(12.0), stl + 2.0 * pt);

      // Pantulan BUY dari batas bawah saluran + Order Flow mulai naik
      if(low0 <= garisBawah + V24_Pip(2.0) && tick.bid > open0 && upPress >= 56.0)
      {
         double slB = AlignHargaTick(MathMin(low0, garisBawah) - slDistR * 0.6, false);
         double tpB = AlignHargaTick(garisAtas - V24_Pip(2.0), false);
         double volB = 0.0; string infB = "";
         if(V24_Lot(true, tick.ask, slB, 5, volB, infB) && tpB > tick.ask + stl && DS_RisikoBasketLolos(true, volB, tick.ask, slB))
         {
            if(trade.Buy(volB, SymbolKerja, 0.0, slB, tpB, "SCALP_RNG_INSTAN|S=5|0"))
            { lastInstanExec = TimeCurrent(); Print("SCALP_RANGE_BUY_INSTAN | Entry=", tick.ask, " TP=", tpB); return; }
         }
      }
      // Pantulan SELL dari batas atas saluran + Order Flow mulai turun
      if(high0 >= garisAtas - V24_Pip(2.0) && tick.bid < open0 && upPress <= 44.0)
      {
         double slS = AlignHargaTick(MathMax(high0, garisAtas) + slDistR * 0.6, true);
         double tpS = AlignHargaTick(garisBawah + V24_Pip(2.0), true);
         double volS = 0.0; string infS = "";
         if(V24_Lot(false, tick.bid, slS, 5, volS, infS) && tpS < tick.bid - stl && DS_RisikoBasketLolos(false, volS, tick.bid, slS))
         {
            if(trade.Sell(volS, SymbolKerja, 0.0, slS, tpS, "SCALP_RNG_INSTAN|S=5|0"))
            { lastInstanExec = TimeCurrent(); Print("SCALP_RANGE_SELL_INSTAN | Entry=", tick.bid, " TP=", tpS); return; }
         }
      }
      return;
   }

   // =====================================================================
   // MODE B: TREND, BREAKOUT, VIP NEWS, & CHAOS NGAMUK -> ORDER INSTAN
   // (Khusus Chaos Ngamuk & VIP FOMC otomatis dikawal Reverse Stop di V24_KelolaSemua)
   // =====================================================================
   double ema8 = MS_EMA(PERIOD_M1, 8, 0), ema21 = MS_EMA(PERIOD_M1, 21, 0);
   if(ema8 <= 0.0 || ema21 <= 0.0) return;

   bool isChaosMode = (g_CuacaSekarang == CUACA_CHAOS_NGAMUK || g_NewsModeVIP == 2);
   bool arahBuy  = (ema8 > ema21 && tick.ask > gM1.high && upPress >= 58.0);
   bool arahSell = (ema8 < ema21 && tick.bid < gM1.low  && upPress <= 42.0);
   if(!arahBuy && !arahSell) return;

   bool bull = arahBuy;
   double entry = (bull ? tick.ask : tick.bid);
   double jarakSL = MathMax(V24_Pip(ScalpSLMinPips), stl + 2.0 * pt);
   double sl = AlignHargaTick(bull ? entry - jarakSL : entry + jarakSL, !bull);
   double vol = 0.0; string info = "";
   if(!V24_Lot(bull, entry, sl, 5, vol, info)) return;
   if(!DS_RisikoBasketLolos(bull, vol, entry, sl) || HitungPosisiEA() + 1 > MaxPosisiEA) return;

   string tagComment = (isChaosMode ? "CHAOS_REV|S=5|0" : "TREND_VIP|S=5|0");
   bool ok = (bull ? trade.Buy(vol, SymbolKerja, 0.0, sl, 0.0, tagComment)
                   : trade.Sell(vol, SymbolKerja, 0.0, sl, 0.0, tagComment));
   if(ok)
   {
      lastInstanExec = TimeCurrent();
      long pid = 0; ulong d = trade.ResultDeal();
      if(d > 0 && HistoryDealSelect(d)) pid = HistoryDealGetInteger(d, DEAL_POSITION_ID);
      if(pid == 0) pid = (long)trade.ResultOrder();
      if(pid > 0) { string sp = IntegerToString(pid); SimpanGV("SR" + sp, jarakSL); SimpanGV("SB" + sp, 0.0); SimpanGV("SV" + sp, vol); }
      Print("VIP_INSTAN_EXEC | ", (bull ? "BUY" : "SELL"), " Mode=", (isChaosMode ? "CHAOS_REVERSE" : "TREND_SLPLUS"), " Lot=", vol);
   }
}
Gunakan kode dengan hati-hati.

Bagian 4: Pengawalan SL+, Reverse Stop Khusus Chaos, & Re-Entry Jeda 2 Detik


4A. Pembatasan Reverse Stop Hanya untuk Chaos Ngamuk & VIP FOMC

Lokasi: Di baris paling bawah fungsi void V24_KelolaSemua() (sekitar baris 2180 – 2195). Ganti blok sinkronisasi KelolaReverseGelombangScalp dengan:
mql5
   // Reverse Stop HANYA aktif jika cuaca = CHAOS_NGAMUK atau VIP NEWS FOMC (g_NewsModeVIP == 2)
   bool bolehReverseChaos = (g_CuacaSekarang == CUACA_CHAOS_NGAMUK || g_NewsModeVIP == 2);
   if(bolehReverseChaos && dW >= 0 && scX[dW] > 0.0 && adaScalpTanpaTP)
   {
      KelolaReverseGelombangScalp((dW == 1), scX[dW], scV[dW], scR[dW]);
   }
   else
   {
      HapusSemuaPendingReverseScalp();
   }
Gunakan kode dengan hati-hati.

4B. Deteksi Kena SL+ di OnTradeTransaction() & Eksekusi Jeda 2 Detik di OnTick()

Lokasi 1: Di dalam fungsi void OnTradeTransaction(...) tepat sebelum baris Print("TRADE_RESULT...") (sekitar baris 1070). Tambahkan:
mql5
   // Deteksi apakah posisi ditutup karena menyentuh SL+ (Profit > 0 dan reason == SL)
   if(posSelesai && reason == DEAL_REASON_SL && profit > 0.0)
   {
      if(g_HitunganReEntryGelombang < MaxReEntryGelombang)
      {
         g_WaktuKenaSLPlus = TimeCurrent();
         g_MenungguReEntrySLPlus = true;
         g_HitunganReEntryGelombang++;
         g_ArahTerakhirSLPlus = (arah == "BUY");
         Print("SL+_TERKENA | Profit=", DoubleToString(profit, 2), " | Jeda ", JedaReEntrySLPlusDetik, " detik untuk analisa arah baru...");
      }
   }
   else if(posSelesai && reason == DEAL_REASON_SL && profit <= 0.0)
   {
      // SL Rugi Biasa -> reset hitungan sambung gelombang
      g_MenungguReEntrySLPlus = false;
      g_HitunganReEntryGelombang = 0;
   }
Gunakan kode dengan hati-hati.
Lokasi 2: Tambahkan fungsi V24_CekReEntryPascaSLPlus() tepat di atas void OnTick() (sekitar baris 2630), dan panggil V24_CekReEntryPascaSLPlus(); di baris awal OnTick():
mql5
void V24_CekReEntryPascaSLPlus()
{
   if(!g_MenungguReEntrySLPlus) return;
   if(TimeCurrent() - g_WaktuKenaSLPlus < JedaReEntrySLPlusDetik) return; // Tunggu tepat 2 detik

   g_MenungguReEntrySLPlus = false;
   if(DS_SpreadShock() || g_CuacaSekarang == CUACA_CHAOS_NGANTUK || g_CuacaSekarang == CUACA_CHAOS_NGAMUK) return;
   if(HitungPosisiEA() >= MaxPosisiEA) return;

   double upPress = 50.0; int t3 = 0, tp = 0;
   DS_AnalisaOrderFlow(upPress, t3, tp);
   double ema8 = MS_EMA(PERIOD_M1, 8, 0);
   double bid  = SymbolInfoDouble(SymbolKerja, SYMBOL_BID);
   double ask  = SymbolInfoDouble(SymbolKerja, SYMBOL_ASK);

   // Melihat harga akan kemana setelah jeda 2 detik (bisa lanjut tren atau balik arah)
   bool arahBuy  = (bid > ema8 && upPress >= 58.0);
   bool arahSell = (bid < ema8 && upPress <= 42.0);
   if(!arahBuy && !arahSell)
   {
      Print("REENTRY_2S_BATAL | Arah harga belum tegas setelah 2 detik (OrderFlow=", DoubleToString(upPress, 0), "%)");
      return;
   }

   bool bull = arahBuy;
   double entry = (bull ? ask : bid);
   double jarakSL = V24_Pip(ScalpSLMinPips);
   double sl = AlignHargaTick(bull ? entry - jarakSL : entry + jarakSL, !bull);
   double vol = 0.0; string info = "";

   if(V24_Lot(bull, entry, sl, 5, vol, info) && DS_RisikoBasketLolos(bull, vol, entry, sl))
   {
      bool ok = (bull ? trade.Buy(vol, SymbolKerja, 0.0, sl, 0.0, "RE_SLPLUS_2S|S=5|0")
                      : trade.Sell(vol, SymbolKerja, 0.0, sl, 0.0, "RE_SLPLUS_2S|S=5|0"));
      if(ok)
      {
         long pid = 0; ulong d = trade.ResultDeal();
         if(d > 0 && HistoryDealSelect(d)) pid = HistoryDealGetInteger(d, DEAL_POSITION_ID);
         if(pid == 0) pid = (long)trade.ResultOrder();
         if(pid > 0) { string sp = IntegerToString(pid); SimpanGV("SR" + sp, jarakSL); SimpanGV("SB" + sp, 0.0); SimpanGV("SV" + sp, vol); }
         Print("REENTRY_2S_SUKSES | ", (bull ? "BUY" : "SELL"), " (Gelombang ke-", g_HitunganReEntryGelombang, ") OrderFlow=", DoubleToString(upPress, 0), "%");
      }
   }
}
Gunakan kode dengan hati-hati.

Bagian 5: Metode Utama 3-Layer Zone-to-Zone (Seperti 10 Foto Referensi)

Lokasi: Di dalam fungsi bool EksekusiSatuSinyal(...) (sekitar baris 775 – 890), ganti bagian pengecekan kedalaman titikSniper dan blok loop for(int ez=0; ez<jmlEntryZona; ez++) dengan logika 3-Layer Bertingkat (20%, 50%, 80% kedalaman zona) berikut:
mql5
   // Cek sudah berapa layer yang terisi di zona ini (maksimal 3 layer bertingkat)
   int layerSudahMasuk = JumlahEntryZona(entry);
   if(layerSudahMasuk >= 3) { JurnalTolak(idx, kat, DG_DONE, "3 Layer zona sudah terisi penuh"); return false; }

   // Tentukan kedalaman target untuk layer berikutnya: Layer 1 = 20%, Layer 2 = 50%, Layer 3 = 80%
   double targetDepthPct = (layerSudahMasuk == 0 ? 0.20 : (layerSudahMasuk == 1 ? 0.50 : 0.80));
   MqlTick tkTouch;
   if(!SymbolInfoTick(SymbolKerja, tkTouch)) return false;
   double pxTouch = (bullish ? tkTouch.ask : tkTouch.bid);
   double tinggiZona = entry.batasAtas - entry.batasBawah;
   if(tinggiZona <= 0.0) return false;

   double titikLayer = (bullish ? entry.batasAtas - (targetDepthPct * tinggiZona)
                                : entry.batasBawah + (targetDepthPct * tinggiZona));
   bool kenaTitikLayer = (bullish ? (pxTouch <= titikLayer && pxTouch >= entry.batasBawah)
                                  : (pxTouch >= titikLayer && pxTouch <= entry.batasAtas));
   if(!kenaTitikLayer) return false;

   // Tahan eksekusi sementara jika M1 sedang Chaos Ngamuk (menunggu ekor liar mereda)
   if(g_CuacaSekarang == CUACA_CHAOS_NGAMUK) return false;
Gunakan kode dengan hati-hati.
Dan untuk pembagian lot agar total risiko 3 Layer tetap sama dengan 1 gelombang (RiskLayerZonePct), gunakan perhitungan ini saat mengirim order 1 layer per sentuhan:
mql5
   // Hitung lot untuk 1 layer = (Anggaran 1 Gelombang / 3 Layer)
   double balZ = AccountInfoDouble(ACCOUNT_BALANCE);
   double budgetPerLayer = (balZ * (RiskLayerZonePct / 100.0)) / 3.0;
   double riskPerLotZ = V24_RiskMoney(bullish ? ORDER_TYPE_BUY : ORDER_TYPE_SELL, 1.0, entryPrice, sl);
   if(riskPerLotZ <= 0.0) return false;
   double volLayer = NormalisasiVolumeBawah(budgetPerLayer / riskPerLotZ);
   double minLotB = SymbolInfoDouble(SymbolKerja, SYMBOL_VOLUME_MIN);
   if(volLayer < minLotB) volLayer = minLotB;
Gunakan kode dengan hati-hati.

Cara Melakukan Pengujian & Evaluasi Setelah Terpasang

1. Compile di MetaEditor (F7): Pastikan muncul 0 errors, 0 warnings.
2. Uji di Strategy Tester MT5:
	• Pilih simbol XAUUSDm, Timeframe M5 (EA tetap memindai M1 hingga H4 secara otomatis), dan model Every tick based on real ticks.
	• Perhatikan tab Journal untuk melihat apakah log cuaca (CUACA_RANGE, CUACA_TREND, CUACA_CHAOS_NGAMUK), SL+_TERKENA, dan REENTRY_2S_SUKSES berjalan sesuai skenario.
3. Jika Terlalu Banyak Kena SL:
	• Jika SL terjadi di Metode Utama (3-Layer): Perlebar buffer SL di luar zona (SLBufferNormalPips dinaikkan dari 5.0 menjadi 8.0–10.0 pip) karena XAUUSD sering menyapu batas luar kotak zona sejauh 5–7 pip sebelum memantul.
	• Jika SL terjadi di Scalping M1: Naikkan ambang Order Flow pada Bagian 3 & 4 dari 58% / 42% menjadi 65% / 35% agar EA hanya masuk saat dorongan tick benar-benar dominan.
Apakah ada bagian dari kode di atas yang memunculkan error saat Anda compile, atau ingin Anda sesuaikan terlebih dahulu angkanya sebelum diuji di Strategy Tester?
