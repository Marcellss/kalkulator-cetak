"""Satu sumber daftar field input (spesifikasi §5) dan nilai defaultnya."""

from decimal import Decimal

INT = "int"
DEC = "dec"
TEXT = "text"

PLANO_VALUES = ["61x86", "65x90", "65x100", "61x92", "120x90"]
GRAMASI_VALUES = [
    "60",
    "70",
    "80",
    "100",
    "190",
    "210",
    "230",
    "260",
    "310",
    "350",
    "400",
    "500",
]


def _pilihan_plano():
    return [("", "— pilih —")] + [
        (v, v.replace("x", " × ") + " cm") for v in PLANO_VALUES
    ]


def _pilihan_gramasi():
    return [("", "— pilih —")] + [(v, v + " gsm") for v in GRAMASI_VALUES]


CHOICES = {
    "plano_isi": _pilihan_plano(),
    "plano_cover": _pilihan_plano(),
    "gramasi_isi": _pilihan_gramasi(),
    "gramasi_cover": _pilihan_gramasi(),
    "lipat_faktor_a": [("", "— pilih —"), ("1", "1"), ("2", "2"), ("3", "3")],
}

SUGGESTIONS = {
    "finishing": ["Doff", "Glossy", "Embos", "Polly"],
    "cetak_cover": ["4/0", "4/1", "4/4"],
}
CHOICE_VALUES = {
    key: {value for value, _label in choices if value}
    for key, choices in CHOICES.items()
}
PLANO_KEYS = {"plano_isi", "plano_cover"}

# key, label, kind, default, satuan, grup
FIELDS = [
    ("oplah", "Oplah (Q)", INT, 2000, "eksemplar", "kertas_isi"),
    (
        "jumlah_bahan",
        "Jumlah bahan / set bahan (Qb)",
        INT,
        2200,
        "set bahan",
        "kertas_isi",
    ),
    ("jlh_hal_isi", "Jumlah halaman isi", INT, 200, "halaman", "kertas_isi"),
    ("hal_per_lembar", "Halaman per lembar", INT, 8, "hal/lembar", "kertas_isi"),
    ("up_per_plano", "Up per plano (isi)", INT, 4, "up", "kertas_isi"),
    ("plano_isi", "Plano isi (P × L)", TEXT, "65x90", "cm", "kertas_isi"),
    ("gramasi_isi", "Gramasi kertas isi", DEC, 80, "gsm", "kertas_isi"),
    ("harga_kertas_isi", "Harga kertas isi", DEC, 19000, "Rp/kg", "kertas_isi"),
    ("plat_isi_jumlah", "Jumlah plat isi", INT, 2, "plat", "plat_isi"),
    ("tarif_plat_isi", "Tarif plat isi", DEC, 15000, "Rp/plat", "plat_isi"),
    ("tarif_cetak_isi", "Tarif ongkos cetak isi", DEC, 50000, "Rp/bentuk", "plat_isi"),
    ("tarif_druk_isi", "Tarif druk isi", DEC, 20, "Rp", "plat_isi"),
    ("pengurang_druk", "Pengurang druk", INT, 1000, "lembar", "plat_isi"),
    ("jumlah_cover", "Jumlah cover", INT, 2200, "cover", "kertas_cover"),
    ("cover_per_lembar", "Cover per lembar", INT, 8, "cover/lembar", "kertas_cover"),
    ("plano_cover", "Plano cover (P × L)", TEXT, "65x90", "cm", "kertas_cover"),
    ("gramasi_cover", "Gramasi cover", DEC, 230, "gsm", "kertas_cover"),
    ("harga_kertas_cover", "Harga kertas cover", DEC, 19000, "Rp/kg", "kertas_cover"),
    ("plat_cover_jumlah", "Jumlah plat cover", INT, 4, "plat", "plat_cover"),
    ("tarif_plat_cover", "Tarif plat cover", DEC, 15000, "Rp/plat", "plat_cover"),
    (
        "tarif_cetak_cover",
        "Tarif ongkos cetak cover",
        DEC,
        50000,
        "Rp/bentuk",
        "plat_cover",
    ),
    ("tarif_druk_cover", "Tarif druk cover", DEC, 20, "Rp", "plat_cover"),
    ("lipat_faktor_a", "Lipat", DEC, 2, "-", "finishing"),
    ("lipat_faktor_b", "Harga lipat setelah 3000", DEC, 12, "Rp", "finishing"),
    ("lipat_biaya_tetap", "Biaya tetap lipat", DEC, 150000, "Rp", "finishing"),
    ("bending_jumlah", "Tinggi buku bending", INT, 23, "-", "finishing"),
    ("bending_tebal", "Tebal buku", DEC, 1, "-", "finishing"),
    ("tarif_bending", "Tarif bending", DEC, 35, "Rp", "finishing"),
    ("wrapping_jumlah", "Tinggi buku wrapping", INT, 21, "-", "finishing"),
    ("tarif_wrapping", "Tarif wrapping", DEC, 20, "Rp", "finishing"),
    ("biaya_kirim", "Biaya kirim", DEC, 350000, "Rp", "finishing"),
    ("margin_persen", "Margin", DEC, 30, "%", "harga"),
    ("diskon", "Diskon", DEC, 2000000, "Rp", "harga"),
    ("finishing", "Finishing", TEXT, "", "-", "info"),
    ("cetak_cover", "Cetak Cover", TEXT, "", "-", "info"),
    ("ukuran_buku", "Ukuran buku (info)", TEXT, "", "-", "info"),
    ("bahan_isi", "Bahan isi (info)", TEXT, "", "-", "info"),
    ("bahan_cover", "Bahan cover (info)", TEXT, "", "-", "info"),
]

GROUPS = [
    ("kertas_isi", "Kertas Isi"),
    ("plat_isi", "Plat & Cetak Isi"),
    ("kertas_cover", "Kertas Cover"),
    ("plat_cover", "Plat & Cetak Cover"),
    ("finishing", "Finishing & Kirim"),
    ("harga", "Harga Jual"),
]

INFO_GROUP = "info"

PEMBULATAN_CHOICES = [
    ("none", "Tanpa pembulatan (2 desimal)"),
    ("up_100", "Bulatkan ke atas Rp100"),
    ("up_500", "Bulatkan ke atas Rp500"),
    ("up_1000", "Bulatkan ke atas Rp1.000"),
]
PEMBULATAN_DEFAULT = "none"

_DEFAULT_BY_KIND = {
    INT: lambda v: int(v),
    DEC: lambda v: Decimal(str(v)),
    TEXT: lambda v: str(v),
}

DEFAULTS = {
    key: _DEFAULT_BY_KIND[kind](default) for key, _l, kind, default, _u, _g in FIELDS
}

NUMERIC_KEYS = {key for key, _l, kind, _d, _u, _g in FIELDS if kind in (INT, DEC)}

NON_NEGATIVE_KEYS = {"diskon"} | {
    key for key, *_rest in FIELDS if key.startswith("tarif_")
}
