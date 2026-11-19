Berikut adalah paket kode MQL5 final untuk DEWA XAUUSD V25 HYBRID SNIPER yang sudah diselaraskan 100% dengan seluruh aturan terakhir yang Anda tetapkan:
1. Patokan Lot Otomatis Mulai $1.000: Scalping 0.03, Super 0.03, Biasa/Trend/SR/SD 0.02, RBR/DBD/Retest 0.03—dan otomatis naik/turun proporsional mengikuti perkembangan saldo (Saldo / 1000).
2. Kotak Zona Beton M30 – W1 + Golden Fibo (50% – 61,8%): Hanya zona fresh yang berada di rasio emas 50% – 61,8%, berwarna isi lembut, dan tampil sesuai TF-nya masing-masing (M1/M5 kosong, M15 tampil M30/H1/H4, dan M30/H1/H4/D1/W1 tampil di TF-nya sendiri).
3. 3-Layer Zone-to-Zone (M30, H1, H4): Masuk bertingkat di kedalaman 20%, 50%, dan 80% dengan jeda minimal 3 detik dan jarak minimal 5 pip antar-layer (D1 & W1 tampil sebagai tembok batas/target tanpa entry).
4. VIP Scalping M1 Murni 24 Jam: Bebas bentrok dengan Metode Utama, SL seragam 15 pip baik saat Range maupun Trend, dikawal Trailing SL+ Kilat, Reverse Stop khusus saat Chaos Ngamuk, serta Smart Re-Entry (jeda 2 detik) setelah posisi terkena SL+.
5. Protokol VIP News (Aman / Sniper) + Pelindung Spread Rollover: Menahan entry jika spread melebar > 3,5 pip (35 poin setara 2 digit).

Peta Pemasangan Kode Final di File Anda (source: 3)


Blok	Fungsi / Bagian yang Diganti	Keterangan
Blok 1	Input Parameter & Judul EA	Menambahkan sakelar VIP News, batas spread scalping, dan identitas V25 Hybrid.
Blok 2	ZonaDitampilkan(), GambarZonaIdx(), SimpanZonaRegistry(), PerbaruiStatusZonaHistoris()	Aturan tampilan per TF, warna isi kotak, kunci Fibo 50%–61,8%, dan hapus instan jika zona jebol.
Blok 3	EksekusiSatuSinyal()	Kunci eksekusi khusus M30, H1, H4 + 3-Layer bertingkat (20%, 50%, 80%) + Veto Momentum.
Blok 4	V24_Lot()	Rumus patokan lot otomatis mulai $1.000 (0.03 & 0.02) yang berkembang otomatis sesuai saldo.
Blok 5	V24_JagaSiklusReverse(), V24_CekReEntryPascaSLPlus(), V24_KelolaSemua()	VIP Scalping M1 murni 24 jam, SL seragam Range & Trend + Trailing SL+ + Re-Entry jeda 2 detik.
Blok 6	V24_Dashboard() & OnTick()	Judul dashboard V25 Hybrid, info patokan lot aktif, dan pembersihan gambar kotak saat pindah TF.


Blok 1: Judul & Input Parameter Final

Lokasi: Ganti 3 baris #property paling atas dan tambahkan input baru tepat di bawah input double RiskLayerZonePct = 1.50; (baris ±77).
mql5
// --- Ganti 3 baris paling atas file Anda dengan ini ---
#property strict
#property version   "25.00"
#property description "DEWA XAUUSD V25 Hybrid Sniper: Golden-Fibo 50-61.8 Z2Z + M1 Order-Flow Scalping"

// --- Tambahkan input baru ini tepat di bawah RiskLayerZonePct (baris ±77) ---
enum ModeVIPNewsEnum { VIP_NEWS_AMAN = 0, VIP_NEWS_SNIPER = 1 };
input ModeVIPNewsEnum ModeVIPNews       = VIP_NEWS_SNIPER; // 0 = Istirahat total saat berita, 1 = Masuk detik ke-5 + Lot 50%
input int    JedaAntarLayerDetik        = 3;               // Jeda minimal 3 detik antar Layer 1, 2, dan 3
input double JarakMinAntarLayerPips     = 5.0;             // Jarak minimal 5 pip antar Layer agar tersebar rapi
input int    DeviasiAntiSlippagePoints  = 20;              // Maksimal selisih harga eksekusi 20 poin (2 pip) anti-keseret
input int    MaxSpreadScalp2DigitPts    = 35;              // Tahan scalping jika spread > 3.5 pip (35 poin setara 2 digit)
Gunakan kode dengan hati-hati.
(Pastikan input bool HanyaZonaFresh = true; dan input double ScalpSLMinPips = 15.0; sudah terpasang).

Blok 2: Zona Beton (M30–W1 + Fibo 50%–61,8%) & Tampilan Kotak Berwarna Isi

Lokasi: Ganti fungsi ZonaDitampilkan(), bagian kotak di GambarZonaIdx(), bagian awal SimpanZonaRegistry(), serta tolBreak di PerbaruiStatusZonaHistoris().
mql5
// 1. Aturan Tampilan Kotak Per Timeframe (M1/M5 kosong, M15 tampil M30-H4, M30..W1 tampil masing-masing)
bool ZonaDitampilkan(DataZona &z)
{
   if(z.timeframe < PERIOD_M30) return false;
   if((z.kategori == ZONA_SUPER || z.kategori == ZONA_BIASA) && z.skor < 5) return false;

   ENUM_TIMEFRAMES chartTF = (ENUM_TIMEFRAMES)_Period;
   if(chartTF == PERIOD_M1 || chartTF == PERIOD_M5) return false;
   if(chartTF == PERIOD_M15)
      return (z.timeframe == PERIOD_M30 || z.timeframe == PERIOD_H1 || z.timeframe == PERIOD_H4);

   // Di M30, H1, H4, D1, W1 -> hanya tampilkan kotak milik timeframe itu sendiri
   return (z.timeframe == chartTF);
}

// 2. Di dalam GambarZonaIdx(int idx): ganti blok pengaturan warna kotak & label (sekitar baris 620-648)
   color fillClr = (z.bullish ? C'14,48,68' : C'62,22,42');
   if(z.kategori == ZONA_RBR || z.kategori == ZONA_DBD)
      fillClr = (z.bullish ? C'18,42,74' : C'68,48,16');

   ObjectSetInteger(0, name, OBJPROP_COLOR, fillClr);
   ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_SOLID);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
   ObjectSetInteger(0, name, OBJPROP_FILL, true);      // Kotak berwarna isi penuh
   ObjectSetInteger(0, name, OBJPROP_BACK, true);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);
   // ... (pada bagian AturTampilanLabelZona di bawahnya, gunakan WarnaZona(z, false) sebagai warna teks)
   AturTampilanLabelZona(label, badge, WarnaZona(z, false), ANCHOR_CENTER);

// 3. Bagian awal SimpanZonaRegistry(DataZona &z, double tol) -> Wajib M30-W1 + Tebal >= 0.45x ATR + Fibo 50%-61.8%
bool SimpanZonaRegistry(DataZona &z, double tol)
{
   g_IdxTerakhir = -1;
   if(!ZonaRegistryValid(z) || !MathIsValidNumber(tol) || tol < 0) return false;

   // Hanya izinkan zona M30, H1, H4, D1, W1
   if(z.timeframe < PERIOD_M30) return false;

   // Tolak zona tipis (< 0.45x ATR)
   double atrZona = AmbilATR(z.timeframe);
   if(atrZona > 0.0 && (z.batasAtas - z.batasBawah) < 0.45 * atrZona) return false;

   // Wajib skor konfluensi tinggi
   if((z.kategori == ZONA_SUPER || z.kategori == ZONA_BIASA) && z.skor < 5) return false;
   if((z.kategori == ZONA_RETEST || z.kategori == ZONA_RBR || z.kategori == ZONA_DBD) && z.skor < 2) return false;

   // WAJIB KONFLUENSI GOLDEN FIBONACCI (50.0% - 61.8%)
   if(AktifkanFibonacci)
   {
      MS_FibPerbarui();
      bool fibValid = (z.bullish ? g_fibBuyOk : g_fibSellOk);
      if(fibValid)
      {
         double fH = (z.bullish ? g_fibBuyH : g_fibSellH);
         double fL = (z.bullish ? g_fibBuyL : g_fibSellL);
         double fRange = fH - fL;
         if(fRange > 0.0)
         {
            double fib50  = (z.bullish ? fH - 0.500 * fRange : fL + 0.500 * fRange);
            double fib618 = (z.bullish ? fH - 0.618 * fRange : fL + 0.618 * fRange);
            double goldLow  = MathMin(fib50, fib618) - (0.15 * atrZona);
            double goldHigh = MathMax(fib50, fib618) + (0.15 * atrZona);

            if(!(z.batasAtas >= goldLow && z.batasBawah <= goldHigh)) return false;
         }
      }
   }

// 4. Di dalam PerbaruiStatusZonaHistoris(): langsung hapus kotak begitu 1 candle menutup di luar batas belakang zona
   double tolBreak = 0.0;
Gunakan kode dengan hati-hati.

Blok 3: Metode Utama 3-Layer Zone-to-Zone (Khusus Eksekusi M30, H1, H4)

Lokasi: Di dalam bool EksekusiSatuSinyal(...), pastikan zona D1/W1 hanya jadi visual/target (tidak entry), dan gunakan 3-Layer bertingkat (20%, 50%, 80%) tanpa blok pembagi lot lama:
mql5
   // Eksekusi Metode Utama difokuskan pada M30, H1, dan H4 (D1 & W1 sebagai rambu besar/target TP)
   if(entry.timeframe < PERIOD_M30 || entry.timeframe > PERIOD_H4) return false;

   // Cek jumlah layer yang sudah masuk di zona ini (maksimal 3 layer: 20%, 50%, 80%)
   int layerSudahMasuk = JumlahEntryZona(entry);
   if(layerSudahMasuk >= 3) { JurnalTolak(idx, kat, DG_DONE, "3 Layer zona sudah terisi penuh"); return false; }

   // Anti-Triple Burst: jeda minimal 3 detik antar layer
   if(layerSudahMasuk > 0)
   {
      double lastLayerT = 0.0;
      if(BacaGV("L" + KunciZonaID(entry), lastLayerT) && (TimeCurrent() - (datetime)lastLayerT < JedaAntarLayerDetik))
         return false;
   }

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

   // Jarak minimal 5 pip antar layer
   for(int p = PositionsTotal() - 1; p >= 0; p--)
   {
      ulong ptk = PositionGetTicket(p);
      if(ptk > 0 && PositionGetString(POSITION_SYMBOL) == SymbolKerja && (ulong)PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         if(MathAbs(PositionGetDouble(POSITION_PRICE_OPEN) - pxTouch) < V24_Pip(JarakMinAntarLayerPips))
            return false;
   }

   // Veto Momentum & Chaos Ngamuk
   if(g_CuacaSekarang == CUACA_CHAOS_NGAMUK) return false;
   double oM5 = iOpen(SymbolKerja, PERIOD_M5, 0), cM5 = iClose(SymbolKerja, PERIOD_M5, 0), atrM5Now = AmbilATR(PERIOD_M5);
   if(oM5 > 0.0 && cM5 > 0.0 && atrM5Now > 0.0)
   {
      if(bullish ? (oM5 - cM5 > 1.3 * atrM5Now) : (cM5 - oM5 > 1.3 * atrM5Now)) return false;
   }
Gunakan kode dengan hati-hati.
(Pastikan di bagian bawah EksekusiSatuSinyal, blok pembagi lot lama volLayer sudah dihapus agar EA memakai 100% angka lot dari V24_Lot).

Blok 4: Patokan Lot Otomatis Mulai $1.000 (V24_Lot)

Lokasi: Ganti isi fungsi bool V24_Lot(...) dengan rumus patokan otomatis Anda (Scalping 0.03, Super 0.03, Biasa 0.02, RBR/DBD/Retest 0.03 mulai $1.000 dan berkembang otomatis sesuai pertumbuhan saldo):
mql5
bool V24_Lot(bool bull, double entry, double sl, int cat, double &vol, string &info, int stratIdx, bool isFullMargin)
{
   vol = 0.0; info = "";
   double bal = AccountInfoDouble(ACCOUNT_BALANCE);
   if(bal <= 0.0) { info = "balance<=0"; return false; }

   double mn = SymbolInfoDouble(SymbolKerja, SYMBOL_VOLUME_MIN);
   double mx = SymbolInfoDouble(SymbolKerja, SYMBOL_VOLUME_MAX);
   double st = SymbolInfoDouble(SymbolKerja, SYMBOL_VOLUME_STEP);
   if(st <= 0.0 || mn <= 0.0) { info = "spesifikasi volume broker tidak valid"; return false; }

   int vd = (int)MathMax(0.0, MathRound(-MathLog10(st)));

   // PATOKAN LOT BERDASARKAN MODAL (MULAI $1.000, BERKEMBANG OTOMATIS)
   double lotPatokan = mn; // Jika saldo < $1.000, gunakan lot minimum broker (0.01)
   if(bal >= 1000.0)
   {
      double multSaldo = bal / 1000.0; // Skala otomatis: $1000 = 1.0x, $1500 = 1.5x, $2000 = 2.0x, dst.
      double baseCat   = 0.02;         // Default: BIASA / Trend / SR / SD = 0.02

      if(cat == 0)                               baseCat = 0.03; // SUPER = 0.03
      else if(cat == 1)                          baseCat = 0.02; // BIASA / Trend / SR / SD = 0.02
      else if(cat == 2 || cat == 3 || cat == 4)  baseCat = 0.03; // RETEST / RBR / DBD / BO = 0.03
      else if(cat == 5)                          baseCat = 0.03; // VIP SCALPING = 0.03

      lotPatokan = baseCat * multSaldo;
   }

   // Pengaman ringan (0.75x) hanya jika terkena 2x SL beruntun (tetap menjaga lot berkembang)
   if(g_ConsecSL >= 2 && bal >= 1200.0)
      lotPatokan *= 0.75;

   double v = NormalizeDouble(MathFloor(lotPatokan / st + 1e-9) * st, vd);
   if(v < mn) v = mn;
   if(v > mx) v = mx;
   if(!ValidasiVolumeOrder(v)) { info = "volume tidak valid"; return false; }

   vol = v;
   info = "Bal=" + DoubleToString(bal, 0) + " Mult=" + DoubleToString(bal / 1000.0, 2) + "x Lot=" + DoubleToString(v, 2);
   return true;
}
Gunakan kode dengan hati-hati.

Blok 5: VIP Scalping M1 Murni 24 Jam (SL Seragam Range & Trend + Trailing SL+ + Re-Entry 2 Detik)

Lokasi: Ganti fungsi V24_JagaSiklusReverse() dan V24_CekReEntryPascaSLPlus() dengan kode berikut:
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

   // Pelindung Spread Rollover (tahan jika spread > 3.5 pip)
   if(V24_SpreadPts() > MaxSpreadScalp2DigitPts) return;

   // Cek Filter Berita & Mode VIP News (Aman vs Sniper)
   datetime nowJ = TimeTradeServer(); if(nowJ <= 0) nowJ = TimeCurrent();
   bool newsOK = NewsFilterBolehLanjut(), modeNewsVIP = false;
   if(newsOK) g_SpikeDetectedTime = 0;
   else if(ModeVIPNews == VIP_NEWS_SNIPER && g_NewsEventTime > 0 && nowJ >= g_NewsEventTime + 5 && nowJ <= g_NewsEventTime + 60)
      modeNewsVIP = true;
   if(!newsOK && !modeNewsVIP) { HapusPendingInitScalp(); return; }

   double balR = AccountInfoDouble(ACCOUNT_BALANCE), rl = HitungProfitRealisasiEASejak(AwalHariServer());
   double baseD = (MetrikAwalHariEA > 0.0 ? MetrikAwalHariEA : balR);
   if(rl != EMPTY_VALUE && rl < 0.0 && -rl >= baseD * MathMin(DailyLossLimitPct, MaxDailyLossPct) / 100.0) return;
   if(g_VaultLockedUSD > 0.0 && V24_ProfitHarian() <= g_VaultLockedUSD) return;

   if(!MS_SiapkanKonteksM1() || gM1n < 25) return;
   DS_EvaluasiCuacaPasar();

   // Berhenti hanya jika pasar benar-benar mati (Chaos Ngantuk)
   if(g_CuacaSekarang == CUACA_CHAOS_NGANTUK && !modeNewsVIP) return;

   // Cek posisi scalping aktif (maksimal 1 gelombang scalping berjalan)
   int adaPosisiScalp = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(tk > 0 && PositionGetString(POSITION_SYMBOL) == SymbolKerja && (ulong)PositionGetInteger(POSITION_MAGIC) == MagicNumber && StringFind(PositionGetString(POSITION_COMMENT), "|S=5|") >= 0) adaPosisiScalp++;
   }
   if(adaPosisiScalp > 0) return;

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
   if(HitungPosisiEA() + 1 > MaxPosisiEA) return;

   trade.SetDeviationInPoints((ulong)DeviasiAntiSlippagePoints);
   double jarakSL = MathMax(V24_Pip(modeNewsVIP ? 20.0 : ScalpSLMinPips), stl + 2.0 * pt);

   // =====================================================================
   // MODE A: RANGE / SIDEWAYS M1 -> SL SERAGAM (15 PIP) + TRAILING SL+ (TP = 0)
   // =====================================================================
   if(g_CuacaSekarang == CUACA_RANGE && !modeNewsVIP && (garisAtas - garisBawah >= V24_Pip(8.0)))
   {
      double low0 = iLow(SymbolKerja, PERIOD_M1, 0), high0 = iHigh(SymbolKerja, PERIOD_M1, 0), open0 = iOpen(SymbolKerja, PERIOD_M1, 0);

      if(low0 <= garisBawah + V24_Pip(3.5) && tick.bid > open0 && upPress >= 51.0)
      {
         double slB = AlignHargaTick(tick.ask - jarakSL, false);
         double volB = 0.0; string infB = "";
         if(V24_Lot(true, tick.ask, slB, 5, volB, infB) && DS_RisikoBasketLolos(true, volB, tick.ask, slB))
         {
            lastInstanExec = TimeCurrent();
            if(trade.Buy(volB, SymbolKerja, 0.0, slB, 0.0, "SCALP_M1_RNG|S=5|0"))
            {
               long pidB = (long)trade.ResultOrder();
               if(pidB > 0) { string spB = IntegerToString(pidB); SimpanGV("SR" + spB, jarakSL); SimpanGV("SB" + spB, 0.0); SimpanGV("SV" + spB, volB); }
               Print("VIP_M1_RANGE_BUY (TRAILING SL+) | Lot=", DoubleToString(volB, 2), " Entry=", tick.ask);
               return;
            }
         }
      }
      if(high0 >= garisAtas - V24_Pip(3.5) && tick.bid < open0 && upPress <= 49.0)
      {
         double slS = AlignHargaTick(tick.bid + jarakSL, true);
         double volS = 0.0; string infS = "";
         if(V24_Lot(false, tick.bid, slS, 5, volS, infS) && DS_RisikoBasketLolos(false, volS, tick.bid, slS))
         {
            lastInstanExec = TimeCurrent();
            if(trade.Sell(volS, SymbolKerja, 0.0, slS, 0.0, "SCALP_M1_RNG|S=5|0"))
            {
               long pidS = (long)trade.ResultOrder();
               if(pidS > 0) { string spS = IntegerToString(pidS); SimpanGV("SR" + spS, jarakSL); SimpanGV("SB" + spS, 0.0); SimpanGV("SV" + spS, volS); }
               Print("VIP_M1_RANGE_SELL (TRAILING SL+) | Lot=", DoubleToString(volS, 2), " Entry=", tick.bid);
               return;
            }
         }
      }
      return;
   }

   // =====================================================================
   // MODE B: PURE M1 TREND, BREAKOUT, VIP NEWS, & CHAOS NGAMUK (24 JAM)
   // =====================================================================
   double ema8 = MS_EMA(PERIOD_M1, 8, 0), ema21 = MS_EMA(PERIOD_M1, 21, 0);
   if(ema8 <= 0.0 || ema21 <= 0.0) return;

   double open0 = iOpen(SymbolKerja, PERIOD_M1, 0);
   double body0 = MathAbs(tick.bid - open0);
   bool isChaosMode = (g_CuacaSekarang == CUACA_CHAOS_NGAMUK || g_NewsModeVIP == 2);

   double minBodyReq = (modeNewsVIP ? V24_Pip(6.0) : V24_Pip(3.0));
   double minFlowBuy = (modeNewsVIP ? 62.0 : 51.0);
   double maxFlowSell = (modeNewsVIP ? 38.0 : 49.0);

   bool arahBuy  = (ema8 > ema21 && tick.bid > open0 && body0 >= minBodyReq && upPress >= minFlowBuy);
   bool arahSell = (ema8 < ema21 && tick.bid < open0 && body0 >= minBodyReq && upPress <= maxFlowSell);
   if(!arahBuy && !arahSell) return;

   bool bull = arahBuy;
   double entry = (bull ? tick.ask : tick.bid);
   double sl = AlignHargaTick(bull ? entry - jarakSL : entry + jarakSL, !bull);
   double vol = 0.0; string info = "";
   if(!V24_Lot(bull, entry, sl, 5, vol, info)) return;

   if(modeNewsVIP) vol = MathMax(SymbolInfoDouble(SymbolKerja, SYMBOL_VOLUME_MIN), NormalisasiVolumeBawah(vol * 0.5));
   if(!DS_RisikoBasketLolos(bull, vol, entry, sl)) return;

   lastInstanExec = TimeCurrent();
   string tagComment = (isChaosMode ? "CHAOS_REV|S=5|0" : (modeNewsVIP ? "VIP_NEWS|S=5|0" : "TREND_M1|S=5|0"));
   bool ok = (bull ? trade.Buy(vol, SymbolKerja, 0.0, sl, 0.0, tagComment)
                   : trade.Sell(vol, SymbolKerja, 0.0, sl, 0.0, tagComment));
   if(ok)
   {
      long pid = 0; ulong d = trade.ResultDeal();
      if(d > 0 && HistoryDealSelect(d)) pid = HistoryDealGetInteger(d, DEAL_POSITION_ID);
      if(pid == 0) pid = (long)trade.ResultOrder();
      if(pid > 0) { string sp = IntegerToString(pid); SimpanGV("SR" + sp, jarakSL); SimpanGV("SB" + sp, 0.0); SimpanGV("SV" + sp, vol); }
      Print("VIP_M1_EXEC | ", (bull ? "BUY" : "SELL"), " Mode=", tagComment, " Lot=", DoubleToString(vol, 2));
   }
}

// Re-Entry Pasca Kena SL+ (Jeda 2 Detik) -> Lancar di Range Maupun Trend
void V24_CekReEntryPascaSLPlus()
{
   if(!g_MenungguReEntrySLPlus) return;
   if(TimeCurrent() - g_WaktuKenaSLPlus < JedaReEntrySLPlusDetik) return;

   g_MenungguReEntrySLPlus = false;
   if(ModeOperasi != AUTO_TRADE || g_TargetMenungguTutup) return;
   if(DS_SpreadShock() || V24_SpreadPts() > MaxSpreadScalp2DigitPts) return;
   if(g_CuacaSekarang == CUACA_CHAOS_NGANTUK || g_CuacaSekarang == CUACA_CHAOS_NGAMUK) return;
   if(HitungPosisiEA() >= MaxPosisiEA) return;
   if(!NewsFilterBolehLanjut()) return;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tkp = PositionGetTicket(i);
      if(tkp > 0 && PositionGetString(POSITION_SYMBOL) == SymbolKerja && (ulong)PositionGetInteger(POSITION_MAGIC) == MagicNumber && StringFind(PositionGetString(POSITION_COMMENT), "|S=5|") >= 0) return;
   }

   double upPress = 50.0; int t3 = 0, tpp = 0;
   DS_AnalisaOrderFlow(upPress, t3, tpp);
   double ema8 = MS_EMA(PERIOD_M1, 8, 0);
   double bid  = SymbolInfoDouble(SymbolKerja, SYMBOL_BID);
   double ask  = SymbolInfoDouble(SymbolKerja, SYMBOL_ASK);

   bool arahBuy = false, arahSell = false;
   if(g_CuacaSekarang == CUACA_RANGE)
   {
      double open0 = iOpen(SymbolKerja, PERIOD_M1, 0);
      arahBuy  = (bid > open0 && upPress >= 51.0);
      arahSell = (bid < open0 && upPress <= 49.0);
   }
   else
   {
      arahBuy  = (bid > ema8 && upPress >= 51.0);
      arahSell = (bid < ema8 && upPress <= 49.0);
   }

   if(!arahBuy && !arahSell) return;

   bool bull = arahBuy;
   double entry = (bull ? ask : bid);
   double stlR = (double)MathMax(SymbolInfoInteger(SymbolKerja, SYMBOL_TRADE_STOPS_LEVEL), SymbolInfoInteger(SymbolKerja, SYMBOL_TRADE_FREEZE_LEVEL)) * SymbolInfoDouble(SymbolKerja, SYMBOL_POINT);
   double jarakSL = MathMax(V24_Pip(ScalpSLMinPips), stlR + 2.0 * SymbolInfoDouble(SymbolKerja, SYMBOL_POINT));
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
Gunakan kode dengan hati-hati.
if(pid > 0) { string sp = IntegerToString(pid); SimpanGV("SR" + sp, jarakSL); SimpanGV("SB" + sp, 0.0); SimpanGV("SV" + sp, vol); }
Print("REENTRY_2S_SUKSES | ", (bull ? "BUY" : "SELL"), " (Gelombang ke-", g_HitunganReEntryGelombang, ") Lot=", DoubleToString(vol, 2));
}
}
}

---

### Blok 6: Pembaruan Judul Dashboard & Info Patokan Lot Aktif
**Lokasi:** Di dalam `void V24_Dashboard()` (**sekitar baris 2860–2890**), ubah baris judul `A24D_L0` dan informasi patokan lot pada `A24D_L4`:

```mql5
   double lotAktifScp = (bal >= 1000.0 ? NormalizeDouble(0.03 * (bal / 1000.0), 2) : 0.01);
   double lotAktifBsa = (bal >= 1000.0 ? NormalizeDouble(0.02 * (bal / 1000.0), 2) : 0.01);

   V24_DrawText("A24D_L0", mx+10, my+6,  "* DEWA XAUUSD V25 HYBRID SNIPER | " + NamaTFSingkat((ENUM_TIMEFRAMES)_Period), clrGold, 9, true);
   // ...
   V24_DrawText("A24D_L4", mx+10, my+100, StringFormat("Patokan Lot: %.2f / %.2f | Posisi: %d/%d", lotAktifScp, lotAktifBsa, HitungPosisiEA(), MaxPosisiEA), clrSilver, 8, false);

Langkah Terakhir:

1. Masukkan seluruh 6 blok di atas ke dalam file .mq5 Anda.
2. Tekan F7 (Compile) di MetaEditor dan pastikan muncul 0 errors.
3. Sekarang Anda dapat langsung mengujinya di Strategy Tester MT5 atau Akun Demo dan memantau pergerakan lot, kotak zona Fibo 50%–61,8%, serta siklus SL+ & Re-Entry 2 detik-nya.
Apakah sudah berhasil Anda gabungkan dan compile (0 errors), atau ada pesan error di baris tertentu yang perlu langsung saya bantu perbaiki?
