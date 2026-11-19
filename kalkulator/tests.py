from decimal import Decimal

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .fields import DEFAULTS
from .cetak_fields import DEFAULTS as CETAK_DEFAULTS
from .models import PrintingQuotation, Quotation
from .services.pricing import hitung
from .services.printing import hitung as hitung_cetak

GOLDEN = {
    "lembar_per_buku": "25",
    "total_lembar_jadi": "55000",
    "jumlah_plano": "13750",
    "jumlah_rim": "27.5",
    "harga_per_rim_isi": "444600",
    "subtotal_kertas": "12226500",
    "subtotal_plat_isi": "750000",
    "subtotal_cetak_isi": "2500000",
    "druk_isi_qty": "1200",
    "subtotal_druk_isi": "1200000",
    "lembar_cover": "275",
    "rim_cover": "0.55",
    "harga_per_rim_cover": "1278225",
    "subtotal_kertas_cover": "703023.75",
    "subtotal_plat_cover": "60000",
    "subtotal_cetak_cover": "200000",
    "subtotal_druk_cover": "96000",
    "lipat_dasar": "52000",
    "lipat_variabel": "1248000",
    "subtotal_lipat": "1398000",
    "subtotal_komplit": "699000",
    "subtotal_bending": "1771000",
    "subtotal_wrapping": "924000",
    "subtotal_kirim": "350000",
    "subtotal": "22877523.75",
    "nilai_margin": "6863257.125",
    "total": "29740780.875",
    "harga_unit": "14870.3904375",
    "total_setelah_diskon": "27740780.875",
    "harga_unit_setelah_diskon": "13870.3904375",
}


class OngkosCetakTest(SimpleTestCase):
    def test_komponen_dasar(self):
        hasil = hitung_cetak(
            dict(
                CETAK_DEFAULTS,
                oplah=2000,
                berat_potong=10,
                diskon=0,
                plat_rows=[{"unit_plat": "1/1", "oplah": 2000, "jumlah_keteran": 5, "harga_plat": 15000, "tarif_cetak": 50000}],
                lipat_rows=[{"jumlah_lembar": 5000, "lipat_faktor": 2, "harga_lipat": 12}],
            )
        )
        self.assertEqual(hasil["total_plat"], 10)
        self.assertEqual(hasil["subtotal_plat"], Decimal("150000"))
        self.assertEqual(hasil["subtotal_ongkos"], Decimal("500000"))
        self.assertEqual(hasil["subtotal_druk"], Decimal("200000"))
        self.assertEqual(hasil["subtotal_lipat"], Decimal("150000"))
        self.assertEqual(hasil["subtotal_potong"], Decimal("10000"))
        self.assertEqual(hasil["subtotal"], Decimal("1010000"))
        self.assertEqual(hasil["total"], Decimal("1313000"))
        self.assertEqual(hasil["harga_unit"], Decimal("656.5"))

    def test_beberapa_komponen_plat(self):
        hasil = hitung_cetak(
            dict(
                CETAK_DEFAULTS,
                oplah=2000,
                plat_rows=[
                    {"unit_plat": "4/1", "oplah": 2000, "jumlah_keteran": 25, "harga_plat": 15000, "tarif_cetak": 50000},
                    {"unit_plat": "1/1", "oplah": 2000, "jumlah_keteran": 5, "harga_plat": 15000, "tarif_cetak": 50000},
                ],
            )
        )
        self.assertEqual(hasil["total_plat"], 135)
        self.assertEqual(hasil["subtotal_plat"], Decimal("2025000"))
        self.assertEqual(hasil["subtotal_ongkos"], Decimal("6750000"))

    def test_druk_nol_jika_oplah_tidak_lebih_dari_1000(self):
        for oplah in (800, 1000):
            hasil = hitung_cetak(
                dict(
                    CETAK_DEFAULTS,
                    plat_rows=[{
                        "unit_plat": "1/1",
                        "oplah": oplah,
                        "jumlah_keteran": 5,
                        "harga_plat": 15000,
                        "tarif_cetak": 50000,
                    }],
                )
            )
            self.assertEqual(hasil["subtotal_druk"], Decimal("0"))

    def test_lipat_fifo_dan_biaya_tetap_sekali(self):
        hasil = hitung_cetak(
            dict(
                CETAK_DEFAULTS,
                plat_rows=[{"oplah": 2000}, {"oplah": 3000}],
                lipat_rows=[
                    {"lipat_faktor": 2, "harga_lipat": 12},
                    {"lipat_faktor": 1, "harga_lipat": 10},
                ],
            )
        )
        self.assertEqual(hasil["lipat_variabel"], Decimal("20000"))
        self.assertEqual(hasil["subtotal_lipat"], Decimal("170000"))

    def test_lipat_di_bawah_3000_tetap_150000(self):
        hasil = hitung_cetak(
            dict(
                CETAK_DEFAULTS,
                plat_rows=[{"oplah": 2000}],
                lipat_rows=[{"lipat_faktor": 2, "harga_lipat": 12}],
            )
        )
        self.assertEqual(hasil["subtotal_lipat"], Decimal("150000"))

    def test_unit_plat_custom_dihitung_dari_angka(self):
        hasil = hitung_cetak(
            dict(
                CETAK_DEFAULTS,
                plat_rows=[{"unit_plat": "6/2", "oplah": 2000, "jumlah_keteran": 2, "harga_plat": 15000}],
            )
        )
        self.assertEqual(hasil["total_plat"], 16)
        self.assertEqual(hasil["subtotal_plat"], Decimal("240000"))

    def test_plat_customer_tidak_dihitung(self):
        hasil = hitung_cetak(
            dict(
                CETAK_DEFAULTS,
                plat_rows=[{"unit_plat": "1/1", "oplah": 2000, "jumlah_keteran": 5, "plat_owner": "customer"}],
            )
        )
        self.assertEqual(hasil["subtotal_plat"], Decimal("0"))


def _payload_cetak():
    data = {
        key: (format(value, "f") if isinstance(value, Decimal) else str(value))
        for key, value in CETAK_DEFAULTS.items()
    }
    data.update(
        {
            "berat_potong": "10",
            "diskon": "0",
            "pelanggan": "Toko Buku",
            "telepon": "0812-3456",
            "judul_buku": "Buku Cetak",
            "unit_plat": ["4/1"],
            "oplah": ["2000"],
            "plat_per_set": ["5"],
            "jumlah_keteran": ["5"],
            "plat_owner": ["reda"],
            "harga_plat": ["15000"],
            "tarif_cetak": ["50000"],
            "lipat_faktor": ["2"],
            "harga_lipat": ["12"],
        }
    )
    return data


class OngkosAlurTest(TestCase):
    def test_simpan_dan_cetak_customer(self):
        response = self.client.post(reverse("kalkulator:ongkos_baru"), _payload_cetak())
        quotation = PrintingQuotation.objects.get()

        self.assertRedirects(response, reverse("kalkulator:ongkos_ubah", args=[quotation.pk]))
        self.assertTrue(quotation.nomor.startswith("OC-"))
        self.assertEqual(quotation.telepon, "0812-3456")

        cust = self.client.get(reverse("kalkulator:ongkos_cetak_cust", args=[quotation.pk]))
        self.assertContains(cust, quotation.nomor)
        self.assertContains(cust, "0812-3456")
        self.assertContains(cust, "Total setelah diskon")
        self.assertContains(cust, "Harga per eksemplar")

        internal = self.client.get(reverse("kalkulator:ongkos_cetak", args=[quotation.pk]))
        self.assertContains(internal, "Rincian ongkos cetak")
        self.assertContains(internal, "Margin")

        listing = self.client.get(reverse("kalkulator:ongkos_list"))
        self.assertContains(listing, quotation.nomor)

    def test_simpan_beberapa_komponen(self):
        payload = _payload_cetak()
        payload.update(
            {
                "unit_plat": ["4/1", "1/1"],
                "judul_komponen": ["Buku A", "Buku B"],
                "oplah": ["2000", "2000"],
                "plat_per_set": ["5", "2"],
                "jumlah_keteran": ["5", "1"],
                "plat_owner": ["reda", "reda"],
                "harga_plat": ["15000", "15000"],
                "tarif_cetak": ["50000", "50000"],
                "lipat_faktor": ["2", "1"],
                "harga_lipat": ["12", "10"],
            }
        )
        self.client.post(reverse("kalkulator:ongkos_baru"), payload)
        quotation = PrintingQuotation.objects.get()
        self.assertEqual(len(quotation.input_snapshot["plat_rows"]), 2)
        self.assertEqual(quotation.input_snapshot["plat_rows"][0]["judul_komponen"], "Buku A")
        self.assertEqual(quotation.input_snapshot["plat_rows"][1]["judul_komponen"], "Buku B")
        self.assertEqual(quotation.hasil_snapshot["total_plat"], "27")
        self.assertEqual(len(quotation.hasil_snapshot["lipat_rows"]), 2)

        internal = self.client.get(reverse("kalkulator:ongkos_cetak", args=[quotation.pk]))
        self.assertContains(internal, "Buku A")
        self.assertContains(internal, "Buku B")

        cust = self.client.get(reverse("kalkulator:ongkos_cetak_cust", args=[quotation.pk]))
        self.assertContains(cust, "Buku A")
        self.assertContains(cust, "Buku B")
        self.assertContains(cust, "4/1")
        self.assertContains(cust, "1/1")

    def test_form_dan_api_pratinjau(self):
        self.assertEqual(self.client.get(reverse("kalkulator:ongkos_baru")).status_code, 200)
        response = self.client.post(
            reverse("kalkulator:api_ongkos"),
            data={
                "plat_rows": [{"unit_plat": "1/1", "oplah": "2000", "jumlah_keteran": "5"}],
                "lipat_rows": [],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["partial"])
        self.assertContains(response, "Rp")

    def test_ubah_dan_hapus(self):
        self.client.post(reverse("kalkulator:ongkos_baru"), _payload_cetak())
        quotation = PrintingQuotation.objects.get()
        payload = _payload_cetak()
        payload["jumlah_keteran"] = ["6"]

        response = self.client.post(
            reverse("kalkulator:ongkos_ubah", args=[quotation.pk]), payload
        )
        self.assertRedirects(response, reverse("kalkulator:ongkos_ubah", args=[quotation.pk]))
        quotation.refresh_from_db()
        self.assertEqual(quotation.hasil_snapshot["total_plat"], "30")

        deleted = self.client.post(reverse("kalkulator:ongkos_hapus", args=[quotation.pk]))
        self.assertRedirects(deleted, reverse("kalkulator:ongkos_list"))
        self.assertFalse(PrintingQuotation.objects.exists())


class GoldenTest(SimpleTestCase):
    def test_default_input_matches_excel(self):
        hasil = hitung(DEFAULTS)
        for key, expected in GOLDEN.items():
            actual = Decimal(hasil[key])
            self.assertLessEqual(
                abs(actual - Decimal(expected)), Decimal("0.01"), f"{key}: {actual} != {expected}"
            )

    def test_lipat_di_bawah_3000_tetap_150000(self):
        hasil = hitung(dict(DEFAULTS, jumlah_bahan=100))
        self.assertEqual(hasil["lipat_dasar"], Decimal("0"))
        self.assertEqual(hasil["subtotal_lipat"], Decimal("150000"))
        self.assertEqual(hasil["subtotal_komplit"], Decimal("75000"))

    def test_rim_selalu_500(self):
        hasil = hitung(dict(DEFAULTS, lembar_per_rim=250, lembar_per_rim_cover=250))
        self.assertEqual(hasil["jumlah_rim"], Decimal("27.5"))
        self.assertEqual(hasil["rim_cover"], Decimal("0.55"))

    def test_ambang_lipat_selalu_3000(self):
        hasil = hitung(dict(DEFAULTS, ambang_lipat=100))
        self.assertEqual(hasil["lipat_dasar"], Decimal("52000"))

    def test_druk_cover_memakai_jumlah_plat(self):
        hasil = hitung(dict(DEFAULTS, up_cover=99))
        self.assertEqual(hasil["subtotal_druk_cover"], Decimal("96000"))

    def test_wrapping_memakai_tebal_bending(self):
        hasil = hitung(dict(DEFAULTS, bending_tebal=2))
        self.assertEqual(hasil["subtotal_bending"], Decimal("3542000"))
        self.assertEqual(hasil["subtotal_wrapping"], Decimal("1848000"))

    def test_pembulatan_hanya_mengubah_harga_final(self):
        hasil = hitung(dict(DEFAULTS, pembulatan="up_1000"))
        self.assertEqual(hasil["harga_unit"], Decimal("14870.3904375"))
        self.assertEqual(hasil["harga_unit_final"], Decimal("15000"))


def _payload():
    return {
        key: (format(value, "f") if isinstance(value, Decimal) else str(value))
        for key, value in DEFAULTS.items()
    }


class AlurTest(TestCase):
    def test_simpan_penawaran_dan_api(self):
        payload = _payload()
        payload.update({"pelanggan": "Toko Buku", "telepon": "0812-3456", "judul_buku": "Buku A", "pembulatan": "none"})

        response = self.client.post(reverse("kalkulator:hitung"), payload)
        self.assertEqual(response.status_code, 302)

        quotation = Quotation.objects.get()
        self.assertRegex(quotation.nomor, r"^RP-\d{8}-0001$")
        self.assertEqual(quotation.pelanggan, "Toko Buku")
        self.assertEqual(quotation.telepon, "0812-3456")
        self.assertEqual(Decimal(quotation.subtotal), Decimal("22877523.75"))
        self.assertEqual(quotation.hasil_snapshot["total"], "29740780.875")

        detail = self.client.get(reverse("kalkulator:detail", args=[quotation.pk]))
        self.assertContains(detail, "Rp22.877.523,75")

        cetak = self.client.get(reverse("kalkulator:cetak", args=[quotation.pk]))
        self.assertContains(cetak, quotation.nomor)

        cust = self.client.get(reverse("kalkulator:cetak_cust", args=[quotation.pk]))
        self.assertContains(cust, quotation.nomor)
        self.assertContains(cust, "Harga per eksemplar")
        self.assertContains(cust, "Finishing")
        self.assertContains(cust, "Cetak cover")
        self.assertContains(cust, "Bending")
        self.assertContains(cust, "Wrapping")
        self.assertContains(cust, "Ada")
        self.assertNotContains(cust, "Rincian per pos")
        self.assertNotContains(cust, "Margin")

        api = self.client.post(
            reverse("kalkulator:api_hitung"), data=payload, content_type="application/json"
        )
        self.assertEqual(api.status_code, 200)
        self.assertContains(api, "Rp29.740.780,88")
        self.assertFalse(api.json()["partial"])

    def test_api_pratinjau_sebagian(self):
        response = self.client.post(
            reverse("kalkulator:api_hitung"),
            data={"oplah": "1000"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["partial"])
        self.assertContains(response, "Rp0")
        self.assertNotContains(response, "Rp29.740.780,88")

    def test_plano_dropdown_mengubah_harga_kertas(self):
        hasil = hitung(dict(DEFAULTS, plano_isi="61x86"))
        self.assertEqual(hasil["harga_per_rim_isi"], Decimal("398696"))

    def test_plano_di_luar_daftar_ditolak(self):
        payload = _payload()
        payload["plano_isi"] = "99x99"
        response = self.client.post(reverse("kalkulator:hitung"), payload)
        self.assertEqual(response.status_code, 400)

    def test_form_baru_kosong(self):
        response = self.client.get(reverse("kalkulator:hitung"))
        self.assertContains(response, "Rp0")
        self.assertContains(response, "Margin (0%)")
        self.assertContains(response, "61 × 86 cm")
        self.assertContains(response, "500 gsm")
        self.assertContains(response, "Embos")
        self.assertContains(response, "4/4")
        self.assertNotContains(response, 'value="2000"')
        self.assertNotContains(response, 'value="2200"')

    def test_simpan_dengan_field_kosong(self):
        response = self.client.post(
            reverse("kalkulator:hitung"),
            {"oplah": "1000", "pembulatan": "none"},
        )
        self.assertEqual(response.status_code, 302)
        quotation = Quotation.objects.get()
        self.assertEqual(quotation.oplah, 1000)
        self.assertEqual(Decimal(quotation.total), Decimal("0"))

    def test_ubah_memperbarui_penawaran_yang_sama(self):
        payload = _payload()
        self.client.post(reverse("kalkulator:hitung"), payload)
        quotation = Quotation.objects.get()
        payload["oplah"] = "3000"

        response = self.client.post(reverse("kalkulator:ubah", args=[quotation.pk]), payload)

        self.assertRedirects(response, reverse("kalkulator:ubah", args=[quotation.pk]))
        self.assertEqual(Quotation.objects.count(), 1)
        quotation.refresh_from_db()
        self.assertEqual(quotation.oplah, 3000)

    def test_hapus_penawaran(self):
        self.client.post(reverse("kalkulator:hitung"), _payload())
        quotation = Quotation.objects.get()

        response = self.client.post(reverse("kalkulator:hapus", args=[quotation.pk]))

        self.assertRedirects(response, reverse("kalkulator:dashboard"))
        self.assertFalse(Quotation.objects.exists())

    def test_custom_finishing_dan_cetak_cover(self):
        payload = _payload()
        payload.update(
            {
                "finishing": "Spot UV",
                "cetak_cover": "4/2 + varnish",
            }
        )
        self.client.post(reverse("kalkulator:hitung"), payload)
        quotation = Quotation.objects.get()
        cust = self.client.get(reverse("kalkulator:cetak_cust", args=[quotation.pk]))
        self.assertContains(cust, "Spot UV")
        self.assertContains(cust, "4/2 + varnish")

    def test_diskon_melebihi_total_ditolak(self):
        payload = _payload()
        payload["diskon"] = "999999999"
        response = self.client.post(reverse("kalkulator:hitung"), payload)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Quotation.objects.exists())
