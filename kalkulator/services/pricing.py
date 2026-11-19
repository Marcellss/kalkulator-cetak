"""Fungsi murni perhitungan harga cetak (spesifikasi §4). Tanpa I/O, tanpa DB."""

from decimal import Decimal, ROUND_CEILING, localcontext

from ..fields import DEFAULTS, NUMERIC_KEYS

STEP = {
    "none": None,
    "up_100": Decimal("100"),
    "up_500": Decimal("500"),
    "up_1000": Decimal("1000"),
}

# Satu rim selalu 500 lembar, bukan input staff.
RIM = Decimal("500")

# 3.000 lembar pertama kena biaya tetap lipat, bukan input staff.
AMBANG_LIPAT = Decimal("3000")


def _d(value):
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _div(numerator, denominator):
    # Pratinjau boleh berisi 0; simpan penawaran tetap divalidasi > 0.
    return numerator / denominator if denominator else Decimal("0")


def _plano_dims(value):
    """'65x90' -> (65, 90). Nilai kosong/tidak dikenal -> nol."""
    left, separator, right = str(value).lower().partition("x")
    if not separator:
        return Decimal("0"), Decimal("0")
    return _d(left.strip()), _d(right.strip())


def _bulat_atas(value, step):
    if step is None:
        return value
    return (value / step).to_integral_value(rounding=ROUND_CEILING) * step


def hitung(data=None):
    """Hitung satu penawaran. `data` berisi field §5 (boleh sebagian); default dipakai bila kosong."""
    inp = dict(DEFAULTS)
    for key, value in (data or {}).items():
        if key in inp and value is not None and value != "":
            inp[key] = value
    pembulatan = (data or {}).get("pembulatan") or "none"
    if pembulatan not in STEP:
        pembulatan = "none"

    with localcontext() as ctx:
        ctx.prec = 28
        values = {
            key: (_d(inp[key]) if key in NUMERIC_KEYS else inp[key]) for key in inp
        }
        d = values
        step = STEP[pembulatan]

        lembar_per_buku = _div(d["jlh_hal_isi"], d["hal_per_lembar"])
        total_lembar_jadi = lembar_per_buku * d["jumlah_bahan"]
        jumlah_plano = _div(total_lembar_jadi, d["up_per_plano"])
        jumlah_rim = _div(jumlah_plano, RIM)
        panjang_isi, lebar_isi = _plano_dims(d["plano_isi"])
        harga_per_rim_isi = (
            panjang_isi
            * lebar_isi
            * d["gramasi_isi"]
            * d["harga_kertas_isi"]
            * RIM
            / Decimal("10000000")
        )
        subtotal_kertas = jumlah_rim * harga_per_rim_isi

        subtotal_plat_isi = d["plat_isi_jumlah"] * lembar_per_buku * d["tarif_plat_isi"]
        subtotal_cetak_isi = (
            d["plat_isi_jumlah"] * lembar_per_buku * d["tarif_cetak_isi"]
        )
        druk_isi_qty = d["jumlah_bahan"] - d["pengurang_druk"]
        subtotal_druk_isi = (
            d["plat_isi_jumlah"] * lembar_per_buku * d["tarif_druk_isi"] * druk_isi_qty
        )

        lembar_cover = _div(d["jumlah_cover"], d["cover_per_lembar"])
        rim_cover = _div(lembar_cover, RIM)
        panjang_cover, lebar_cover = _plano_dims(d["plano_cover"])
        harga_per_rim_cover = (
            panjang_cover
            * lebar_cover
            * d["gramasi_cover"]
            * d["harga_kertas_cover"]
            * RIM
            / Decimal("10000000")
        )
        subtotal_kertas_cover = rim_cover * harga_per_rim_cover

        subtotal_plat_cover = d["plat_cover_jumlah"] * d["tarif_plat_cover"]
        subtotal_cetak_cover = d["plat_cover_jumlah"] * d["tarif_cetak_cover"]
        druk_cover_qty = d["jumlah_cover"] - d["pengurang_druk"]
        subtotal_druk_cover = druk_cover_qty * d["plat_cover_jumlah"] * d["tarif_druk_cover"]

        lipat_dasar = max(total_lembar_jadi - AMBANG_LIPAT, Decimal("0"))
        lipat_variabel = lipat_dasar * d["lipat_faktor_a"] * d["lipat_faktor_b"]
        subtotal_lipat = lipat_variabel + d["lipat_biaya_tetap"]
        subtotal_komplit = subtotal_lipat / 2
        subtotal_bending = (
            d["bending_jumlah"]
            * d["bending_tebal"]
            * d["tarif_bending"]
            * d["jumlah_bahan"]
        )
        subtotal_wrapping = (
            d["wrapping_jumlah"]
            * d["bending_tebal"]
            * d["tarif_wrapping"]
            * d["jumlah_bahan"]
        )
        subtotal_kirim = d["biaya_kirim"]

        subtotal = (
            subtotal_kertas
            + subtotal_plat_isi
            + subtotal_cetak_isi
            + subtotal_druk_isi
            + subtotal_kertas_cover
            + subtotal_plat_cover
            + subtotal_cetak_cover
            + subtotal_druk_cover
            + subtotal_lipat
            + subtotal_komplit
            + subtotal_bending
            + subtotal_wrapping
            + subtotal_kirim
        )
        nilai_margin = subtotal * d["margin_persen"] / Decimal("100")
        total = subtotal + nilai_margin
        harga_unit = _div(total, d["oplah"])
        total_setelah_diskon = total - d["diskon"]
        harga_unit_setelah_diskon = _div(total_setelah_diskon, d["oplah"])

        hasil = {
            "lembar_per_buku": lembar_per_buku,
            "total_lembar_jadi": total_lembar_jadi,
            "jumlah_plano": jumlah_plano,
            "jumlah_rim": jumlah_rim,
            "harga_per_rim_isi": harga_per_rim_isi,
            "subtotal_kertas": subtotal_kertas,
            "subtotal_plat_isi": subtotal_plat_isi,
            "subtotal_cetak_isi": subtotal_cetak_isi,
            "druk_isi_qty": druk_isi_qty,
            "subtotal_druk_isi": subtotal_druk_isi,
            "lembar_cover": lembar_cover,
            "rim_cover": rim_cover,
            "harga_per_rim_cover": harga_per_rim_cover,
            "subtotal_kertas_cover": subtotal_kertas_cover,
            "subtotal_plat_cover": subtotal_plat_cover,
            "subtotal_cetak_cover": subtotal_cetak_cover,
            "druk_cover_qty": druk_cover_qty,
            "subtotal_druk_cover": subtotal_druk_cover,
            "lipat_dasar": lipat_dasar,
            "lipat_variabel": lipat_variabel,
            "subtotal_lipat": subtotal_lipat,
            "subtotal_komplit": subtotal_komplit,
            "subtotal_bending": subtotal_bending,
            "subtotal_wrapping": subtotal_wrapping,
            "subtotal_kirim": subtotal_kirim,
            "subtotal": subtotal,
            "nilai_margin": nilai_margin,
            "total": total,
            "harga_unit": harga_unit,
            "total_setelah_diskon": total_setelah_diskon,
            "harga_unit_setelah_diskon": harga_unit_setelah_diskon,
            "harga_unit_final": _bulat_atas(harga_unit, step),
            "harga_unit_setelah_diskon_final": _bulat_atas(
                harga_unit_setelah_diskon, step
            ),
            "pembulatan": pembulatan,
        }

    hasil.update(values)
    return hasil
