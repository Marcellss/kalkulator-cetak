"""Field, default, dan aturan baris untuk mode hitung ongkos cetak saja."""

from decimal import Decimal

INT = "int"
DEC = "dec"
TEXT = "text"

PLAT_PER_UNIT = {
    "1/1": 2,
    "2/1": 3,
    "2/2": 4,
    "4/1": 5,
    "4/2": 6,
    "4/3": 7,
    "4/4": 8,
}
HARGA_PLAT_DEFAULT = {"1/1": 15000, "2/1": 33000}
TARIF_CETAK_DEFAULT = {"1/1": 50000, "2/1": 75000}

UNIT_PLAT_SUGGESTIONS = ["1/1", "2/1", "2/2", "4/1", "4/2", "4/3", "4/4"]
PLAT_OWNER_CHOICES = [
    ("reda", "Disediakan Reda Printing"),
    ("customer", "Disediakan customer"),
]
PLAT_OWNER_VALUES = {value for value, _label in PLAT_OWNER_CHOICES}
LIPAT_CHOICES = [("", "— pilih —"), ("1", "1"), ("2", "2"), ("3", "3")]
LIPAT_VALUES = {"1", "2", "3"}

SUGGESTIONS = {
    "unit_plat": UNIT_PLAT_SUGGESTIONS,
    "harga_potong": ["1000", "800"],
}

FIELDS = [
    ("tarif_druk", "Tarif druk", DEC, 20, "Rp", "druk"),
    ("berat_potong", "Berat potong", DEC, 0, "kg", "finishing"),
    ("harga_potong", "Harga potong per kg", DEC, 1000, "Rp/kg", "finishing"),
    ("margin_persen", "Margin", DEC, 30, "%", "harga"),
    ("diskon", "Diskon", DEC, 0, "Rp", "harga"),
]

GROUPS = [
    ("plat", "Plat & Ongkos Cetak"),
    ("druk", "Druk"),
    ("finishing", "Lipat & Potong"),
    ("harga", "Harga Jual"),
]

PLAT_ROW_KEYS = [
    "judul_komponen",
    "unit_plat",
    "oplah",
    "plat_per_set",
    "jumlah_keteran",
    "plat_owner",
    "harga_plat",
    "tarif_cetak",
]
LIPAT_ROW_KEYS = ["lipat_faktor", "harga_lipat"]

PLAT_ROW_DEFAULTS = {
    "judul_komponen": "",
    "unit_plat": "",
    "oplah": 0,
    "plat_per_set": 0,
    "jumlah_keteran": 0,
    "plat_owner": "reda",
    "harga_plat": 0,
    "tarif_cetak": 0,
}
LIPAT_ROW_DEFAULTS = {"lipat_faktor": 2, "harga_lipat": 12}

_DEFAULT_BY_KIND = {
    INT: lambda v: int(v),
    DEC: lambda v: Decimal(str(v)),
    TEXT: lambda v: str(v),
}

DEFAULTS = {
    key: _DEFAULT_BY_KIND[kind](default)
    for key, _label, kind, default, _unit, _group in FIELDS
}
NUMERIC_KEYS = {
    key for key, _label, kind, _default, _unit, _group in FIELDS if kind in (INT, DEC)
}
NON_NEGATIVE_KEYS = {"diskon", "berat_potong"}
