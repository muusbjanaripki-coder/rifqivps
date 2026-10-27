
from dataclasses import dataclass
from enum import Enum
import unittest

RISIKO_NORMAL_PERSEN = 0.35
RISIKO_SUPER_PERSEN = 0.50
BATAS_RUGI_HARIAN_PERSEN = 4.0

MAX_SUPER = 8
MAX_BIASA = 5
MAX_RETEST = 3


class KategoriZona(Enum):
    SUPER = "Super"
    BIASA = "Biasa"
    RETEST = "Retest"


@dataclass
class Zona:
    kategori: KategoriZona
    arah: str
    harga: float
    valid: bool = True
    mitigated: bool = False


def hitung_batas_risiko(saldo, persen):
    if saldo <= 0:
        raise ValueError("Saldo harus lebih besar dari nol")
    if not 0 < persen <= 100:
        raise ValueError("Persentase risiko tidak valid")
    return saldo * persen / 100


def zona_layak(zona):
    return zona.valid and not zona.mitigated


def cari_tp_zona_berikutnya(entry, semua_zona):
    if not zona_layak(entry):
        return None

    if entry.arah == "BUY":
        kandidat = [
            z for z in semua_zona
            if z.kategori == entry.kategori
            and z.arah == "SELL"
            and zona_layak(z)
            and z.harga > entry.harga
        ]
        return min(kandidat, key=lambda z: z.harga, default=None)

    if entry.arah == "SELL":
        kandidat = [
            z for z in semua_zona
            if z.kategori == entry.kategori
            and z.arah == "BUY"
            and zona_layak(z)
            and z.harga < entry.harga
        ]
        return max(kandidat, key=lambda z: z.harga, default=None)

    raise ValueError("Arah harus BUY atau SELL")


def batas_entry(kategori):
    return {
        KategoriZona.SUPER: MAX_SUPER,
        KategoriZona.BIASA: MAX_BIASA,
        KategoriZona.RETEST: MAX_RETEST,
    }[kategori]


def rugi_harian_mencapai_batas(saldo_awal, rugi):
    if saldo_awal <= 0 or rugi < 0:
        raise ValueError("Saldo atau nilai rugi tidak valid")
    return rugi >= saldo_awal * BATAS_RUGI_HARIAN_PERSEN / 100


class TesEA(unittest.TestCase):

    def test_risiko_normal(self):
        self.assertAlmostEqual(
            hitung_batas_risiko(10000, RISIKO_NORMAL_PERSEN), 35
        )

    def test_risiko_super(self):
        self.assertAlmostEqual(
            hitung_batas_risiko(10000, RISIKO_SUPER_PERSEN), 50
        )

    def test_saldo_nol_ditolak(self):
        with self.assertRaises(ValueError):
            hitung_batas_risiko(0, RISIKO_NORMAL_PERSEN)

    def test_tp_buy_zona_sejenis_terdekat(self):
        entry = Zona(KategoriZona.SUPER, "BUY", 2700)
        jauh = Zona(KategoriZona.SUPER, "SELL", 2730)
        dekat = Zona(KategoriZona.SUPER, "SELL", 2715)
        beda = Zona(KategoriZona.BIASA, "SELL", 2710)

        self.assertIs(
            cari_tp_zona_berikutnya(entry, [jauh, dekat, beda]), dekat
        )

    def test_tp_sell_zona_sejenis_terdekat(self):
        entry = Zona(KategoriZona.RETEST, "SELL", 2700)
        jauh = Zona(KategoriZona.RETEST, "BUY", 2670)
        dekat = Zona(KategoriZona.RETEST, "BUY", 2690)

        self.assertIs(
            cari_tp_zona_berikutnya(entry, [jauh, dekat]), dekat
        )

    def test_zona_invalid_dan_termitigasi_ditolak(self):
        entry = Zona(KategoriZona.SUPER, "BUY", 2700)
        invalid = Zona(KategoriZona.SUPER, "SELL", 2710, valid=False)
        mitigated = Zona(
            KategoriZona.SUPER, "SELL", 2720, mitigated=True
        )

        self.assertIsNone(
            cari_tp_zona_berikutnya(entry, [invalid, mitigated])
        )

    def test_batas_entry_per_kategori(self):
        self.assertEqual(batas_entry(KategoriZona.SUPER), 8)
        self.assertEqual(batas_entry(KategoriZona.BIASA), 5)
        self.assertEqual(batas_entry(KategoriZona.RETEST), 3)

    def test_batas_rugi_harian_empat_persen(self):
        self.assertTrue(rugi_harian_mencapai_batas(10000, 400))
        self.assertFalse(rugi_harian_mencapai_batas(10000, 399))

    def test_arah_entry_tidak_valid(self):
        entry = Zona(KategoriZona.SUPER, "SIDEWAYS", 2700)
        with self.assertRaises(ValueError):
            cari_tp_zona_berikutnya(entry, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
