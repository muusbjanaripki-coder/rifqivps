Berikut adalah panduan lengkap bagian serta barisan kode yang diubah/ditambahkan beserta kode siap pakai untuk diterapkan pada file APlus V24.18 Anda di MetaEditor.
Karena file asli Anda memiliki panjang lebih dari 1.400 baris, agar tidak terjadi error pemotongan teks saat Anda menyalin (copy-paste), berikut adalah 8 blok modifikasi terstruktur beserta nomor baris dan nama fungsinya di file Anda sehingga Anda bisa menggantinya dengan cepat dan akurat:

Peta Lokasi & Barisan Kode yang Diubah di File Asli Anda

1. Blok 1 (Sekitar Baris 53–68): Variabel Global Buku Otak Mandiri, Shadow Training, & News VIP
	• Fungsi: Menambahkan memori kalibrasi mandiri (SL+ Regret, Limit Tolerance, Shadow Mode), klasifikasi news terarah vs spike, dan kunci anti-dobel (mutex) saat SL keseret.
2. Blok 2 (Sekitar Baris 115–290): Parameter input Utama (RR 1:2, Zero Partial, & Visual Per TF)
	• Fungsi: Mengunci MinRiskReward = 2.0 & AsiaMinRR = 2.0, menghapus pemotongan sesi Asia (AsiaTPMult = 1.0), menonaktifkan Partial Close (MSPartialPct = 0.0), mengisolasi tampilan kotak & garis per TF (ModeTampilanTF = 2, TampilkanGarisAnalisis = true), serta menambah DeviasiMaksimalPoints = 120.
3. Blok 3 (Sekitar Baris 535–570): Isolasi Kotak Zona Per Timeframe & Penanda Unmitigated Strong Bounce
	• Fungsi: Memastikan kotak zona hanya muncul di TF asalnya dan memberi label [STRONG BOUNCE] pada zona perawan (fresh) di candle belakang.
4. Blok 4 (Sekitar Baris 965–1050): Klasifikasi News Besar (NFP/CPI/PPI/PCE/GDP/PMI vs FOMC/Powell)
	• Fungsi: Memisahkan aturan News Filter agar metode utama dilarang masuk saat news besar hingga 1 menit setelahnya, sementara VIP Scalping tetap boleh menyambut news.
5. Blok 5 (Sekitar Baris 1445–1525): Penghapusan Full Margin & Penambahan Posisi Entry (EksekusiSatuSinyal)
	• Fungsi: Menonaktifkan bolehFM, menggantinya dengan penambahan posisi entry, dan menanamkan pengecekan Shadow Sniper Mode saat drawdown penuh.
6. Blok 6 (Sekitar Baris 2090–2215): Reset Siklus Tanpa Berhenti (V24_UpdateBaseLock)
	• Fungsi: Menghapus g_TargetMenungguTutup agar EA tidak mati suri saat target tercapai, melainkan langsung me-reset drawdown, basket, dan hitungan loss lalu lanjut entry.
7. Blok 7 (Sekitar Baris 2440–2710): VIP Scalping (Limit Menyambut News → Stop Order, Anti-SL Keseret + Cadangan Instan, Zero Partial, & SL+ 1.5R)
	• Fungsi: Menggabungkan Buy/Sell Limit ke siklus Stop Order, menghapus limit basi, sensor close kilat jika SL mulai keseret (> 2.5 pips) + buka posisi cadangan instan beridentitas scalping (|S=5|), reset flip saat SL+, dan SL+ berbasis 1.5R tanpa pemotongan profit.
8. Blok 8 (Sekitar Baris 3045–3115): Buku Otak Mandiri (V24_SimpanBukuOtak / V24_MuatBukuOtak) & Gambar Next Sniper Plan Saat Drawdown Penuh
	• Fungsi: Menyimpan hasil evaluasi SL+ tersapu / limit terlewat ke APlus_Brain_Master.csv dan menggambar garis Entry, SL, TP rencana berikutnya di chart saat drawdown penuh.

Kode Pembaruan Lengkap (Siap Salin per Blok)


BLOK 1 — Ganti Baris 53–68 (Deklarasi Variabel Global Baru)

Cari baris // --- Pembelajaran mandiri & target bertingkat --- hingga void V24_JalankanMomentum();, lalu ganti dengan kode berikut:
mql5
// --- Pembelajaran mandiri, Shadow Mode, News VIP & Anti-Keseret ---
double g_LearnScore[6] = {100.0, 100.0, 100.0, 100.0, 100.0, 100.0};
int    g_ConsecSL = 0;
int    g_JamRawan[24];
bool   g_TargetMenungguTutup = false;
double g_SniperDepthPct = 0.45;      // kedalaman titik sniper dalam zona (dipelajari otomatis)
double g_BrainSLPlusR   = 1.50;      // rasio R pemicu SL+ utama (bertambah otomatis jika sering tersapu)
double g_BrainTrailPips = 25.0;      // jarak trailing SL+ utama (bertambah otomatis jika sering tersapu)
double g_BrainLimitPad  = 3.5;       // buffer jemput order limit (bertambah otomatis jika sering diekorin)
bool   g_FMTerpakaiHariIni = false;
int    g_FMHari = -1;
int    g_NewsModeVIP = 0;            // 0=normal, 1=news terarah (NFP/CPI/PPI/dll), 2=news spike (FOMC/Powell)
datetime g_NewsEventTime = 0;        // waktu rilis berita besar terdekat
datetime g_SpikeDetectedTime = 0;    // waktu terdeteksi spike FOMC
ulong  g_LastEmergencyLockMs = 0;    // mutex anti-dobel saat close paksa SL keseret
double g_ShadowEntry = 0.0, g_ShadowSL = 0.0, g_ShadowTP = 0.0;
bool   g_ShadowBull = true, g_ShadowActive = false;

void   V24_SimpanBukuOtak();
void   V24_MuatBukuOtak();
void   V24_UpdateEquityState();
double V24_DDPct();
bool   V24_DiAsia();
void   V24_JalankanMomentum();
void   V24_ShadowTrainingDanGambar();
Gunakan kode dengan hati-hati.

BLOK 2 — Ubah Nilai Input Utama (Cari & Ganti Masing-Masing Baris input Ini)

Pastikan parameter input berikut di bagian atas file Anda diubah menjadi:
mql5
input double MinRiskReward         = 2.0;    // RR mutlak minimal 1:2 di semua sesi
input double MinRRStrategi         = 2.0;    // RR minimum strategi 2-5 disamakan ke 1:2
input double AsiaTPMult            = 1.0;    // 1.0 = TANPA pemotongan TP di sesi Asia
input double AsiaMinRR             = 2.0;    // RR minimum sesi Asia disamakan 1:2
input double MSPartialR            = 0.0;    // 0 = TANPA pemotongan profit (Zero Partial Close)
input double MSPartialPct          = 0.0;    // 0% partial close, semua lot berlari 100% utuh
input double ScalpPartialRR        = 0.0;    // 0 = TANPA pemotongan profit scalping
input double UtamaMulaiSLPlusPips  = 35.0;   // cadangan pips (utama memakai g_BrainSLPlusR = 1.5R)
input double UtamaKunciAwalPips    = 8.0;    // kunci profit bersih minimal +8 pips saat SL+ aktif
input double UtamaTrailingPips     = 25.0;   // jarak trailing SL+ memberi ruang napas XAUUSD
input int    DeviasiMaksimalPoints = 120;    // toleransi deviasi non-news agar tidak kena requote
input int    MaxEntrySuper         = 3;      // ditambah menjadi 3 entry (pengganti Full Margin)
input int    MaxEntryBiasa         = 2;      // ditambah menjadi 2 entry
input int    ModeTampilanTF        = 2;      // 2 = ISOLASI MUTLAK PER TIMEFRAME (M1 di M1, M5 di M5, dst)
input bool   TampilkanGarisAnalisis= true;   // aktifkan kembali garis BOS/CHoCH, PDH/PDL, EQH/EQL
input bool   LabelBersih           = false;  // tampilkan label garis struktur & zona
input bool   TutupPosisiSebelumNews= true;   // tutup posisi lama 2 menit sebelum news besar
Gunakan kode dengan hati-hati.

BLOK 3 — Ganti Fungsi ZonaDitampilkan & GambarZonaIdx (Isolasi TF & Penanda Candle Belakang)

Cari bool ZonaDitampilkan(DataZona &z) (sekitar baris 535) dan ganti blok ZonaDitampilkan hingga akhir GambarZonaIdx dengan kode ini:
mql5
bool ZonaDitampilkan(DataZona &z)
{
   if((z.kategori==ZONA_SUPER || z.kategori==ZONA_BIASA) && (z.skor < 4 || z.timeframe < PERIOD_M15)) return false;
   if((z.kategori==ZONA_RETEST || z.kategori==ZONA_RBR || z.kategori==ZONA_DBD) && z.timeframe < PERIOD_M15) return false;

   // ISOLASI MUTLAK PER TIMEFRAME: Kotak M1 hanya di M1, M5 hanya di M5, H1 hanya di H1, dst.
   int sc = PeriodSeconds((ENUM_TIMEFRAMES)_Period);
   int sz = PeriodSeconds(z.timeframe);
   if(ModeTampilanTF == 2 && sz != sc) return false;
   if(ModeTampilanTF == 1 && sz < sc)  return false;

   double px = SymbolInfoDouble(SymbolKerja, SYMBOL_BID);
   if(TampilanBersih && JarakTampilZonaATR > 0.0)
   {
      double atrc = AmbilATR((ENUM_TIMEFRAMES)_Period);
      if(atrc > 0.0 && px > 0.0)
      {
         double d = (px < z.batasBawah ? z.batasBawah - px : (px > z.batasAtas ? px - z.batasAtas : 0.0));
         if(d > JarakTampilZonaATR * atrc) return false;
      }
   }
   return true;
}

void GambarZonaIdx(int idx)
{
   if(!TampilkanZonaChart || idx < 0 || idx >= JumlahZonaRegistry) return;
   DataZona z = RegistryZona[idx];
   if(!ZonaRegistryValid(z)) return;
   if(!ZonaDitampilkan(z)) { HapusObjekZona(z); return; }

   string name = NamaObjekZona(z);
   datetime now = iTime(SymbolKerja, (ENUM_TIMEFRAMES)_Period, 0);
   if(now <= 0) now = TimeCurrent();
   int sec = PeriodSeconds((ENUM_TIMEFRAMES)_Period); if(sec <= 0) sec = 300;
   datetime t2 = now + (datetime)(sec * 15);
   datetime tLeft = z.waktu;

   // Deteksi Candle Belakang yang Masih Perawan (Unmitigated Strong Bounce)
   int umurBar = iBarShift(SymbolKerja, z.timeframe, z.waktu, false);
   bool strongBounce = (!zonaMitigasi[idx] && zTouchCount[idx] == 0 && umurBar >= 60 && z.skor >= 6);

   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_RECTANGLE, 0, tLeft, z.batasAtas, t2, z.batasBawah);
   else
   {
      ObjectMove(0, name, 0, tLeft, z.batasAtas);
      ObjectMove(0, name, 1, t2, z.batasBawah);
   }

   ObjectSetInteger(0, name, OBJPROP_COLOR, strongBounce ? C'255,235,190' : WarnaKotakZona(z));
   ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_SOLID);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, strongBounce ? 2 : 1);
   ObjectSetInteger(0, name, OBJPROP_FILL, true);
   ObjectSetInteger(0, name, OBJPROP_BACK, true);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);

   datetime tl = tLeft + (datetime)((long)(t2 - tLeft) / 2);
   double labelPrice = 0.5 * (z.batasAtas + z.batasBawah);
   string label = name + "_TXT";
   if(ObjectFind(0, label) < 0) ObjectCreate(0, label, OBJ_TEXT, 0, tl, labelPrice);
   else ObjectMove(0, label, 0, tl, labelPrice);

   string teksZona = NamaKategoriZona(z.kategori) + (z.bullish ? " BUY " : " SELL ") + NamaTFSingkat(z.timeframe);
   if(strongBounce) teksZona += " [STRONG BOUNCE]";
   AturTampilanLabelZona(label, teksZona, (z.bullish ? clrDodgerBlue : clrRed), ANCHOR_CENTER);
}
Gunakan kode dengan hati-hati.

BLOK 4 — Ganti Fungsi NewsFilterBolehLanjut (Klasifikasi News Besar vs Kecil/Sedang)

Cari bool NewsFilterBolehLanjut() (sekitar baris 995) dan ganti seluruh isinya dengan kode ini:
mql5
int KlasifikasiJudulNews(string title)
{
   StringToUpper(title);
   // Kategori 2: News Spike (FOMC / Suku Bunga / Pidato Ketua The Fed)
   if(StringFind(title, "FOMC") >= 0 || StringFind(title, "FEDERAL FUNDS") >= 0 ||
      StringFind(title, "INTEREST RATE") >= 0 || StringFind(title, "POWELL") >= 0 ||
      StringFind(title, "FED CHAIR") >= 0)
      return 2;

   // Kategori 1: News Besar Terarah (NFP, CPI, PPI, PCE, Retail Sales, GDP, ISM PMI, ADP)
   if(StringFind(title, "NONFARM") >= 0 || StringFind(title, "NON-FARM") >= 0 ||
      StringFind(title, "PAYROLL") >= 0 || StringFind(title, "UNEMPLOYMENT") >= 0 ||
      StringFind(title, "CPI") >= 0 || StringFind(title, "CONSUMER PRICE") >= 0 ||
      StringFind(title, "PPI") >= 0 || StringFind(title, "PRODUCER PRICE") >= 0 ||
      StringFind(title, "PCE") >= 0 || StringFind(title, "RETAIL SALES") >= 0 ||
      StringFind(title, "GDP") >= 0 || StringFind(title, "ISM ") >= 0 ||
      StringFind(title, "ADP ") >= 0)
      return 1;

   return 0; // News kecil / sedang -> metode utama tetap jalan normal
}

bool NewsFilterBolehLanjut()
{
   g_NewsModeVIP = 0;
   g_NewsEventTime = 0;
   datetime now = TimeTradeServer();
   if(now <= 0) now = TimeCurrent();
   if(now <= 0) return false;

   if(AktifkanEconomicCalendarMT5)
   {
      bool tester = (MQLInfoInteger(MQL_TESTER) != 0);
      if(tester && g_kalTesterTidakAda) return true;
      MqlCalendarValue values[];
      datetime from = now - (datetime)(NewsMinutesAfter * 60);
      datetime to   = now + (datetime)(NewsMinutesBefore * 60);
      int count = CalendarValueHistory(values, from, to, NULL, "USD");
      if(count > 0)
      {
         for(int i = 0; i < count; i++)
         {
            MqlCalendarEvent ev;
            if(!CalendarEventById(values[i].event_id, ev)) continue;
            if(ev.importance != CALENDAR_IMPORTANCE_HIGH) continue;

            int katNews = KlasifikasiJudulNews(ev.name);
            if(katNews == 0) continue; // Berita kecil/sedang tidak memblokir metode utama

            if(now >= values[i].time - (datetime)(NewsMinutesBefore * 60) &&
               now <  values[i].time + (datetime)(NewsMinutesAfter * 60))
            {
               g_NewsModeVIP   = katNews;
               g_NewsEventTime = values[i].time;

               // 2 menit sebelum news besar: tutup semua posisi berjalan agar aman dari pelebaran spread
               if(TutupPosisiSebelumNews && now < values[i].time - 20 && HitungPosisiEA() > 0)
               {
                  Print("NEWS_CLOSE_ALL: Menutup posisi 2 menit sebelum ", ev.name);
                  TutupSemuaPosisiEA("NEWS_CLOSE_ALL");
               }
               return false; // Blokir metode utama sampai 1 menit setelah news selesai
            }
         }
      }
   }
   return true;
}
Gunakan kode dengan hati-hati.

BLOK 5 — Matikan Full Margin & Tambah Posisi di EksekusiSatuSinyal

Di dalam fungsi bool EksekusiSatuSinyal(...) (sekitar baris 1525), cari baris bool bolehFM = ... dan ubah menjadi:
mql5
   // Full Margin dinonaktifkan sesuai kesepakatan, diganti penambahan jumlah posisi entry
   bool bolehFM = false;
Gunakan kode dengan hati-hati.

BLOK 6 — Reset Siklus Tanpa Berhenti di V24_UpdateBaseLock

Cari fungsi void V24_UpdateBaseLock() (sekitar baris 2135) dan ganti seluruh isinya dengan kode ini:
mql5
void V24_UpdateBaseLock()
{
   static datetime lastChk = 0; datetime now = TimeCurrent(); if(now == lastChk) return; lastChk = now;
   double base = V24_BaseBal();
   double step = V24_TargetStep();
   double tl   = base + step;
   double eq   = AccountInfoDouble(ACCOUNT_EQUITY);
   double bal  = AccountInfoDouble(ACCOUNT_BALANCE);

   // Target tercapai: JANGAN berhenti entry! Langsung reset drawdown, basket, & catatan loss
   if(base > 0.0 && MathMax(eq, bal) >= tl)
   {
      double saldoAcuan = MathMax(eq, bal);
      double stepBaru   = step * 1.5;

      V24G_Set("v24Base", saldoAcuan);
      V24G_Set("v24Step", stepBaru);
      V24G_Set("v24Peak", saldoAcuan);     // Reset Drawdown menjadi 0%
      V24G_Set("v24DayEq", saldoAcuan);    // Reset Loss Harian menjadi 0%
      V24G_Set("v24Flip", 0.0);
      g_ConsecSL = 0;                      // Reset hitungan loss beruntun
      DailyLossTerpicu = false;
      SimpanGV("dTrip", 0.0);
      SimpanGV("dBase", saldoAcuan);
      g_TargetMenungguTutup = false;

      Print("V24_TARGET_RESET_LANJUT | Target ", DoubleToString(tl, 2), " tercapai! Saldo Utama Baru=",
            DoubleToString(saldoAcuan, 2), " | Drawdown, Basket & Loss di-reset ke 0. EA terus berjalan!");
   }
}
Gunakan kode dengan hati-hati.

BLOK 7 — VIP Scalping: Limit Menyambut News → Stop Order, Sensor Anti-SL Keseret + Cadangan Instan, Zero Partial, & SL+ 1.5R

Ganti fungsi V24_JagaSiklusReverse() dan V24_KelolaSemua() (sekitar baris 2445–2715) dengan kode terpadu berikut:
mql5
// Buka posisi cadangan instan dengan identitas VIP Scalping Stop Order jika SL keseret
void EksekusiCadanganSLKeseret(bool arahBaruBuy, double volume, double jarakSL)
{
   if(GetTickCount64() - g_LastEmergencyLockMs < 1500) return; // Mutex anti-dobel 1.5 detik
   g_LastEmergencyLockMs = GetTickCount64();

   HapusSemuaPendingReverseScalp();
   MqlTick tk; if(!SymbolInfoTick(SymbolKerja, tk)) return;
   double entry = (arahBaruBuy ? tk.ask : tk.bid);
   double sl = AlignHargaTick(arahBaruBuy ? entry - jarakSL : entry + jarakSL, !arahBaruBuy);

   trade.SetDeviationInPoints(150);
   bool ok = (arahBaruBuy ? trade.Buy(volume, SymbolKerja, 0.0, sl, 0.0, "REV_|S=5|_CADANGAN")
                          : trade.Sell(volume, SymbolKerja, 0.0, sl, 0.0, "REV_|S=5|_CADANGAN"));
   trade.SetDeviationInPoints((ulong)DeviasiMaksimalPoints);

   if(ok)
   {
      long pid = 0; ulong d = trade.ResultDeal();
      if(d > 0 && HistoryDealSelect(d)) pid = HistoryDealGetInteger(d, DEAL_POSITION_ID);
      if(pid == 0) pid = (long)trade.ResultOrder();
      if(pid > 0)
      {
         string sp = IntegerToString(pid);
         SimpanGV("SR" + sp, jarakSL);
         SimpanGV("SB" + sp, 0.0);
         SimpanGV("SV" + sp, volume);
      }
      Print("ANTI_SL_KESERET_CADANGAN | Close paksa SL keseret & langsung buka ",
            (arahBaruBuy ? "BUY" : "SELL"), " Scalping Stop Order di ", DoubleToString(entry, _Digits));
   }
}

void V24_JagaSiklusReverse()
{
   if(!ScalpReverseAktif || ModeOperasi != AUTO_TRADE)
   {
      HapusSemuaPendingReverseScalp();
      HapusPendingInitScalp();
      return;
   }

   int adaPosisiScalp = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(tk > 0 && PositionGetString(POSITION_SYMBOL) == SymbolKerja &&
         (ulong)PositionGetInteger(POSITION_MAGIC) == MagicNumber &&
         StringFind(PositionGetString(POSITION_COMMENT), "|S=5|") >= 0)
         adaPosisiScalp++;
   }
   if(adaPosisiScalp > 0) return;

   MqlTick tick;
   if(!SymbolInfoTick(SymbolKerja, tick) || tick.bid <= 0.0) return;
   datetime now = TimeTradeServer(); if(now <= 0) now = TimeCurrent();

   // Cek Jadwal Khusus News VIP
   bool newsOK = NewsFilterBolehLanjut();
   bool modeNewsTerarah = false;
   bool modeNewsSpike   = false;

   if(!newsOK)
   {
      if(g_NewsModeVIP == 1 && g_NewsEventTime > 0 && now >= g_NewsEventTime - 15 && now <= g_NewsEventTime + 60)
         modeNewsTerarah = true; // 15 detik sebelum NFP/CPI/PPI/dll: aktifkan perangkap VIP tanpa flip
      else if(g_NewsModeVIP == 2 && g_NewsEventTime > 0 && now > g_NewsEventTime)
      {
         // Deteksi spike FOMC lalu tunggu 3 detik setelah spike
         double rngM1 = iHigh(SymbolKerja, PERIOD_M1, 0) - iLow(SymbolKerja, PERIOD_M1, 0);
         if(rngM1 >= V24_Pip(25.0) && g_SpikeDetectedTime == 0) g_SpikeDetectedTime = now;
         if(g_SpikeDetectedTime > 0 && now >= g_SpikeDetectedTime + 3) modeNewsSpike = true;
      }
      if(!modeNewsTerarah && !modeNewsSpike) { HapusPendingInitScalp(); return; }
   }
   else g_SpikeDetectedTime = 0;

   double tCool = 0.0;
   if(V24G_Get("v24FlipCool", tCool) && now < (datetime)tCool) { HapusPendingInitScalp(); return; }

   double pt  = SymbolInfoDouble(SymbolKerja, SYMBOL_POINT);
   double stl = (double)MathMax(SymbolInfoInteger(SymbolKerja, SYMBOL_TRADE_STOPS_LEVEL),
                                SymbolInfoInteger(SymbolKerja, SYMBOL_TRADE_FREEZE_LEVEL)) * pt;
   double spr = tick.ask - tick.bid;

   // Jika Mode News VIP (15 detik sebelum NFP atau 3 detik pasca-spike FOMC): Pasang Buy Stop & Sell Stop dengan kompensasi spread
   if(modeNewsTerarah || modeNewsSpike)
   {
      double jarakStop = MathMax(V24_Pip(16.0) + spr * 1.5, stl + 3.0 * pt);
      double jarakSL   = MathMax(V24_Pip(ScalpSLMinPips), stl + 2.0 * pt);
      double hBuy  = AlignHargaTick(tick.ask + jarakStop, true);
      double hSell = AlignHargaTick(tick.bid - jarakStop, false);

      double vol = 0.0; string info = "";
      if(!V24_Lot(true, hBuy, hBuy - jarakSL, 5, vol, info)) return;

      bool adaB = false, adaS = false;
      for(int j = OrdersTotal() - 1; j >= 0; j--)
      {
         ulong otk = OrderGetTicket(j);
         if(otk > 0 && OrderGetString(ORDER_SYMBOL) == SymbolKerja && (ulong)OrderGetInteger(ORDER_MAGIC) == MagicNumber)
         {
            string cm = OrderGetString(ORDER_COMMENT);
            if(StringFind(cm, "REV_INIT_B_") == 0) adaB = true;
            if(StringFind(cm, "REV_INIT_S_") == 0) adaS = true;
         }
      }
      int jml = MathMax(1, ScalpMaxPosisi);
      for(int k = 0; k < jml; k++)
      {
         if(!adaB) trade.BuyStop(vol, hBuy, SymbolKerja, AlignHargaTick(hBuy - jarakSL, false), 0.0, ORDER_TIME_GTC, 0, "REV_INIT_B_|S=5|_NEWS_" + IntegerToString(k));
         if(!adaS) trade.SellStop(vol, hSell, SymbolKerja, AlignHargaTick(hSell + jarakSL, true), 0.0, ORDER_TIME_GTC, 0, "REV_INIT_S_|S=5|_NEWS_" + IntegerToString(k));
      }
      return;
   }

   // Mode Normal: Menyambut pergerakan dengan Order Limit (jemput maju + g_BrainLimitPad pips) -> lalu dikawal Stop Order
   bool konteksM1 = MS_SiapkanKonteksM1();
   if(konteksM1 && MS_M1SedangRange())
   {
      double atap   = MS_MaxHigh(gM1, gM1n, 1, 30);
      double lantai = MS_MinLow(gM1, gM1n, 1, 30);
      if(atap <= lantai || (atap - lantai) < V24_Pip(22.0)) return;

      double bufJemput = V24_Pip(g_BrainLimitPad) + spr; // Jemput lebih awal agar tidak diekorin
      double buyLim  = AlignHargaTick(lantai + bufJemput, true);
      double sellLim = AlignHargaTick(atap - bufJemput, false);
      double slDist  = MathMax(V24_Pip(12.0), stl + 2.0 * pt);
      double tpDist  = slDist * 2.2; // Rasio minimal > 1:2

      // Hapus Order Limit yang basi (> 15 menit atau harga sudah menyentuh TP duluan)
      for(int j2 = OrdersTotal() - 1; j2 >= 0; j2--)
      {
         ulong otk2 = OrderGetTicket(j2);
         if(otk2 > 0 && OrderGetString(ORDER_SYMBOL) == SymbolKerja && (ulong)OrderGetInteger(ORDER_MAGIC) == MagicNumber)
         {
            string cm2 = OrderGetString(ORDER_COMMENT);
            datetime tSet = (datetime)OrderGetInteger(ORDER_TIME_SETUP);
            double tpOrd  = OrderGetDouble(ORDER_TP);
            bool basi = (now - tSet >= 900) ||
                        (StringFind(cm2, "REV_INIT_BL") == 0 && tpOrd > 0 && tick.bid >= tpOrd) ||
                        (StringFind(cm2, "REV_INIT_SL") == 0 && tpOrd > 0 && tick.ask <= tpOrd);
            if(basi) { trade.OrderDelete(otk2); continue; }
         }
      }

      double volL = 0.0; string infoL = "";
      if(!V24_Lot(true, buyLim, buyLim - slDist, 5, volL, infoL)) return;

      bool adaBL = false, adaSL = false;
      for(int j3 = OrdersTotal() - 1; j3 >= 0; j3--)
      {
         ulong otk3 = OrderGetTicket(j3);
         if(otk3 > 0 && OrderGetString(ORDER_SYMBOL) == SymbolKerja && (ulong)OrderGetInteger(ORDER_MAGIC) == MagicNumber)
         {
            string cm3 = OrderGetString(ORDER_COMMENT);
            if(StringFind(cm3, "REV_INIT_BL") == 0) adaBL = true;
            if(StringFind(cm3, "REV_INIT_SL") == 0) adaSL = true;
         }
      }
      if(!adaBL && buyLim < tick.ask - stl - pt)
         trade.BuyLimit(volL, buyLim, SymbolKerja, AlignHargaTick(buyLim - slDist, false), AlignHargaTick(buyLim + tpDist, true), ORDER_TIME_GTC, 0, "REV_INIT_BL_|S=5|_0");
      if(!adaSL && sellLim > tick.bid + stl + pt)
         trade.SellLimit(volL, sellLim, SymbolKerja, AlignHargaTick(sellLim + slDist, true), AlignHargaTick(sellLim - tpDist, false), ORDER_TIME_GTC, 0, "REV_INIT_SL_|S=5|_0");
      return;
   }

   // Mode Trending Normal: Perangkap Buy Stop & Sell Stop
   double jarakStopN = MathMax(V24_Pip(16.0), stl + 2.0 * pt);
   double jarakSLN   = MathMax(V24_Pip(ScalpSLMinPips), stl + 2.0 * pt);
   double hBuyN  = AlignHargaTick(tick.ask + jarakStopN, true);
   double hSellN = AlignHargaTick(tick.bid - jarakStopN, false);

   double volN = 0.0; string infoN = "";
   if(!V24_Lot(true, hBuyN, hBuyN - jarakSLN, 5, volN, infoN)) return;

   bool adaBN = false, adaSN = false;
   for(int j4 = OrdersTotal() - 1; j4 >= 0; j4--)
   {
      ulong otk4 = OrderGetTicket(j4);
      if(otk4 > 0 && OrderGetString(ORDER_SYMBOL) == SymbolKerja && (ulong)OrderGetInteger(ORDER_MAGIC) == MagicNumber)
      {
         string cm4 = OrderGetString(ORDER_COMMENT);
         if(StringFind(cm4, "REV_INIT_B_") == 0) adaBN = true;
         if(StringFind(cm4, "REV_INIT_S_") == 0) adaSN = true;
      }
   }
   int jmlN = MathMax(1, ScalpMaxPosisi);
   for(int k2 = 0; k2 < jmlN; k2++)
   {
      if(!adaBN) trade.BuyStop(volN, hBuyN, SymbolKerja, AlignHargaTick(hBuyN - jarakSLN, false), 0.0, ORDER_TIME_GTC, 0, "REV_INIT_B_|S=5|_" + IntegerToString(k2));
      if(!adaSN) trade.SellStop(volN, hSellN, SymbolKerja, AlignHargaTick(hSellN + jarakSLN, true), 0.0, ORDER_TIME_GTC, 0, "REV_INIT_S_|S=5|_" + IntegerToString(k2));
   }
}
Gunakan kode dengan hati-hati.
(Catatan untuk V24_KelolaSemua() di Blok 7: Pastikan di dalam loop posisi Anda menambahkan Sensor Anti-SL Keseret dan SL+ 1.5R tanpa Partial Close di bawah ini):
mql5
      // SENSOR ANTI-SL KESERET: Jika harga menembus SL resmi > 2.5 pips, tutup kilat & buka cadangan Scalping Stop Order
      if(sl > 0.0)
      {
         bool slKeseret = (buy ? (px <= sl - V24_Pip(2.5)) : (px >= sl + V24_Pip(2.5)));
         if(slKeseret && ModifikasiDiizinkan())
         {
            if(trade.PositionClose(tk))
            {
               if(scalp) EksekusiCadanganSLKeseret(!buy, vol, rd);
               continue;
            }
         }
      }

      // SL+ METODE UTAMA: Berbasis 1.5R (g_BrainSLPlusR) tanpa pemotongan profit (Zero Partial Close)
      if(!scalp && UtamaSLPlusAktif && R >= g_BrainSLPlusR)
      {
         double slAwalPlusU = buy ? (opn + V24_Pip(UtamaKunciAwalPips)) : (opn - V24_Pip(UtamaKunciAwalPips));
         double slTrailU    = buy ? (px - V24_Pip(g_BrainTrailPips))   : (px + V24_Pip(g_BrainTrailPips));
         double targetSLU   = buy ? MathMax(slAwalPlusU, slTrailU)      : MathMin(slAwalPlusU, slTrailU);
         targetSLU          = AlignHargaTick(targetSLU, buy);
         if((sl <= 0.0 || (buy ? targetSLU > sl + point : targetSLU < sl - point)) &&
            (buy ? targetSLU <= px - dmin : targetSLU >= px + dmin) && ModifikasiDiizinkan())
         {
            trade.PositionModify(tk, targetSLU, tp);
         }
      }
Gunakan kode dengan hati-hati.
(Dan pada bagian KelolaReverseGelombangScalp di bawah V24_KelolaSemua(), pastikan saat posisi scalping masuk mode sudahSLPlus, V24G_Set("v24Flip", 0.0) dipanggil sehingga Stop Order tetap menempel di garis SL+, sedangkan jika sedang g_NewsModeVIP > 0 maka flip dikunci ke 0).

BLOK 8 — Buku Otak Mandiri & Gambar Next Sniper Plan Saat Drawdown Penuh

Ganti fungsi V24_SimpanBukuOtak() dan V24_MuatBukuOtak() (sekitar baris 2225) serta tambahkan fungsi V24_ShadowTrainingDanGambar() untuk dipanggil di dalam OnTick():
mql5
void V24_SimpanBukuOtak()
{
   int h = FileOpen("APlus_Brain_Master.csv", FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(h == INVALID_HANDLE) return;
   FileWriteString(h, "BASE;" + DoubleToString(V24_BaseBal(), 2) + ";" + DoubleToString(V24_TargetStep(), 2) + "\r\n");
   FileWriteString(h, "DEPTH;" + DoubleToString(g_SniperDepthPct, 3) + "\r\n");
   FileWriteString(h, "ADAPT;" + DoubleToString(g_BrainSLPlusR, 2) + ";" + DoubleToString(g_BrainTrailPips, 1) + ";" + DoubleToString(g_BrainLimitPad, 1) + "\r\n");
   string scLine = "SCORE";
   for(int i = 0; i < 6; i++) scLine += ";" + DoubleToString(g_LearnScore[i], 2);
   FileWriteString(h, scLine + "\r\n");
   FileClose(h);
}

void V24_MuatBukuOtak()
{
   int h = FileOpen("APlus_Brain_Master.csv", FILE_READ|FILE_TXT|FILE_ANSI);
   if(h == INVALID_HANDLE) return;
   while(!FileIsEnding(h))
   {
      string ln = FileReadString(h);
      string p[]; int n = StringSplit(ln, ';', p);
      if(n < 2) continue;
      if(p[0] == "DEPTH") g_SniperDepthPct = MathMax(0.25, MathMin(0.80, StringToDouble(p[1])));
      else if(p[0] == "ADAPT" && n >= 4)
      {
         g_BrainSLPlusR   = MathMax(1.20, MathMin(2.50, StringToDouble(p[1])));
         g_BrainTrailPips = MathMax(15.0, MathMin(45.0, StringToDouble(p[2])));
         g_BrainLimitPad  = MathMax(2.0,  MathMin(7.0,  StringToDouble(p[3])));
      }
      else if(p[0] == "SCORE" && n >= 7)
         for(int i = 0; i < 6; i++) g_LearnScore[i] = MathMax(45.0, MathMin(100.0, StringToDouble(p[i+1])));
   }
   FileClose(h);
}

// Berlatih mandiri & menggambar rencana Next Valid Sniper Entry saat Drawdown Penuh
void V24_ShadowTrainingDanGambar()
{
   MqlTick tk; if(!SymbolInfoTick(SymbolKerja, tk) || tk.bid <= 0.0) return;
   double px = tk.bid;

   // 1. Evaluasi latihan bayangan yang sedang berjalan
   if(g_ShadowActive)
   {
      bool kenaSL = (g_ShadowBull ? (px <= g_ShadowSL) : (px >= g_ShadowSL));
      bool kenaTP = (g_ShadowBull ? (px >= g_ShadowTP) : (px <= g_ShadowTP));
      if(kenaSL)
      {
         g_SniperDepthPct = MathMin(0.80, g_SniperDepthPct + 0.05); // Bidik lebih dalam di zona berikutnya
         g_ShadowActive = false;
         V24_SimpanBukuOtak();
      }
      else if(kenaTP)
      {
         g_LearnScore[ST_SMC] = MathMin(100.0, g_LearnScore[ST_SMC] + 3.0);
         g_ShadowActive = false;
         V24_SimpanBukuOtak();
      }
   }

   // 2. Cari zona terbaik terdekat & gambar garis rencana jika Drawdown Penuh
   bool ddPenuh = (V24_DDPct() >= MaxDrawdownPct || BatasRugiHarianTercapai());
   if(!ddPenuh) { ObjectsDeleteAll(0, "A24_PLAN_"); return; }

   int bestIdx = -1; double bestDist = DBL_MAX;
   for(int i = 0; i < JumlahZonaRegistry; i++)
   {
      if(!ZonaRegistryValid(RegistryZona[i]) || zStatus[i] >= ZS_BREACHED) continue;
      double mid = RegistryZona[i].ce50;
      double d = MathAbs(mid - px);
      if(d < bestDist) { bestDist = d; bestIdx = i; }
   }
   if(bestIdx < 0) return;

   DataZona z = RegistryZona[bestIdx];
   double hZona = z.batasAtas - z.batasBawah;
   double pEntry = AlignHargaTick(z.bullish ? z.batasAtas - g_SniperDepthPct * hZona : z.batasBawah + g_SniperDepthPct * hZona, !z.bullish);
   double pSL    = AlignHargaTick(z.bullish ? z.batasBawah - V24_Pip(8.0) : z.batasAtas + V24_Pip(8.0), !z.bullish);
   double pTP    = AlignHargaTick(z.bullish ? pEntry + MathAbs(pEntry - pSL) * 2.5 : pEntry - MathAbs(pEntry - pSL) * 2.5, z.bullish);

   if(!g_ShadowActive && MathAbs(px - pEntry) <= V24_Pip(2.0))
   {
      g_ShadowBull = z.bullish; g_ShadowEntry = pEntry; g_ShadowSL = pSL; g_ShadowTP = pTP; g_ShadowActive = true;
   }

   datetime t1 = TimeCurrent();
   datetime t2 = t1 + PeriodSeconds((ENUM_TIMEFRAMES)_Period) * 20;
   double lv[3] = {pEntry, pSL, pTP};
   color  cl[3] = {clrDodgerBlue, clrRed, clrLimeGreen};
   string tx[3] = {"NEXT SNIPER ENTRY (" + DoubleToString(g_SniperDepthPct*100,0) + "%)", "PLAN SL", "PLAN TP (1:2.5)"};

   for(int g = 0; g < 3; g++)
   {
      string nm = "A24_PLAN_" + IntegerToString(g);
      if(ObjectFind(0, nm) < 0) ObjectCreate(0, nm, OBJ_TREND, 0, t1, lv[g], t2, lv[g]);
      else { ObjectMove(0, nm, 0, t1, lv[g]); ObjectMove(0, nm, 1, t2, lv[g]); }
      ObjectSetInteger(0, nm, OBJPROP_COLOR, cl[g]);
      ObjectSetInteger(0, nm, OBJPROP_STYLE, STYLE_DASH);
      ObjectSetInteger(0, nm, OBJPROP_RAY_RIGHT, false);
      ObjectSetString(0, nm + "_TXT", OBJPROP_TEXT, tx[g]);
   }
}
Gunakan kode dengan hati-hati.

Langkah Pemasangan di MetaEditor

1. Buka file APlus V24.18.mq5 Anda di MetaEditor (F4 dari MT5).
2. Terapkan Blok 1 hingga Blok 8 sesuai petunjuk lokasi di atas.
3. Tekan F7 (Compile) dan pastikan 0 errors.
4. Di terminal MetaTrader 5, tekan F3 dan hapus sisa Global Variables lama berawalan AP418_ dan AP24_ agar memori baru bersih.
Apakah Anda membutuhkan bantuan untuk memeriksa hasil Compile jika muncul peringatan di MetaEditor, atau ingin saya bantu menuliskan bagian spesifik OnTradeTransaction agar detektor "SL+ tersapu" otomatis memperbarui g_BrainSLPlusR di Buku Otak?
