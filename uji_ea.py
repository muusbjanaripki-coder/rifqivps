Berikut adalah panduan pemasangan Dewa Trading XAUUSD Engine lengkap dari Bagian 1 sampai Bagian 7 yang sudah disusun berurutan, diperbaiki sintaksnya (seluruh indeks array [] dan komentar order sudah seragam), serta disesuaikan dengan Pilihan 2 (keamanan risiko tetap terjaga).
Ikuti urutan langkah dan patokan baris di bawah ini di MetaEditor (F4):

BAGIAN 1: Penyesuaian Pagar Risiko & Kapasitas Posisi (Input Parameters)

• Lokasi: Sekitar baris 92–95 dan baris 152 pada file .mq5 Anda.
• Cara Mencari: Tekan Ctrl + F, cari DailyLossLimitPct dan MaxPosisiEA.
• Instruksi: Pertahankan batas risiko aman Anda (sesuai Pilihan 2 agar tidak over-exposure). Lewati baris ScalpMaxPosisi jika variabel tersebut memang tidak ada di file dasar Anda.
cpp
// Sekitar baris 92-94 (Pertahankan batas aman Anda)
input double DailyLossLimitPct   = 8.0;   // Batas rugi harian 8% (atau sesuaikan dengan profil aman Anda)
input double MaxRiskPerBasketPct = 6.0;   // Tetap 6% sesuai batas aman awal (Pilihan 2)
input double MaxDailyLossPct     = 8.0;   // Diselaraskan ke 8%

// Sekitar baris 152 (Cari MaxPosisiEA)
input int    MaxPosisiEA         = 10;    // Tetap 10 posisi maksimal agar margin terjaga
Gunakan kode dengan hati-hati.

BAGIAN 2: Upgrade Kokpit Visual Obsidian Institutional

• Lokasi: Sekitar baris 546–662 pada file .mq5 Anda.
• Cara Mencari: Tekan Ctrl + F, ketik color WarnaKotakZona.
• Instruksi (Ganti Fungsi): Ganti seluruh fungsi WarnaKotakZona dan TerapkanTemaChart yang lama dengan kode di bawah ini:
cpp
// Kotak zona: Obsidian Slate untuk BUY, Dark Maroon untuk SELL
color WarnaKotakZona(DataZona &z)
{
   if(AktifkanTemaChart) return (z.bullish ? C'18,45,68' : C'68,22,32');
   return WarnaZona(z,false);
}

// Tema Chart Obsidian Institutional Pro
void TerapkanTemaChart()
{
   if(!AktifkanTemaChart) return;
   ChartSetInteger(0,CHART_MODE,CHART_CANDLES);
   ChartSetInteger(0,CHART_COLOR_BACKGROUND,C'11,14,20');    // Deep Obsidian Dark
   ChartSetInteger(0,CHART_COLOR_FOREGROUND,C'210,218,230'); // Silver White Text
   ChartSetInteger(0,CHART_COLOR_GRID,C'22,28,38');
   ChartSetInteger(0,CHART_SHOW_GRID,false);                 // Bersih tanpa grid
   ChartSetInteger(0,CHART_COLOR_CHART_UP,C'0,230,138');     // Emerald Green Outline
   ChartSetInteger(0,CHART_COLOR_CHART_DOWN,C'255,68,92');   // Coral Crimson Outline
   ChartSetInteger(0,CHART_COLOR_CANDLE_BULL,C'0,230,138');  // Emerald Green Body
   ChartSetInteger(0,CHART_COLOR_CANDLE_BEAR,C'255,68,92');  // Coral Crimson Body
   ChartSetInteger(0,CHART_COLOR_CHART_LINE,clrGold);
   ChartSetInteger(0,CHART_COLOR_VOLUME,C'60,75,95');
   ChartSetInteger(0,CHART_COLOR_ASK,C'255,100,120');
   ChartSetInteger(0,CHART_COLOR_BID,clrGold);
   ChartSetInteger(0,CHART_COLOR_LAST,clrAqua);
   ChartSetInteger(0,CHART_COLOR_STOP_LEVEL,C'120,130,150');
   ChartRedraw(0);
}
Gunakan kode dengan hati-hati.

BAGIAN 3: Mesin Utama Dewa Sniper (Auto Trendline, Order Flow, Chaos Hunter, & Deteksi Range)

• Lokasi: Sekitar baris 1470–1518 pada file .mq5 Anda.
• Cara Mencari: Tekan Ctrl + F, ketik bool g_ScalpModeRangeTerkunci (atau bool MS_M1SedangRange()).
• Instruksi (Ganti Variabel & Fungsi): Blok dan hapus variabel g_ScalpModeRangeTerkunci, g_WaktuKunciScalpMode, serta seluruh isi fungsi MS_M1SedangRange() lama, lalu tempelkan kode di bawah ini:
cpp
// =========================================================================
// DEWA TRADING XAUUSD ENGINE: 5-CORE ARCHITECTURE
// 1. Auto Trendline (Miring + Datar) | 2. Order Flow & Tick Exhaustion
// 3. Chaos & Whipsaw Hunter         | 4. ATR Squeeze Detector
// 5. House Money Vault & Confluence Lock
// =========================================================================
struct TrendlineChannel
{
   bool valid;
   bool isFlat;
   datetime tA1, tA2;
   double   pA1, pA2;
   datetime tB1, tB2;
   double   pB1, pB2;
};

TrendlineChannel g_TL_M1;

// Memori Tick Real-Time (Bid-Ask Pressure & Tick Exhaustion)
double   g_TickPrices[60];
datetime g_TickTimes[60];
int      g_TickHead = 0;
double   g_AvgSpreadPts = 0.0;
double   g_LastUpPressure = 50.0;
bool     g_MarketChaos = false;
bool     g_MarketSqueeze = false;
double   g_VaultLockedUSD = 0.0;

void DS_CatatTick(double bid, double spreadPts)
{
   if(bid <= 0.0) return;
   g_TickPrices[g_TickHead] = bid;
   g_TickTimes[g_TickHead]  = TimeCurrent();
   g_TickHead = (g_TickHead + 1) % 60;

   if(g_AvgSpreadPts <= 0.0) g_AvgSpreadPts = spreadPts;
   else g_AvgSpreadPts = g_AvgSpreadPts * 0.95 + spreadPts * 0.05;
}

void DS_AnalisaOrderFlow(double &upPressurePct, int &tick3s, int &tickPrev)
{
   upPressurePct = 50.0;
   tick3s = 0;
   tickPrev = 0;
   datetime now = TimeCurrent();
   int up = 0, dn = 0;

   for(int i = 0; i < 59; i++)
   {
      int idxNow  = (g_TickHead - 1 - i + 60) % 60;
      int idxPrev = (g_TickHead - 2 - i + 60) % 60;
      if(g_TickPrices[idxNow] <= 0.0 || g_TickPrices[idxPrev] <= 0.0) continue;

      long age = (long)(now - g_TickTimes[idxNow]);
      if(age <= 3) tick3s++;
      else if(age <= 8) tickPrev++;

      if(age <= 10)
      {
         if(g_TickPrices[idxNow] > g_TickPrices[idxPrev]) up++;
         else if(g_TickPrices[idxNow] < g_TickPrices[idxPrev]) dn++;
      }
   }
   if(up + dn > 0) upPressurePct = (double)up / (double)(up + dn) * 100.0;
   g_LastUpPressure = upPressurePct;
}

bool DS_SpreadShock()
{
   double curSp = (double)SymbolInfoInteger(SymbolKerja, SYMBOL_SPREAD);
   return (g_AvgSpreadPts > 0.0 && curSp > g_AvgSpreadPts * 1.80);
}

bool DS_DekatAngkaPsikologis(double harga)
{
   double rem = MathMod(harga, 0.50);
   if(rem < 0) rem += 0.50;
   return (MathMin(rem, 0.50 - rem) <= V24_Pip(3.0));
}

// Otak Ke-5: Chaos & Whipsaw Hunter + ATR Squeeze Detector
void DS_EvaluasiCuacaPasar()
{
   g_MarketChaos = false;
   g_MarketSqueeze = false;
   if(gM1n < 20 || g_atr1 <= 0.0) return;

   // 1. Cek Chaos / Market Ngamuk (ekor panjang saling menelan > 65% pada 5 candle terakhir)
   int candleLiar = 0;
   for(int i = 1; i <= 5; i++)
   {
      double rng  = gM1[i].high - gM1[i].low;
      double body = MathAbs(gM1[i].close - gM1[i].open);
      if(rng > 0.0 && (rng - body) / rng >= 0.65 && rng >= V24_Pip(8.0))
         candleLiar++;
   }
   if(candleLiar >= 3) g_MarketChaos = true;

   // 2. Cek ATR Squeeze (penyempitan volatilitas sebelum ledakan)
   double sumRng = 0.0;
   for(int k = 1; k <= 5; k++) sumRng += (gM1[k].high - gM1[k].low);
   if((sumRng / 5.0) < g_atr1 * 0.55) g_MarketSqueeze = true;

   // 3. Update House Money Vault (kunci 70% profit harian saat profit > 3% saldo)
   double pnlH = V24_ProfitHarian();
   double bal  = AccountInfoDouble(ACCOUNT_BALANCE);
   if(bal > 0.0 && pnlH > bal * 0.03)
      g_VaultLockedUSD = MathMax(g_VaultLockedUSD, pnlH * 0.70);
}

double TL_HargaPadaWaktu(datetime t1, double p1, datetime t2, double p2, datetime tTarget)
{
   if(t2 <= t1) return p2;
   double slope = (p2 - p1) / (double)(t2 - t1);
   return p1 + slope * (double)(tTarget - t1);
}

bool TL_Bangun(ENUM_TIMEFRAMES tf, int scanBars, int lb, TrendlineChannel &out)
{
   out.valid = false;
   MqlRates r[];
   ArraySetAsSeries(r, true);
   int got = CopyRates(SymbolKerja, tf, 0, scanBars + lb + 5, r);
   if(got < lb * 2 + 10) return false;

   int idxH[2] = {-1, -1}, nh = 0;
   int idxL[2] = {-1, -1}, nl = 0;

   for(int i = lb + 1; i <= scanBars && i + lb < got; i++)
   {
      if(nh < 2)
      {
         bool sh = true;
         for(int k = 1; k <= lb; k++)
            if(r[i].high <= r[i-k].high || r[i].high <= r[i+k].high) { sh = false; break; }
         if(sh) idxH[nh++] = i;
      }
      if(nl < 2)
      {
         bool sl = true;
         for(int k = 1; k <= lb; k++)
            if(r[i].low >= r[i-k].low || r[i].low >= r[i+k].low) { sl = false; break; }
         if(sl) idxL[nl++] = i;
      }
      if(nh == 2 && nl == 2) break;
   }
   if(nh < 2 || nl < 2) return false;

   out.tA1 = r[idxH[1]].time; out.pA1 = r[idxH[1]].high;
   out.tA2 = r[idxH[0]].time; out.pA2 = r[idxH[0]].high;
   out.tB1 = r[idxL[1]].time; out.pB1 = r[idxL[1]].low;
   out.tB2 = r[idxL[0]].time; out.pB2 = r[idxL[0]].low;

   if(MathAbs(out.pA2 - out.pA1) < V24_Pip(4.0) && MathAbs(out.pB2 - out.pB1) < V24_Pip(4.0))
   {
      double avgA = 0.5 * (out.pA1 + out.pA2);
      double avgB = 0.5 * (out.pB1 + out.pB2);
      out.pA1 = out.pA2 = avgA;
      out.pB1 = out.pB2 = avgB;
      out.isFlat = true;
   }
   else out.isFlat = false;

   datetime nowT = r[0].time;
   double upNow = TL_HargaPadaWaktu(out.tA1, out.pA1, out.tA2, out.pA2, nowT);
   double dnNow = TL_HargaPadaWaktu(out.tB1, out.pB1, out.tB2, out.pB2, nowT);
   if(upNow <= dnNow + V24_Pip(5.0)) return false;

   out.valid = true;
   return true;
}

// Visual Kokpit: Gambar Auto Trendline (Cyan & Gold), Midline (Silver), dan Label HUD Status di Chart
void TL_GambarChart()
{
   ENUM_TIMEFRAMES ctf = (ENUM_TIMEFRAMES)_Period;
   TrendlineChannel tl;
   int barsScan = (ctf == PERIOD_M1 ? 35 : 85);
   int lb       = (ctf == PERIOD_M1 ? 2  : 3);

   if(!TL_Bangun(ctf, barsScan, lb, tl))
   {
      ObjectDelete(0, "A24_TL_UP");
      ObjectDelete(0, "A24_TL_DN");
      ObjectDelete(0, "A24_TL_MID");
      ObjectDelete(0, "A24_TL_HUD");
      return;
   }

   int sec = PeriodSeconds(ctf); if(sec <= 0) sec = 60;
   datetime tEnd = iTime(SymbolKerja, ctf, 0) + (datetime)(sec * 12);
   double pUpEnd = TL_HargaPadaWaktu(tl.tA1, tl.pA1, tl.tA2, tl.pA2, tEnd);
   double pDnEnd = TL_HargaPadaWaktu(tl.tB1, tl.pB1, tl.tB2, tl.pB2, tEnd);

   string nUp = "A24_TL_UP", nDn = "A24_TL_DN", nMid = "A24_TL_MID", nHud = "A24_TL_HUD";
   if(ObjectFind(0, nUp) < 0) ObjectCreate(0, nUp, OBJ_TREND, 0, tl.tA1, tl.pA1, tEnd, pUpEnd);
   else { ObjectMove(0, nUp, 0, tl.tA1, tl.pA1); ObjectMove(0, nUp, 1, tEnd, pUpEnd); }
   ObjectSetInteger(0, nUp, OBJPROP_COLOR, clrAqua);
   ObjectSetInteger(0, nUp, OBJPROP_WIDTH, 2);
   ObjectSetInteger(0, nUp, OBJPROP_STYLE, tl.isFlat ? STYLE_DASH : STYLE_SOLID);
   ObjectSetInteger(0, nUp, OBJPROP_RAY_RIGHT, false);
   ObjectSetInteger(0, nUp, OBJPROP_SELECTABLE, false);

   if(ObjectFind(0, nDn) < 0) ObjectCreate(0, nDn, OBJ_TREND, 0, tl.tB1, tl.pB1, tEnd, pDnEnd);
   else { ObjectMove(0, nDn, 0, tl.tB1, tl.pB1); ObjectMove(0, nDn, 1, tEnd, pDnEnd); }
   ObjectSetInteger(0, nDn, OBJPROP_COLOR, clrGold);
   ObjectSetInteger(0, nDn, OBJPROP_WIDTH, 2);
   ObjectSetInteger(0, nDn, OBJPROP_STYLE, tl.isFlat ? STYLE_DASH : STYLE_SOLID);
   ObjectSetInteger(0, nDn, OBJPROP_RAY_RIGHT, false);
   ObjectSetInteger(0, nDn, OBJPROP_SELECTABLE, false);

   datetime tMidStart = MathMax(tl.tA1, tl.tB1);
   double pMid1 = 0.5 * (TL_HargaPadaWaktu(tl.tA1, tl.pA1, tl.tA2, tl.pA2, tMidStart) + TL_HargaPadaWaktu(tl.tB1, tl.pB1, tl.tB2, tl.pB2, tMidStart));
   double pMid2 = 0.5 * (pUpEnd + pDnEnd);
   if(ObjectFind(0, nMid) < 0) ObjectCreate(0, nMid, OBJ_TREND, 0, tMidStart, pMid1, tEnd, pMid2);
   else { ObjectMove(0, nMid, 0, tMidStart, pMid1); ObjectMove(0, nMid, 1, tEnd, pMid2); }
   ObjectSetInteger(0, nMid, OBJPROP_COLOR, C'120,135,155');
   ObjectSetInteger(0, nMid, OBJPROP_WIDTH, 1);
   ObjectSetInteger(0, nMid, OBJPROP_STYLE, STYLE_DOT);
   ObjectSetInteger(0, nMid, OBJPROP_RAY_RIGHT, false);
   ObjectSetInteger(0, nMid, OBJPROP_SELECTABLE, false);

   // Label Status Visual di Ujung Trendline
   if(ObjectFind(0, nHud) < 0) ObjectCreate(0, nHud, OBJ_TEXT, 0, tEnd, pUpEnd);
   else ObjectMove(0, nHud, 0, tEnd, pUpEnd);
   string hudTxt = (g_MarketChaos ? "[CHAOS HUNTER AKTIF]" : (g_MarketSqueeze ? "[SQUEEZE - SIAP LEDAK]" : "[DEWA SNIPER TL]"));
   ObjectSetString(0, nHud, OBJPROP_TEXT, hudTxt);
   ObjectSetInteger(0, nHud, OBJPROP_COLOR, g_MarketChaos ? clrTomato : (g_MarketSqueeze ? clrGold : clrSpringGreen));
   ObjectSetString(0, nHud, OBJPROP_FONT, "Consolas Bold");
   ObjectSetInteger(0, nHud, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, nHud, OBJPROP_ANCHOR, ANCHOR_LEFT_LOWER);
   ObjectSetInteger(0, nHud, OBJPROP_SELECTABLE, false);
}

int TL_KonfluensiSMC(bool bullish, ENUM_TIMEFRAMES tf, double zLow, double zHigh)
{
   TrendlineChannel tl;
   if(!TL_Bangun(tf, 90, 3, tl)) return 0;
   datetime nowT = iTime(SymbolKerja, tf, 0);
   double upNow = TL_HargaPadaWaktu(tl.tA1, tl.pA1, tl.tA2, tl.pA2, nowT);
   double dnNow = TL_HargaPadaWaktu(tl.tB1, tl.pB1, tl.tB2, tl.pB2, nowT);
   double pad   = V24_Pip(8.0);
   if(bullish && dnNow >= zLow - pad && dnNow <= zHigh + pad) return 1;
   if(!bullish && upNow >= zLow - pad && upNow <= zHigh + pad) return 1;
   return 0;
}

bool g_ScalpModeRangeTerkunci = true;
datetime g_WaktuKunciScalpMode = 0;

bool MS_M1SedangRange()
{
   if(g_NewsModeVIP > 0 || g_MarketSqueeze)
   {
      g_ScalpModeRangeTerkunci = false;
      g_WaktuKunciScalpMode = TimeCurrent();
      return false;
   }

   if(!TL_Bangun(PERIOD_M1, 35, 2, g_TL_M1))
      return true;

   datetime t1 = iTime(SymbolKerja, PERIOD_M1, 1);
   double c1   = iClose(SymbolKerja, PERIOD_M1, 1);
   double up1  = TL_HargaPadaWaktu(g_TL_M1.tA1, g_TL_M1.pA1, g_TL_M1.tA2, g_TL_M1.pA2, t1);
   double dn1  = TL_HargaPadaWaktu(g_TL_M1.tB1, g_TL_M1.pB1, g_TL_M1.tB2, g_TL_M1.pB2, t1);

   bool diDalamLorong = (c1 <= up1 + V24_Pip(2.0) && c1 >= dn1 - V24_Pip(2.0));
   datetime now = TimeCurrent();
Gunakan kode dengan hati-hati.
if(g_WaktuKunciScalpMode == 0 || (diDalamLorong != g_ScalpModeRangeTerkunci && now - g_WaktuKunciScalpMode >= 60))
{
g_ScalpModeRangeTerkunci = diDalamLorong;
g_WaktuKunciScalpMode = now;
}
return g_ScalpModeRangeTerkunci;
}

---

### BAGIAN 4: Integrasi Konfluensi Trendline HTF ke SMC/ICT (`EksekusiSatuSinyal`)
* **Lokasi:** Sekitar **baris 1105–1115** di dalam fungsi `EksekusiSatuSinyal`.
* **Cara Mencari:** Tekan `Ctrl + F`, ketik `if(V24_TrendDir()==(bullish?1:-1)) v24sk++;`.
* **Instruksi (Tambahkan 1 Baris):** Tempelkan 1 baris di bawahnya:

```cpp
      if(V24_TrendDir()==(bullish?1:-1)) v24sk++;
      v24sk += TL_KonfluensiSMC(bullish, entry.timeframe, entry.batasBawah, entry.batasAtas);

BAGIAN 5: Mesin Eksekusi Utama Dewa Sniper (V24_JagaSiklusReverse)

• Lokasi: Sekitar baris 1803–1946 pada file .mq5 Anda.
• Cara Mencari: Tekan Ctrl + F, ketik void V24_JagaSiklusReverse().
• Instruksi (Ganti Seluruh Fungsi): Blok dan ganti seluruh isi fungsi V24_JagaSiklusReverse() (sampai tepat di atas void V24_KelolaSemua()) dengan kode bersih berikut (indeks array rsiArr[0] & gM1[1] sudah diperbaiki, komentar order diseragamkan, dan cek risiko basket dikembalikan):
cpp
void V24_JagaSiklusReverse()
{
   if(!ScalpReverseAktif || ModeOperasi != AUTO_TRADE || g_TargetMenungguTutup)
   {
      HapusSemuaPendingReverseScalp();
      HapusPendingInitScalp();
      return;
   }

   MqlTick tick;
   if(!SymbolInfoTick(SymbolKerja, tick) || tick.bid <= 0.0 || tick.ask <= 0.0) return;

   // 1. Rekam Tick Real-Time & Cek Spread Shock Absorber
   DS_CatatTick(tick.bid, (double)SymbolInfoInteger(SymbolKerja, SYMBOL_SPREAD));
   if(DS_SpreadShock()) return;

   // 2. Gerbang Pengaman: Berita, Spread, House Money Vault, Daily Loss, & Basket Risk
   datetime nowJ    = TimeTradeServer(); if(nowJ <= 0) nowJ = TimeCurrent();
   bool newsOK      = NewsFilterBolehLanjut();
   bool modeNewsVIP = false;
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
   if((int)SymbolInfoInteger(SymbolKerja, SYMBOL_SPREAD) > limSpread) { HapusPendingInitScalp(); return; }

   {
      double balR       = AccountInfoDouble(ACCOUNT_BALANCE);
      double rl         = HitungProfitRealisasiEASejak(AwalHariServer());
      double baseD      = (MetrikAwalHariEA > 0.0 ? MetrikAwalHariEA : balR);
      double limitMoney = baseD * MathMin(DailyLossLimitPct, MaxDailyLossPct) / 100.0;
      if(rl != EMPTY_VALUE && rl < 0.0 && -rl >= limitMoney) { HapusPendingInitScalp(); return; }
      if(g_VaultLockedUSD > 0.0 && V24_ProfitHarian() <= g_VaultLockedUSD) { HapusPendingInitScalp(); return; }

      double br = HitungRisikoTerbukaEA();
      if(balR > 0.0 && br >= 0.0 && (br / balR * 100.0) >= MaxRiskPerBasketPct) { HapusPendingInitScalp(); return; }
   }

   bool konteksM1   = MS_SiapkanKonteksM1();
   if(!konteksM1 || gM1n < 25) return;
   DS_EvaluasiCuacaPasar();
   bool sedangRange = MS_M1SedangRange();

   double pt  = SymbolInfoDouble(SymbolKerja, SYMBOL_POINT);
   double stl = (double)MathMax(SymbolInfoInteger(SymbolKerja, SYMBOL_TRADE_STOPS_LEVEL),
                                SymbolInfoInteger(SymbolKerja, SYMBOL_TRADE_FREEZE_LEVEL)) * pt;

   // 3. Cek Posisi Aktif (Pyramiding dinonaktifkan sesuai Pilihan 2)
   int adaPosisiScalp = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(tk > 0 && PositionGetString(POSITION_SYMBOL) == SymbolKerja &&
         (ulong)PositionGetInteger(POSITION_MAGIC) == MagicNumber &&
         StringFind(PositionGetString(POSITION_COMMENT), "|S=5|") >= 0)
      {
         adaPosisiScalp++;
      }
   }

   if(adaPosisiScalp > 0)
   {
      HapusPendingInitScalp();
      return;
   }

   // 4. Analisa Order Flow, Tick Exhaustion, & RSI M1
   double upPress = 50.0; int t3s = 0, tPrev = 0;
   DS_AnalisaOrderFlow(upPress, t3s, tPrev);
   bool tickExhaustion = (tPrev >= 10 && t3s <= 3);

   double rsiArr[]; ArraySetAsSeries(rsiArr, true);
   int ix1 = IndexTimeframe(PERIOD_M1);
   double rsi1 = 50.0;
   if(ix1 >= 0 && CopyBuffer(rsiHandles[ix1], 0, 1, 1, rsiArr) == 1) rsi1 = rsiArr[0];

   datetime tNow = iTime(SymbolKerja, PERIOD_M1, 0);
   double garisAtas = 0.0, garisBawah = 0.0;
   if(g_TL_M1.valid)
   {
      garisAtas  = TL_HargaPadaWaktu(g_TL_M1.tA1, g_TL_M1.pA1, g_TL_M1.tA2, g_TL_M1.pA2, tNow);
      garisBawah = TL_HargaPadaWaktu(g_TL_M1.tB1, g_TL_M1.pB1, g_TL_M1.tB2, g_TL_M1.pB2, tNow);
   }

   double low0  = iLow(SymbolKerja, PERIOD_M1, 0);
   double high0 = iHigh(SymbolKerja, PERIOD_M1, 0);
   double open0 = iOpen(SymbolKerja, PERIOD_M1, 0);

   // =========================================================================
   // OTAK KE-5: CHAOS HUNTER (Climax Sniper dengan Validasi Risiko)
   // =========================================================================
   if(g_MarketChaos && !modeNewsVIP)
   {
      HapusPendingInitScalp();
      HapusSemuaPendingReverseScalp();
      static datetime lastChaosFire = 0;
      if(TimeCurrent() - lastChaosFire < 15) return;

      double slChaos = MathMax(V24_Pip(12.0), stl + 2.0 * pt);
      if(tickExhaustion && rsi1 <= 22.0 && upPress >= 72.0 && tick.bid > open0)
      {
         double slB = AlignHargaTick(tick.ask - slChaos, false);
         double tpB = AlignHargaTick(tick.ask + V24_Pip(14.0), false);
         double volB = 0.0; string infB = "";
         if(V24_Lot(true, tick.ask, slB, 5, volB, infB) && trade.Buy(volB, SymbolKerja, 0.0, slB, tpB, "CHAOS_CLIMAX_B|S=5|0"))
         {
            lastChaosFire = TimeCurrent();
            Print("CHAOS_HUNTER_BUY | Menyergap titik klimaks di ", DoubleToString(tick.ask, _Digits));
         }
      }
      else if(tickExhaustion && rsi1 >= 78.0 && upPress <= 28.0 && tick.bid < open0)
      {
         double slS = AlignHargaTick(tick.bid + slChaos, true);
         double tpS = AlignHargaTick(tick.bid - V24_Pip(14.0), true);
         double volS = 0.0; string infS = "";
         if(V24_Lot(false, tick.bid, slS, 5, volS, infS) && trade.Sell(volS, SymbolKerja, 0.0, slS, tpS, "CHAOS_CLIMAX_S|S=5|0"))
         {
            lastChaosFire = TimeCurrent();
            Print("CHAOS_HUNTER_SELL | Menyergap titik klimaks di ", DoubleToString(tick.bid, _Digits));
         }
      }
      return;
   }

   // =========================================================================
   // MODE 1: RANGE / SIDEWAYS -> DUAL-LAYER LIMIT + CONFLUENCE INSTAN SNIPER
   // =========================================================================
   if(sedangRange && !modeNewsVIP && g_TL_M1.valid && (garisAtas - garisBawah >= V24_Pip(8.0)))
   {
      HapusSemuaPendingReverseScalp();

      int buktiBuy = 1;
      if(DS_DekatAngkaPsikologis(garisBawah)) buktiBuy++;
      if(rsi1 <= 35.0) buktiBuy++;
      if(tickExhaustion) buktiBuy++;
      if(upPress >= 68.0) buktiBuy++;

      int buktiSell = 1;
      if(DS_DekatAngkaPsikologis(garisAtas)) buktiSell++;
      if(rsi1 >= 65.0) buktiSell++;
      if(tickExhaustion) buktiSell++;
      if(upPress <= 32.0) buktiSell++;

      static datetime lastInstanRange = 0;
      if(TimeCurrent() - lastInstanRange >= 3)
      {
         double slDistR = MathMax(V24_Pip(10.0), stl + 2.0 * pt);
         if(buktiBuy >= 3 && low0 <= garisBawah + V24_Pip(2.0) && tick.bid > open0 && upPress >= 70.0)
         {
            double slB = AlignHargaTick(MathMin(low0, garisBawah) - V24_Pip(3.0), false);
            if(tick.ask - slB < slDistR) slB = AlignHargaTick(tick.ask - slDistR, false);
            double tpB = AlignHargaTick(garisAtas - V24_Pip(1.0), false);
            double volB = 0.0; string infB = "";
            if(V24_Lot(true, tick.ask, slB, 5, volB, infB) && tpB > tick.ask + stl)
            {
               if(trade.Buy(volB, SymbolKerja, 0.0, slB, tpB, "DEWA_SNIPER_B|S=5|0"))
               {
                  lastInstanRange = TimeCurrent();
                  HapusPendingInitScalp();
                  return;
               }
            }
         }
         if(buktiSell >= 3 && high0 >= garisAtas - V24_Pip(2.0) && tick.bid < open0 && upPress <= 30.0)
         {
            double slS = AlignHargaTick(MathMax(high0, garisAtas) + V24_Pip(3.0), true);
            if(slS - tick.bid < slDistR) slS = AlignHargaTick(tick.bid + slDistR, true);
            double tpS = AlignHargaTick(garisBawah + V24_Pip(1.0), true);
            double volS = 0.0; string infS = "";
            if(V24_Lot(false, tick.bid, slS, 5, volS, infS) && tpS < tick.bid - stl)
            {
               if(trade.Sell(volS, SymbolKerja, 0.0, slS, tpS, "DEWA_SNIPER_S|S=5|0"))
               {
                  lastInstanRange = TimeCurrent();
                  HapusPendingInitScalp();
                  return;
               }
            }
         }
      }

      // Smart Anchor Dual-Layer Limit (Komentar Order Sudah Diseragamkan)
      double spr       = tick.ask - tick.bid;
      double bufJemput = V24_Pip(2.0) + spr;
      double buyLim1   = AlignHargaTick(garisBawah + bufJemput, true);
      double buyLim2   = AlignHargaTick(garisBawah - V24_Pip(4.5), true);
      double sellLim1  = AlignHargaTick(garisAtas - bufJemput, false);
      double sellLim2  = AlignHargaTick(garisAtas + V24_Pip(4.5), false);
      if(sellLim1 - buyLim1 < V24_Pip(8.0)) return;

      double slDistL = MathMax(V24_Pip(12.0), stl + 2.0 * pt);
      double slBuyL  = AlignHargaTick(buyLim2 - slDistL, false);
      double tpBuyL  = AlignHargaTick(sellLim1, false);
      double slSellL = AlignHargaTick(sellLim2 + slDistL, true);
      double tpSellL = AlignHargaTick(buyLim1, true);

      datetime nowS = TimeTradeServer(); if(nowS <= 0) nowS = TimeCurrent();
      ulong tkBL1 = 0, tkBL2 = 0, tkSL1 = 0, tkSL2 = 0;
      for(int js = OrdersTotal() - 1; js >= 0; js--)
      {
         ulong ots = OrderGetTicket(js);
         if(ots == 0 || OrderGetString(ORDER_SYMBOL) != SymbolKerja || (ulong)OrderGetInteger(ORDER_MAGIC) != MagicNumber) continue;
         string cms = OrderGetString(ORDER_COMMENT);
         if(nowS - (datetime)OrderGetInteger(ORDER_TIME_SETUP) >= 1800 && StringFind(cms, "REV_INIT_") == 0)
         {
            trade.OrderDelete(ots);
            continue;
         }
         if(cms == "REV_INIT_BL|S=5|0") tkBL1 = ots;
         if(cms == "REV_INIT_BL|S=5|1") tkBL2 = ots;
         if(cms == "REV_INIT_SL|S=5|0") tkSL1 = ots;
         if(cms == "REV_INIT_SL|S=5|1") tkSL2 = ots;
      }

      static datetime lastPasangLimit = 0;
Gunakan kode dengan hati-hati.
if(TimeCurrent() - lastPasangLimit < 2) return;
double volL = 0.0; string infoL = "";
if(!V24_Lot(true, buyLim1, slBuyL, 5, volL, infoL)) return;
double volHalf = NormalisasiVolumeBawah(volL * 0.5);
if(volHalf < SymbolInfoDouble(SymbolKerja, SYMBOL_VOLUME_MIN)) volHalf = volL;
if(HitungPosisiEA() + 2 > MaxPosisiEA) return;
if(tkBL1 == 0 && buyLim1 < tick.ask - stl - pt)
if(trade.BuyLimit(volHalf, buyLim1, SymbolKerja, slBuyL, tpBuyL, ORDER_TIME_GTC, 0, "REV_INIT_BL|S=5|0")) lastPasangLimit = TimeCurrent();
if(tkBL2 == 0 && buyLim2 < tick.ask - stl - pt)
if(trade.BuyLimit(volHalf, buyLim2, SymbolKerja, slBuyL, tpBuyL, ORDER_TIME_GTC, 0, "REV_INIT_BL|S=5|1")) lastPasangLimit = TimeCurrent();
if(tkSL1 == 0 && sellLim1 > tick.bid + stl + pt)
if(trade.SellLimit(volHalf, sellLim1, SymbolKerja, slSellL, tpSellL, ORDER_TIME_GTC, 0, "REV_INIT_SL|S=5|0")) lastPasangLimit = TimeCurrent();
if(tkSL2 == 0 && sellLim2 > tick.bid + stl + pt)
if(trade.SellLimit(volHalf, sellLim2, SymbolKerja, slSellL, tpSellL, ORDER_TIME_GTC, 0, "REV_INIT_SL|S=5|1")) lastPasangLimit = TimeCurrent();
return;
}
// =========================================================================
// MODE 2: TRENDING / BREAKOUT / SQUEEZE -> EKSEKUSI INSTAN
// =========================================================================
HapusPendingInitScalp();
static datetime lastTrendFire = 0;
if(TimeCurrent() - lastTrendFire < 3) return;
double ema8  = MS_EMA(PERIOD_M1, 8, 0);
double ema21 = MS_EMA(PERIOD_M1, 21, 0);
if(ema8 <= 0.0 || ema21 <= 0.0) return;
int dirM5 = MS_DirM5();
bool arahBuy  = (ema8 > ema21 && (modeNewsVIP || dirM5 >= 0) && gM1[1].close > gM1[1].open && tick.ask > gM1[1].high && upPress >= 68.0);
bool arahSell = (ema8 < ema21 && (modeNewsVIP || dirM5 <= 0) && gM1[1].close < gM1[1].open && tick.bid < gM1[1].low  && upPress <= 32.0);
if(!arahBuy && !arahSell) return;
bool bull = arahBuy;
double entry = (bull ? tick.ask : tick.bid);
double jarakSL = MathMax(V24_Pip(ScalpSLMinPips), stl + 2.0 * pt);
double sl = AlignHargaTick(bull ? entry - jarakSL : entry + jarakSL, !bull);
double vol = 0.0; string info = "";
if(!V24_Lot(bull, entry, sl, 5, vol, info)) return;
int jumlah = 1; // Aman sesuai Pilihan 2
if(HitungPosisiEA() + jumlah > MaxPosisiEA) return;
int berhasil = 0;
for(int k = 0; k < jumlah; k++)
{
bool ok = (bull ? trade.Buy(vol, SymbolKerja, 0.0, sl, 0.0, "DEWA_TREND|S=5|" + IntegerToString(k))
: trade.Sell(vol, SymbolKerja, 0.0, sl, 0.0, "DEWA_TREND|S=5|" + IntegerToString(k)));
if(ok)
{
berhasil++;
long pid = 0; ulong d = trade.ResultDeal();
if(d > 0 && HistoryDealSelect(d)) pid = HistoryDealGetInteger(d, DEAL_POSITION_ID);
if(pid == 0) pid = (long)trade.ResultOrder();
if(pid > 0)
{
string sp = IntegerToString(pid);
SimpanGV("SR" + sp, jarakSL);
SimpanGV("SB" + sp, 0.0);
SimpanGV("SV" + sp, vol);
}
}
}
if(berhasil > 0)
{
lastTrendFire = TimeCurrent();
Print("DEWA_TREND_ENTRY | ", (bull ? "BUY" : "SELL"), " ", berhasil, "x lot=", DoubleToString(vol, 2),
" di ", DoubleToString(entry, _Digits), " SL=", DoubleToString(sl, _Digits));
}
}

---

### BAGIAN 6: Asymmetric Breakeven Shield (+2.5 Pips) (`V24_KelolaSemua`)
* **Lokasi:** Sekitar **baris 2005–2040** di dalam fungsi `V24_KelolaSemua()`.
* **Cara Mencari:** Tekan `Ctrl + F`, ketik `if(scalp)`.
* **Instruksi (Ganti Blok `if(scalp)`):** Ganti blok `if(scalp) { ... continue; }` dengan kode di bawah ini (mengaktifkan pengunci **SL+ +0.6 pip di profit +2.5 pips**, tanpa *Midline Partial Cash-Out* sesuai Pilihan 2):

```cpp
      if(scalp)
      {
         double profitPips = (buy ? (px - opn) : (opn - px)) / g_pip;
         double slTerbaru  = sl;

         // Asymmetric Breakeven Shield (+2.5 Pips langsung SL+ +0.6 pip) & Smart Trailing Acceleration
         double trigPips  = (tp > 0.0 ? 2.5 : ScalpMulaiSLPlusPips);
         double kunciPips = (tp > 0.0 ? 0.6 : ScalpKunciAwalPips);
         double trailDin  = (profitPips >= 12.0 ? 3.5 : ScalpTrailingPips);

         if(profitPips >= trigPips)
         {
            double slAwalPlus = buy ? (opn + V24_Pip(kunciPips)) : (opn - V24_Pip(kunciPips));
            double slTrail    = (tp > 0.0 ? slAwalPlus : (buy ? (px - V24_Pip(trailDin)) : (px + V24_Pip(trailDin))));
            double targetSL   = buy ? MathMax(slAwalPlus, slTrail) : MathMin(slAwalPlus, slTrail);
            targetSL = AlignHargaTick(targetSL, buy);
            bool lebihBaik = (sl <= 0.0 || (buy ? targetSL > sl + point : targetSL < sl - point));
            bool jarakAman = (buy ? targetSL <= px - dmin : targetSL >= px + dmin);
            if(lebihBaik && jarakAman && ModifikasiDiizinkan())
            {
               if(trade.PositionModify(tk, targetSL, tp))
               {
                  slTerbaru = targetSL;
                  Print("DEWA_SL+_LOCK | pos=", pid, " Profit=", DoubleToString(profitPips, 1), " pips | SL+ bergeser ke ", DoubleToString(targetSL, digits));
               }
            }
         }
         if(tp == 0.0) adaScalpTanpaTP = true;
         {
            int dI = (buy ? 1 : 0);
            datetime tOpen = 0; if(PositionSelectByTicket(tk)) tOpen = (datetime)PositionGetInteger(POSITION_TIME);
            scCnt[dI]++;
            scV[dI] += vol;
            scR[dI] = rd;
            if(tOpen > scT[dI]) scT[dI] = tOpen;
            if(slTerbaru > 0.0)
            {
               if(scX[dI] == 0.0) scX[dI] = slTerbaru;
               else scX[dI] = (buy ? MathMax(scX[dI], slTerbaru) : MathMin(scX[dI], slTerbaru));
            }
         }
         continue;
      }

BAGIAN 7: Cockpit HUD Panel Canggih & Pembersihan Objek (V24_Dashboard, V24_BersihkanObjek, OnTick)

• Lokasi: Sekitar baris 2165–2245 (V24_Dashboard & V24_BersihkanObjek) dan baris 2415 (OnTick).
• Cara Mencari: Tekan Ctrl + F, ketik void V24_Dashboard().
Langkah 7A: Ganti seluruh fungsi V24_Dashboard() dengan versi Kokpit HUD Obsidian Pro di bawah ini:
cpp
void V24_Dashboard()
{
   static datetime lastD=0, lastRe=0; datetime now=TimeCurrent(); if(now==lastD) return; lastD=now;
   double bal=AccountInfoDouble(ACCOUNT_BALANCE);
   double br=HitungRisikoTerbukaEA(); double brp=(bal>0.0&&br>=0.0)?br/bal*100.0:0.0;
   double rl=HitungProfitRealisasiEASejak(AwalHariServer()); if(rl==EMPTY_VALUE) rl=0.0;
   double pnl=rl+HitungFloatingEA(); double baseD=(MetrikAwalHariEA>0.0?MetrikAwalHariEA:bal);
   double dl=(baseD>0.0&&pnl<0.0)?(-pnl)/baseD*100.0:0.0;

   string regM5=(g_Regime==REG_TREND?"TRENDING":(g_Regime==REG_RANGE?"RANGE (SIDEWAYS)":(g_Regime==REG_BREAKOUT?"BREAKOUT":(g_Regime==REG_EXTREME?"EKSTREM":"NETRAL"))));
   bool m1Range = (!MS_SiapkanKonteksM1() || MS_M1SedangRange());
   string regM1 = (g_MarketChaos ? "CHAOS (NGAMUK)" : (g_MarketSqueeze ? "SQUEEZE (SIAP LEDAK)" : (m1Range ? "RANGE (CHANNEL)" : "TRENDING")));
   color  clrM1 = (g_MarketChaos ? clrTomato : (g_MarketSqueeze ? clrGold : (m1Range ? clrAqua : clrSpringGreen)));

   bool s1_Super = (HitungPosisiKategori(ZONA_SUPER) > 0);
   bool s2_Biasa = (HitungPosisiKategori(ZONA_BIASA) > 0 || HitungPosisiStrategi(ST_TREND) > 0 || HitungPosisiStrategi(ST_SR) > 0 || HitungPosisiStrategi(ST_SD) > 0);
   bool s3_Brk   = (HitungPosisiKategori(ZONA_RETEST) > 0 || HitungPosisiKategori(ZONA_RBR) > 0 || HitungPosisiKategori(ZONA_DBD) > 0 || HitungPosisiStrategi(ST_BREAKOUT) > 0);
   bool s4_Scalp = (HitungPosisiStrategi(ST_SCALP) > 0 || V24_HitungPendingEA() > 0);
   bool s5_Chaos = (g_MarketChaos || g_MarketSqueeze);

   int mx=12, my=26, w=368, h=305;
   bool re=(now-lastRe>=15);
   if(re){ lastRe=now; ObjectsDeleteAll(0,"A24D_"); }

   string bg="A24D_BG";
   if(ObjectFind(0,bg)<0)
   {
      ObjectCreate(0,bg,OBJ_RECTANGLE_LABEL,0,0,0);
      ObjectSetInteger(0,bg,OBJPROP_SELECTABLE,false); ObjectSetInteger(0,bg,OBJPROP_HIDDEN,true);
      ObjectSetInteger(0,bg,OBJPROP_BGCOLOR,C'14,18,26');
      ObjectSetInteger(0,bg,OBJPROP_COLOR,clrGold);
      ObjectSetInteger(0,bg,OBJPROP_BORDER_TYPE,BORDER_FLAT);
      ObjectSetInteger(0,bg,OBJPROP_BACK,false);
   }
   ObjectSetInteger(0,bg,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,bg,OBJPROP_XDISTANCE,mx); ObjectSetInteger(0,bg,OBJPROP_YDISTANCE,my);
   ObjectSetInteger(0,bg,OBJPROP_XSIZE,w); ObjectSetInteger(0,bg,OBJPROP_YSIZE,h);

   V24_DrawText("A24D_L0", mx+10, my+8,   "DEWA XAUUSD ENGINE | " + SymbolKerja + " (" + NamaTFSingkat((ENUM_TIMEFRAMES)_Period) + ")", clrGold, 9, true);
   V24_DrawText("A24D_L1", mx+10, my+28,  "Market M5 : " + regM5, (g_Regime==REG_RANGE ? clrAqua : clrSpringGreen), 9, true);
   V24_DrawText("A24D_L2", mx+10, my+46,  "Cuaca M1  : " + regM1, clrM1, 9, true);
   V24_DrawText("A24D_L3", mx+10, my+64,  StringFormat("OrderFlow : BUY %.0f%% | SELL %.0f%%", g_LastUpPressure, 100.0 - g_LastUpPressure), (g_LastUpPressure>=68.0?clrSpringGreen:(g_LastUpPressure<=32.0?clrTomato:clrSilver)), 9, true);
   V24_DrawText("A24D_L4", mx+10, my+82,  StringFormat("Basket    : %.1f%% / %.0f%% | Posisi: %d/%d", brp, MaxRiskPerBasketPct, HitungPosisiEA(), MaxPosisiEA), clrWhite, 8, false);
   V24_DrawText("A24D_L5", mx+10, my+100, StringFormat("DailyLoss : %.1f%% / %.0f%% | DD: %.1f%%", dl, MathMin(DailyLossLimitPct,MaxDailyLossPct), V24_DDPct()), (dl>=MathMin(DailyLossLimitPct,MaxDailyLossPct)?clrTomato:clrSilver), 8, false);
   V24_DrawText("A24D_L6", mx+10, my+118, StringFormat("Vault Lock: $%.2f | PnL Hari: $%.2f", g_VaultLockedUSD, pnl), (pnl>=0?clrSpringGreen:clrTomato), 8, true);
   V24_DrawText("A24D_L7", mx+10, my+136, "========================================", C'60,75,95', 8, false);
   V24_DrawText("A24D_L8", mx+10, my+150, "5 CORE MESIN DEWA AKTIF:", clrAqua, 8, true);

   V24_DrawStratDot("A24D_S1", mx+10, my+170, 1, "SMC/ICT + HTF Trendline",   s1_Super);
   V24_DrawStratDot("A24D_S2", mx+10, my+190, 2, "Trend / SR / SD Engine",    s2_Biasa);
   V24_DrawStratDot("A24D_S3", mx+10, my+210, 3, "Breakout / Retest / RBR",   s3_Brk);
   V24_DrawStratDot("A24D_S4", mx+10, my+230, 4, "Sniper TL + Dual-Limit",   s4_Scalp);
   V24_DrawStratDot("A24D_S5", mx+10, my+250, 5, "Chaos & Squeeze Hunter",    s5_Chaos);

   string sesiStr = (V24_KZWaktu(now) ? "KILLZONE LONDON/NY" : (V24_DiAsia() ? "SESI ASIA (PING-PONG)" : "NORMAL SESSION"));
   V24_DrawText("A24D_L9", mx+10, my+276, "Sesi      : " + sesiStr, clrGold, 8, true);

   if(re) ChartRedraw(0);
}
Gunakan kode dengan hati-hati.
Langkah 7B: Di dalam V24_BersihkanObjek() (sekitar baris 2238), tambahkan pembersihan garis Trendline:
cpp
   ObjectsDeleteAll(0,"A24D_");
   ObjectsDeleteAll(0,"A24_TL_");
Gunakan kode dengan hati-hati.
Langkah 7C: Di dalam OnTick() (sekitar baris 2415), panggil TL_GambarChart(); tepat di bawah V24_Dashboard();:
cpp
   V24_Dashboard();
   TL_GambarChart();
Gunakan kode dengan hati-hati.
Silakan tempelkan kode di atas secara berurutan ke file .mq5 Anda di MetaEditor, lalu tekan Compile (F7). Jika muncul pesan error atau warning dari compiler, salin pesannya ke sini agar langsung saya perbaiki!
