"""Validasi input §5 di batas kepercayaan (form & API)."""

from decimal import Decimal, InvalidOperation

from ..fields import (
    FIELDS, INT, TEXT, PEMBULATAN_CHOICES, PEMBULATAN_DEFAULT, NON_NEGATIVE_KEYS, CHOICE_VALUES,
)
from ..cetak_fields import (
    DEC, PLAT_OWNER_VALUES, LIPAT_VALUES, PLAT_ROW_KEYS, LIPAT_ROW_KEYS,
)

PEMBULATAN_VALUES = {value for value, _label in PEMBULATAN_CHOICES}


def _row_number(value, kind, minimum_zero=True):
    text = "" if value is None else str(value).strip()
    if text == "":
        return 0, None
    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError):
        return text, "Harus berupa angka."
    if not number.is_finite():
        return text, "Harus berupa angka."
    if kind == INT and number != number.to_integral_value():
        return text, "Harus bilangan bulat."
    if number < 0 or (not minimum_zero and number == 0):
        return text, "Tidak boleh negatif." if minimum_zero else "Harus lebih dari 0."
    return int(number) if kind == INT else number, None


def clean_plat_rows(rows):
    cleaned = []
    errors = []
    for row in rows:
        item = {}
        error = {}
        item["judul_komponen"] = str(row.get("judul_komponen") or "").strip()
        item["unit_plat"] = str(row.get("unit_plat") or "").strip()
        owner = str(row.get("plat_owner") or "reda").strip()
        if owner not in PLAT_OWNER_VALUES:
            error["plat_owner"] = "Pilih dari daftar."
            owner = "reda"
        item["plat_owner"] = owner

        for key, kind in (
            ("oplah", INT),
            ("plat_per_set", INT),
            ("jumlah_keteran", INT),
            ("harga_plat", DEC),
            ("tarif_cetak", DEC),
        ):
            value, message = _row_number(row.get(key), kind)
            item[key] = value
            if message:
                error[key] = message

        kosong = (
            not item["unit_plat"]
            and all(item[key] in ("", 0) for key in ("oplah", "plat_per_set", "jumlah_keteran", "harga_plat", "tarif_cetak"))
            and item["plat_owner"] == "reda"
        )
        if not kosong:
            cleaned.append(item)
        errors.append(error)

    return cleaned, errors


def clean_lipat_rows(rows):
    cleaned = []
    errors = []
    for row in rows:
        item = {}
        error = {}

        faktor = str(row.get("lipat_faktor") or "").strip()
        if faktor and faktor not in LIPAT_VALUES:
            error["lipat_faktor"] = "Pilih 1, 2, atau 3."
            faktor = 0
        item["lipat_faktor"] = int(faktor) if faktor else 0

        item["harga_lipat"], message = _row_number(row.get("harga_lipat"), DEC)
        if message:
            error["harga_lipat"] = message

        if item["lipat_faktor"] or item["harga_lipat"]:
            cleaned.append(item)
        errors.append(error)

    return cleaned, errors


def clean_input(raw, fields=None, non_negative=None, choices=None, with_pembulatan=True):
    """Kembalikan (data bersih, errors). Nilai tidak valid tetap disimpan mentah untuk re-render."""
    fields = FIELDS if fields is None else fields
    non_negative = NON_NEGATIVE_KEYS if non_negative is None else non_negative
    choices = CHOICE_VALUES if choices is None else choices
    data = {}
    errors = {}

    for key, label, kind, default, _unit, _group in fields:
        value = raw.get(key, "")
        raw_text = "" if value is None else str(value).strip()
        allowed = choices.get(key)
        if allowed is not None and raw_text != "" and raw_text not in allowed:
            data[key] = raw_text
            errors[key] = "Pilih dari daftar."
            continue
        if kind == TEXT:
            data[key] = raw_text
            continue

        if raw_text == "":
            data[key] = ""
            continue
        try:
            number = Decimal(raw_text)
        except (InvalidOperation, ValueError):
            data[key] = raw_text
            errors[key] = "Harus berupa angka."
            continue
        if not number.is_finite():
            data[key] = raw_text
            errors[key] = "Harus berupa angka."
            continue
        if kind == INT and number != number.to_integral_value():
            data[key] = raw_text
            errors[key] = "Harus bilangan bulat."
            continue

        strict = key not in non_negative
        if number < 0 or (strict and number == 0):
            data[key] = raw_text
            errors[key] = "Harus lebih dari 0." if strict else "Tidak boleh negatif."
            continue
        data[key] = int(number) if kind == INT else number

    if with_pembulatan:
        pembulatan = raw.get("pembulatan") or PEMBULATAN_DEFAULT
        data["pembulatan"] = pembulatan if pembulatan in PEMBULATAN_VALUES else PEMBULATAN_DEFAULT

    return data, errors
