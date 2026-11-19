"""Fungsi murni perhitungan ongkos cetak (tanpa biaya kertas)."""

from decimal import Decimal, localcontext

from ..cetak_fields import DEFAULTS, NUMERIC_KEYS, PLAT_PER_UNIT

PENGURANG_DRUK = Decimal("1000")
AMBANG_LIPAT = Decimal("3000")
BIAYA_TETAP_LIPAT = Decimal("150000")


def _d(value):
    return value if isinstance(value, Decimal) else Decimal(str(value or "0"))


def _i(value):
    return int(_d(value))


def _div(numerator, denominator):
    return numerator / denominator if denominator else Decimal("0")


def _nominal_plat(value):
    text = str(value or "").strip().lower()
    if text in PLAT_PER_UNIT:
        return PLAT_PER_UNIT[text]
    kiri, pemisah, kanan = text.partition("/")
    if pemisah and kiri.strip().isdigit() and kanan.strip().isdigit():
        return int(kiri) + int(kanan)
    return 0


def hitung(data=None):
    inp = dict(DEFAULTS)
    for key, value in (data or {}).items():
        if key in inp and value is not None and value != "":
            inp[key] = value

    with localcontext() as ctx:
        ctx.prec = 28
        d = {key: (_d(inp[key]) if key in NUMERIC_KEYS else inp[key]) for key in inp}

        plat_rows = []
        total_plat = Decimal("0")
        total_oplah = Decimal("0")
        subtotal_plat = Decimal("0")
        subtotal_ongkos = Decimal("0")
        subtotal_druk = Decimal("0")
        for row in (data or {}).get("plat_rows") or []:
            unit = str(row.get("unit_plat") or "")
            per_set = _nominal_plat(unit) or _i(row.get("plat_per_set"))
            keteran = _i(row.get("jumlah_keteran"))
            oplah = _i(row.get("oplah"))
            jumlah_plat = Decimal(per_set) * keteran
            harga_plat = _d(row.get("harga_plat"))
            tarif_cetak = _d(row.get("tarif_cetak"))
            owner = row.get("plat_owner") or "reda"
            baris_plat = Decimal("0") if owner == "customer" else jumlah_plat * harga_plat
            baris_ongkos = jumlah_plat * tarif_cetak
            druk_qty = max(Decimal(oplah) - PENGURANG_DRUK, Decimal("0"))
            baris_druk = druk_qty * jumlah_plat * d["tarif_druk"]

            total_plat += jumlah_plat
            total_oplah += oplah
            subtotal_plat += baris_plat
            subtotal_ongkos += baris_ongkos
            subtotal_druk += baris_druk
            plat_rows.append(
                {
                    **row,
                    "jumlah_plat": jumlah_plat,
                    "subtotal_plat": baris_plat,
                    "subtotal_ongkos": baris_ongkos,
                    "druk_qty": druk_qty,
                    "subtotal_druk": baris_druk,
                }
            )

        sisa_ambang = AMBANG_LIPAT
        lipat_variabel = Decimal("0")
        ada_lipat = False
        lipat_rows = []
        plat_input = (data or {}).get("plat_rows") or []
        for index, row in enumerate((data or {}).get("lipat_rows") or []):
            sumber = plat_input[index] if index < len(plat_input) else {}
            lembar = _d(sumber.get("oplah"))
            faktor = _d(row.get("lipat_faktor"))
            harga = _d(row.get("harga_lipat"))
            if lembar > 0:
                ada_lipat = True
            kena = max(lembar - sisa_ambang, Decimal("0"))
            sisa_ambang = max(sisa_ambang - lembar, Decimal("0"))
            variabel = kena * faktor * harga
            lipat_variabel += variabel
            lipat_rows.append({**row, "jumlah_lembar": lembar, "dasar": kena, "subtotal": variabel})

        biaya_tetap = BIAYA_TETAP_LIPAT if ada_lipat else Decimal("0")
        subtotal_lipat = lipat_variabel + biaya_tetap
        subtotal_potong = d["berat_potong"] * d["harga_potong"]

        subtotal = subtotal_plat + subtotal_ongkos + subtotal_druk + subtotal_lipat + subtotal_potong
        nilai_margin = subtotal * d["margin_persen"] / Decimal("100")
        total = subtotal + nilai_margin
        harga_unit = _div(total, total_oplah)
        total_setelah_diskon = total - d["diskon"]
        harga_unit_setelah_diskon = _div(total_setelah_diskon, total_oplah)

        hasil = {
            "plat_rows": plat_rows,
            "lipat_rows": lipat_rows,
            "oplah": total_oplah,
            "total_plat": total_plat,
            "subtotal_plat": subtotal_plat,
            "subtotal_ongkos": subtotal_ongkos,
            "subtotal_druk": subtotal_druk,
            "lipat_variabel": lipat_variabel,
            "biaya_tetap_lipat": biaya_tetap,
            "subtotal_lipat": subtotal_lipat,
            "subtotal_potong": subtotal_potong,
            "subtotal": subtotal,
            "nilai_margin": nilai_margin,
            "total": total,
            "harga_unit": harga_unit,
            "total_setelah_diskon": total_setelah_diskon,
            "harga_unit_setelah_diskon": harga_unit_setelah_diskon,
            "harga_unit_final": harga_unit,
            "harga_unit_setelah_diskon_final": harga_unit_setelah_diskon,
        }

    hasil.update(d)
    return hasil
