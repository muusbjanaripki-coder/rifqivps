
from dataclasses import dataclass
from enum import Enum
import unittest


# Spesifikasi dasar EA XAUUSD M5 APlus V4.16 MASTER
RISIKO_NORMAL_PERSEN = 0.35
RISIKO_SUPER_PERSEN = 0.50
MAX_SUPER = 8
MAX_BIASA = 5
MAX_RETEST = 3
TIMEFRAME_UTAMA = "M5"
TIMEFRAME_TAMBAHAN = "M1"


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


def hitung_batas_risiko(saldo, risiko_persen):
    if saldo <= 0:
        raise ValueError("Saldo harus lebih besar dari nol")
    if not 0 < risiko_persen <= 100:
        raise ValueError("Persentase risiko tidak valid")
    return saldo * risiko_persen / 100


def zona_layak(zona):
    return zona.valid and not zona.mitigated


def cari_tp_zona_berikutnya(zona_entry, semua_zona):
    """
    Cari zona lawan terdekat dengan kategori yang sama.
    Ini model sederhana untuk pengujian, bukan logika
    deteksi zona SMC/ICT pada EA MQL5.
    """
    if not zona_layak(zona_entry):
        return None

    if zona_entry.arah == "BUY":
        kandidat = [
            z for z in semua_zona
            if z.kategori == zona_entry.kategori
            and z.arah == "SELL"
            and zona_layak(z)
            and z.harga > zona_entry.harga
        ]
        return min(kandidat, key=lambda z: z.harga, default=None)

    if zona_entry.arah == "SELL":
        kandidat = [
            z for z in semua_zona
            if z.kategori == zona_entry.kategori
            and z.arah == "BUY"
            and zona_layak(z)
            and z.harga < zona_entry.harga
        ]
        return max(kandidat, key=lambda z: z.harga, default=None)

    raise ValueError("Arah entry harus BUY atau SELL")


class TesEA(unittest.TestCase):

    def test_risiko_normal(self):
        self.assertAlmostEqual(
            hitung_batas_risiko(10000, RISIKO_NORMAL_PERSEN),
            35.0
        )

    def test_risiko_super(self):
        self.assertAlmostEqual(
            hitung_batas_risiko(10000, RISIKO_SUPER_PERSEN),
            50.0
        )

    def test_saldo_tidak_valid(self):
        with self.assertRaises(ValueError):
            hitung_batas_risiko(0, RISIKO_NORMAL_PERSEN)

    def test_zona_termitigasi_ditolak(self):
        zona = Zona(KategoriZona.SUPER, "BUY", 2700, True, True)
        self.assertFalse(zona_layak(zona))

    def test_tp_harus_satu_kategori(self):
        entry = Zona(KategoriZona.SUPER, "BUY", 2700)
        zona_biasa = Zona(KategoriZona.BIASA, "SELL", 2710)
        zona_super = Zona(KategoriZona.SUPER, "SELL", 2720)

        tp = cari_tp_zona_berikutnya(
            entry, [zona_biasa, zona_super]
        )
        self.assertIs(tp, zona_super)

    def test_tp_memilih_zona_terdekat(self):
        entry = Zona(KategoriZona.RETEST, "BUY", 2700)
        jauh = Zona(KategoriZona.RETEST, "SELL", 2730)
        dekat = Zona(KategoriZona.RETEST, "SELL", 2715)

        tp = cari_tp_zona_berikutnya(entry, [jauh, dekat])
        self.assertIs(tp, dekat)

    def test_zona_invalid_tidak_jadi_tp(self):
        entry = Zona(KategoriZona.SUPER, "BUY", 2700)
        invalid = Zona(KategoriZona.SUPER, "SELL", 2710, False)

        self.assertIsNone(cari_tp_zona_berikutnya(entry, [invalid]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
