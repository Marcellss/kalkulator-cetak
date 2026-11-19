import json
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .fields import (
    DEFAULTS, FIELDS, GROUPS, INFO_GROUP, NUMERIC_KEYS, PEMBULATAN_CHOICES, PEMBULATAN_DEFAULT,
    CHOICES, PLANO_KEYS, PLANO_VALUES, SUGGESTIONS,
)
from .cetak_fields import (
    DEFAULTS as CETAK_DEFAULTS, FIELDS as CETAK_FIELDS, GROUPS as CETAK_GROUPS,
    HARGA_PLAT_DEFAULT, NUMERIC_KEYS as CETAK_NUMERIC_KEYS,
    NON_NEGATIVE_KEYS as CETAK_NON_NEGATIVE, PLAT_PER_UNIT,
    PLAT_ROW_KEYS, LIPAT_ROW_KEYS,
    PLAT_OWNER_CHOICES, LIPAT_CHOICES, UNIT_PLAT_SUGGESTIONS,
    SUGGESTIONS as CETAK_SUGGESTIONS, TARIF_CETAK_DEFAULT,
)
from .models import PaperGrade, PrintingQuotation, Quotation, RatePreset
from .services.pricing import hitung
from .services.printing import hitung as hitung_cetak
from .services.validation import clean_input, clean_lipat_rows, clean_plat_rows


def _plain(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def _field_groups(data, errors=None, fields=None, groups=None):
    fields = FIELDS if fields is None else fields
    groups = GROUPS if groups is None else groups
    errors = errors or {}
    result = []
    for gkey, glabel in groups:
        items = []
        for key, label, kind, default, unit, group in fields:
            if group != gkey:
                continue
            value = data.get(key, default)
            items.append(
                {
                    "key": key,
                    "label": label,
                    "kind": kind,
                    "unit": unit,
                    "value": "" if value is None else _plain(value),
                    "error": errors.get(key),
                    "choices": CHOICES.get(key),
                    "suggestions": SUGGESTIONS.get(key) or CETAK_SUGGESTIONS.get(key),
                }
            )
        result.append({"key": gkey, "label": glabel, "fields": items})
    return result


def _info_fields(data):
    return [
        {
            "key": key,
            "label": label,
            "value": "" if data.get(key) is None else _plain(data.get(key, "")),
            "choices": CHOICES.get(key),
            "suggestions": SUGGESTIONS.get(key),
        }
        for key, label, kind, _default, _unit, group in FIELDS
        if group == INFO_GROUP
    ]


def _angka_nol(data, numeric_keys=None, plano_keys=None):
    """Pratinjau: field kosong dihitung 0 (plano kosong = 0x0), bukan default Excel."""
    numeric_keys = NUMERIC_KEYS if numeric_keys is None else numeric_keys
    plano_keys = PLANO_KEYS if plano_keys is None else plano_keys
    hasil = {}
    for key, value in data.items():
        if value is None or value == "":
            if key in numeric_keys:
                hasil[key] = 0
            elif key in plano_keys:
                hasil[key] = "0x0"
            else:
                hasil[key] = value
        else:
            hasil[key] = value
    return hasil


def _plano_lama(snapshot, prefix):
    nilai = f"{snapshot.get('panjang_' + prefix, '')}x{snapshot.get('lebar_' + prefix, '')}"
    return nilai if nilai in PLANO_VALUES else ""


def _form_context(
    data, errors=None, preset=None, asal_nomor=None, edit_nomor=None, edit_pk=None,
    form_action=None, pelanggan="", telepon="", judul_buku="", tampilkan_hasil=False,
):
    return {
        "groups": _field_groups(data, errors),
        "info_fields": _info_fields(data),
        "errors": errors or {},
        "hasil": hitung(_angka_nol(data)) if tampilkan_hasil and not errors else None,
        "pembulatan": data.get("pembulatan", PEMBULATAN_DEFAULT),
        "pembulatan_choices": PEMBULATAN_CHOICES,
        "preset": preset,
        "asal_nomor": asal_nomor,
        "edit_nomor": edit_nomor,
        "edit_pk": edit_pk,
        "form_action": form_action,
        "pelanggan": pelanggan,
        "telepon": telepon,
        "judul_buku": judul_buku,
    }


def _jsonable(data):
    def convert(value):
        if isinstance(value, Decimal):
            return _plain(value)
        if isinstance(value, dict):
            return {key: convert(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [convert(item) for item in value]
        return value

    return {key: convert(value) for key, value in data.items()}


def _nomor_baru():
    today = timezone.localdate()
    prefix = f"RP-{today:%Y%m%d}-"
    seq = Quotation.objects.select_for_update().filter(nomor__startswith=prefix).count() + 1
    nomor = f"{prefix}{seq:04d}"
    while Quotation.objects.filter(nomor=nomor).exists():
        seq += 1
        nomor = f"{prefix}{seq:04d}"
    return nomor


def _simpan(data, hasil, request, quotation=None):
    with transaction.atomic():
        if quotation is None:
            quotation = Quotation(
                nomor=_nomor_baru(),
                dibuat_oleh=request.user.get_username() if request.user.is_authenticated else "",
            )
        quotation.pelanggan = (request.POST.get("pelanggan") or "").strip()
        quotation.telepon = (request.POST.get("telepon") or "").strip()
        quotation.judul_buku = (request.POST.get("judul_buku") or "").strip()
        quotation.ukuran_buku = data.get("ukuran_buku", "")
        quotation.bahan_isi = data.get("bahan_isi", "")
        quotation.bahan_cover = data.get("bahan_cover", "")
        quotation.oplah = hasil["oplah"]
        quotation.margin_persen = hasil["margin_persen"]
        quotation.diskon = hasil["diskon"]
        quotation.subtotal = hasil["subtotal"]
        quotation.nilai_margin = hasil["nilai_margin"]
        quotation.total = hasil["total"]
        quotation.harga_unit = hasil["harga_unit"]
        quotation.total_setelah_diskon = hasil["total_setelah_diskon"]
        quotation.harga_unit_setelah_diskon = hasil["harga_unit_setelah_diskon"]
        quotation.input_snapshot = _jsonable(data)
        quotation.hasil_snapshot = _jsonable(hasil)
        quotation.save()
        return quotation


def _cetak_nomor_baru():
    today = timezone.localdate()
    prefix = f"OC-{today:%Y%m%d}-"
    seq = PrintingQuotation.objects.select_for_update().filter(nomor__startswith=prefix).count() + 1
    nomor = f"{prefix}{seq:04d}"
    while PrintingQuotation.objects.filter(nomor=nomor).exists():
        seq += 1
        nomor = f"{prefix}{seq:04d}"
    return nomor


def _simpan_cetak(data, hasil, request, quotation=None):
    with transaction.atomic():
        if quotation is None:
            quotation = PrintingQuotation(
                nomor=_cetak_nomor_baru(),
                dibuat_oleh=request.user.get_username() if request.user.is_authenticated else "",
            )
        quotation.pelanggan = (request.POST.get("pelanggan") or "").strip()
        quotation.telepon = (request.POST.get("telepon") or "").strip()
        quotation.judul_buku = (request.POST.get("judul_buku") or "").strip()
        quotation.oplah = hasil["oplah"]
        quotation.margin_persen = hasil["margin_persen"]
        quotation.diskon = hasil["diskon"]
        quotation.subtotal = hasil["subtotal"]
        quotation.nilai_margin = hasil["nilai_margin"]
        quotation.total = hasil["total"]
        quotation.harga_unit = hasil["harga_unit"]
        quotation.total_setelah_diskon = hasil["total_setelah_diskon"]
        quotation.harga_unit_setelah_diskon = hasil["harga_unit_setelah_diskon"]
        quotation.input_snapshot = _jsonable(data)
        quotation.hasil_snapshot = _jsonable(hasil)
        quotation.save()
        return quotation


def _rows_from_post(post, keys):
    if hasattr(post, "getlist"):
        columns = {key: post.getlist(key) for key in keys}
    else:
        columns = {}
        for key in keys:
            value = post.get(key)
            columns[key] = value if isinstance(value, list) else [value]
    total = max((len(values) for values in columns.values()), default=0)
    return [
        {key: (columns[key][index] if index < len(columns[key]) else "") for key in keys}
        for index in range(total)
    ]


def _raw_rows(raw, name, keys):
    if isinstance(raw, dict) and isinstance(raw.get(name), list):
        return [row for row in raw[name] if isinstance(row, dict)]
    return _rows_from_post(raw, keys)


def _baris_kosong():
    plat = {key: ("" if key != "plat_owner" else "reda") for key in PLAT_ROW_KEYS}
    lipat = {key: "" for key in LIPAT_ROW_KEYS}
    return plat, lipat


def _baris_dari_snapshot(snapshot):
    if snapshot.get("plat_rows") is not None:
        return snapshot.get("plat_rows") or [], snapshot.get("lipat_rows") or []

    plat = [{
        "judul_komponen": "",
        "unit_plat": snapshot.get("unit_plat", ""),
        "oplah": snapshot.get("oplah", ""),
        "plat_per_set": snapshot.get("plat_per_set", ""),
        "jumlah_keteran": snapshot.get("jumlah_keteran", ""),
        "plat_owner": snapshot.get("plat_owner", "reda"),
        "harga_plat": snapshot.get("harga_plat", ""),
        "tarif_cetak": snapshot.get("tarif_cetak", ""),
    }]
    lipat = [{
        "jumlah_lembar": snapshot.get("jumlah_kertas", snapshot.get("oplah", "")),
        "lipat_faktor": snapshot.get("lipat_faktor", ""),
        "harga_lipat": snapshot.get("harga_lipat", ""),
    }]
    return plat, lipat


def _parse_cetak(raw):
    scalars, errors = clean_input(
        raw, CETAK_FIELDS, CETAK_NON_NEGATIVE, {}, with_pembulatan=False,
    )
    plat_raw = _raw_rows(raw, "plat_rows", PLAT_ROW_KEYS)
    lipat_raw = _raw_rows(raw, "lipat_rows", LIPAT_ROW_KEYS)
    if not plat_raw:
        plat_raw = [{key: ("" if key != "plat_owner" else "reda") for key in PLAT_ROW_KEYS}]
    if not lipat_raw:
        lipat_raw = [{key: "" for key in LIPAT_ROW_KEYS}]

    plat_clean, plat_errors = clean_plat_rows(plat_raw)
    lipat_clean, lipat_errors = clean_lipat_rows(lipat_raw)

    for index, error in enumerate(plat_errors):
        for field, message in error.items():
            errors[f"plat-{index}-{field}"] = message
    for index, error in enumerate(lipat_errors):
        for field, message in error.items():
            errors[f"lipat-{index}-{field}"] = message

    data = scalars
    data["plat_rows"] = plat_clean
    data["lipat_rows"] = lipat_clean
    return data, errors, plat_raw, lipat_raw, plat_errors, lipat_errors


def _ui_rows(raw_rows, keys, errors):
    result = []
    for index, row in enumerate(raw_rows):
        values = {key: ("" if row.get(key) is None else _plain(row.get(key))) for key in keys}
        values["errors"] = errors[index] if index < len(errors) else {}
        result.append(values)
    return result


def _cetak_context(data, plat_raw, lipat_raw, errors=None, plat_errors=None,
                   lipat_errors=None, edit=None, form_action=None,
                   pelanggan="", telepon="", judul_buku="", tampilkan_hasil=False):
    plat_ui = _ui_rows(plat_raw, PLAT_ROW_KEYS, plat_errors or [])
    lipat_ui = _ui_rows(lipat_raw, LIPAT_ROW_KEYS, lipat_errors or [])
    for index, row in enumerate(lipat_ui):
        row["jumlah_lembar"] = plat_ui[index].get("oplah", "") if index < len(plat_ui) else ""
    return {
        "groups": _field_groups(data, errors or {}, CETAK_FIELDS, CETAK_GROUPS),
        "errors": errors or {},
        "hasil": hitung_cetak(data) if tampilkan_hasil and not errors else None,
        "plat_rows": plat_ui,
        "lipat_rows": lipat_ui,
        "edit": edit,
        "form_action": form_action,
        "pelanggan": pelanggan,
        "telepon": telepon,
        "judul_buku": judul_buku,
        "plat_map": PLAT_PER_UNIT,
        "harga_plat_map": HARGA_PLAT_DEFAULT,
        "tarif_cetak_map": TARIF_CETAK_DEFAULT,
        "plat_owner_choices": PLAT_OWNER_CHOICES,
        "lipat_choices": LIPAT_CHOICES,
        "unit_plat_suggestions": UNIT_PLAT_SUGGESTIONS,
        "plat_kosong": _baris_kosong()[0],
        "lipat_kosong": _baris_kosong()[1],
    }


def _normalisasi_hasil(hasil):
    if hasil.get("plat_rows") is not None:
        return hasil
    hasil = dict(hasil)
    hasil["plat_rows"] = [{
        "judul_komponen": "",
        "unit_plat": hasil.get("unit_plat", ""),
        "oplah": hasil.get("oplah", ""),
        "plat_per_set": hasil.get("plat_per_set", ""),
        "jumlah_keteran": hasil.get("jumlah_keteran", ""),
        "plat_owner": hasil.get("plat_owner", "reda"),
        "harga_plat": hasil.get("harga_plat", ""),
        "tarif_cetak": hasil.get("tarif_cetak", ""),
        "jumlah_plat": hasil.get("total_plat", 0),
        "subtotal_plat": hasil.get("subtotal_plat", 0),
        "subtotal_ongkos": hasil.get("subtotal_ongkos", 0),
        "druk_qty": hasil.get("druk_qty", 0),
        "subtotal_druk": hasil.get("subtotal_druk", 0),
    }]
    hasil["lipat_rows"] = [{
        "jumlah_lembar": hasil.get("jumlah_kertas", hasil.get("oplah", "")),
        "lipat_faktor": hasil.get("lipat_faktor", ""),
        "harga_lipat": hasil.get("harga_lipat", ""),
        "dasar": hasil.get("lipat_dasar", 0),
        "subtotal": max(Decimal(str(hasil.get("subtotal_lipat", 0))) - Decimal("150000"), Decimal("0")),
    }]
    hasil.setdefault(
        "biaya_tetap_lipat",
        Decimal("150000") if Decimal(str(hasil.get("subtotal_lipat", 0))) > 0 else Decimal("0"),
    )
    return hasil


def ongkos_list(request):
    return render(
        request,
        "kalkulator/ongkos_list.html",
        {"items": PrintingQuotation.objects.all()[:50]},
    )


def ongkos_baru(request):
    if request.method == "POST":
        data, errors, plat_raw, lipat_raw, plat_errors, lipat_errors = _parse_cetak(request.POST)
        if not errors:
            hasil = hitung_cetak(data)
            if hasil["diskon"] > hasil["total"]:
                errors["diskon"] = "Diskon melebihi total penawaran."
            else:
                quotation = _simpan_cetak(data, hasil, request)
                messages.success(request, f"{quotation.nomor} tersimpan.")
                return redirect("kalkulator:ongkos_ubah", pk=quotation.pk)
        return render(
            request,
            "kalkulator/ongkos_form.html",
            _cetak_context(data, plat_raw, lipat_raw, errors, plat_errors, lipat_errors),
            status=400,
        )

    plat_raw, lipat_raw = _baris_kosong()
    data = dict(CETAK_DEFAULTS)
    return render(
        request,
        "kalkulator/ongkos_form.html",
        _cetak_context(
            data, [plat_raw], [lipat_raw], tampilkan_hasil=True,
        ),
    )


def ongkos_ubah(request, pk):
    quotation = get_object_or_404(PrintingQuotation, pk=pk)
    form_action = reverse("kalkulator:ongkos_ubah", args=[quotation.pk])
    if request.method == "POST":
        data, errors, plat_raw, lipat_raw, plat_errors, lipat_errors = _parse_cetak(request.POST)
        if not errors:
            hasil = hitung_cetak(data)
            if hasil["diskon"] > hasil["total"]:
                errors["diskon"] = "Diskon melebihi total penawaran."
            else:
                _simpan_cetak(data, hasil, request, quotation=quotation)
                messages.success(request, f"{quotation.nomor} diperbarui.")
                return redirect("kalkulator:ongkos_ubah", pk=quotation.pk)
        return render(
            request,
            "kalkulator/ongkos_form.html",
            _cetak_context(
                data, plat_raw, lipat_raw, errors, plat_errors, lipat_errors,
                edit=quotation, form_action=form_action,
                pelanggan=quotation.pelanggan, telepon=quotation.telepon,
                judul_buku=quotation.judul_buku,
            ),
            status=400,
        )

    snapshot = dict(quotation.input_snapshot)
    plat_raw, lipat_raw = _baris_dari_snapshot(snapshot)
    raw = {key: snapshot.get(key, "") for key in CETAK_DEFAULTS}
    raw["plat_rows"] = plat_raw
    raw["lipat_rows"] = lipat_raw
    data, errors, plat_raw, lipat_raw, plat_errors, lipat_errors = _parse_cetak(raw)
    return render(
        request,
        "kalkulator/ongkos_form.html",
        _cetak_context(
            data, plat_raw, lipat_raw, errors, plat_errors, lipat_errors,
            edit=quotation, form_action=form_action,
            pelanggan=quotation.pelanggan, telepon=quotation.telepon,
            judul_buku=quotation.judul_buku,
            tampilkan_hasil=not errors,
        ),
    )


@require_POST
def ongkos_hapus(request, pk):
    quotation = get_object_or_404(PrintingQuotation, pk=pk)
    nomor = quotation.nomor
    quotation.delete()
    messages.success(request, f"{nomor} dihapus.")
    return redirect("kalkulator:ongkos_list")


def ongkos_cetak_cust(request, pk):
    quotation = get_object_or_404(PrintingQuotation, pk=pk)
    return render(
        request,
        "kalkulator/ongkos_cetak_cust.html",
        {"q": quotation, "hasil": _normalisasi_hasil(quotation.hasil_snapshot)},
    )


def ongkos_cetak(request, pk):
    quotation = get_object_or_404(PrintingQuotation, pk=pk)
    return render(
        request,
        "kalkulator/ongkos_cetak.html",
        {"q": quotation, "hasil": _normalisasi_hasil(quotation.hasil_snapshot)},
    )


@require_POST
def api_ongkos(request):
    try:
        payload = json.loads(request.body or "{}")
    except ValueError:
        return JsonResponse({"errors": {"__all__": ["Payload JSON tidak valid."]}}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"errors": {"__all__": ["Payload harus objek JSON."]}}, status=400)

    data, errors, plat_raw, lipat_raw, plat_errors, lipat_errors = _parse_cetak(payload)
    if errors:
        return JsonResponse({"errors": errors}, status=400)

    hasil = hitung_cetak(data)
    ringkasan = render_to_string("kalkulator/_ongkos_ringkasan.html", {"hasil": hasil}, request=request)
    rincian = render_to_string("kalkulator/_ongkos_rincian.html", {"hasil": hasil}, request=request)
    provided = {key for key, value in payload.items() if not isinstance(value, list) and str(value).strip() != ""}
    partial = any(key not in provided for key in CETAK_NUMERIC_KEYS)
    return JsonResponse({"ringkasan": ringkasan, "rincian": rincian, "partial": partial})


def dashboard(request):
    return render(
        request,
        "kalkulator/dashboard.html",
        {"quotations": Quotation.objects.all()[:20]},
    )


def hitung_view(request):
    if request.method == "POST":
        data, errors = clean_input(request.POST)
        if not errors:
            hasil = hitung(_angka_nol(data))
            if hasil["diskon"] > hasil["total"]:
                errors["diskon"] = "Diskon melebihi total penawaran."
            else:
                quotation = _simpan(data, hasil, request)
                messages.success(request, f"{quotation.nomor} tersimpan.")
                return redirect("kalkulator:ubah", pk=quotation.pk)
        return render(request, "kalkulator/form.html", _form_context(data, errors), status=400)

    data = {key: "" for key in DEFAULTS}
    data["pembulatan"] = PEMBULATAN_DEFAULT
    preset = None
    if request.GET.get("preset"):
        preset = get_object_or_404(RatePreset, pk=request.GET["preset"])
        data.update(
            {key: value for key, value in preset.data.items() if key in data}
        )
    return render(
        request, "kalkulator/form.html", _form_context(data, preset=preset, tampilkan_hasil=True)
    )


def ubah(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    form_action = reverse("kalkulator:ubah", args=[quotation.pk])
    if request.method == "POST":
        data, errors = clean_input(request.POST)
        if not errors:
            hasil = hitung(_angka_nol(data))
            if hasil["diskon"] > hasil["total"]:
                errors["diskon"] = "Diskon melebihi total penawaran."
            else:
                _simpan(data, hasil, request, quotation=quotation)
                messages.success(request, f"{quotation.nomor} diperbarui.")
                return redirect("kalkulator:ubah", pk=quotation.pk)
        return render(
            request,
            "kalkulator/form.html",
            _form_context(
                data, errors, edit_nomor=quotation.nomor, edit_pk=quotation.pk, form_action=form_action,
                pelanggan=quotation.pelanggan, telepon=quotation.telepon,
                judul_buku=quotation.judul_buku,
            ),
            status=400,
        )

    data = {key: "" for key in DEFAULTS}
    data.update({key: value for key, value in quotation.input_snapshot.items() if key in data})
    for prefix in ("isi", "cover"):
        key = f"plano_{prefix}"
        if not data.get(key):
            data[key] = _plano_lama(quotation.input_snapshot, prefix)
    data["pembulatan"] = quotation.input_snapshot.get("pembulatan", PEMBULATAN_DEFAULT)
    return render(
        request,
        "kalkulator/form.html",
        _form_context(
            data, edit_nomor=quotation.nomor, edit_pk=quotation.pk, form_action=form_action,
            pelanggan=quotation.pelanggan, telepon=quotation.telepon,
            judul_buku=quotation.judul_buku,
            tampilkan_hasil=True,
        ),
    )


@require_POST
def hapus(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    nomor = quotation.nomor
    quotation.delete()
    messages.success(request, f"{nomor} dihapus.")
    return redirect("kalkulator:dashboard")


def detail(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    return render(request, "kalkulator/detail.html", {"q": quotation, "hasil": quotation.hasil_snapshot})


def cetak(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    return render(request, "kalkulator/cetak.html", {"q": quotation, "hasil": quotation.hasil_snapshot})


def cetak_cust(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    hasil = quotation.hasil_snapshot
    ada_diskon = Decimal(str(hasil.get("diskon", "0"))) > 0
    return render(
        request,
        "kalkulator/cetak_cust.html",
        {
            "q": quotation,
            "hasil": hasil,
            "ada_diskon": ada_diskon,
            "harga_unit_cust": hasil.get("harga_unit_setelah_diskon_final" if ada_diskon else "harga_unit_final"),
            "total_cust": hasil.get("total_setelah_diskon" if ada_diskon else "total"),
        },
    )


def duplikat(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    data = dict(DEFAULTS)
    data.update({key: value for key, value in quotation.input_snapshot.items() if key in data})
    for prefix in ("isi", "cover"):
        lama = _plano_lama(quotation.input_snapshot, prefix)
        if lama:
            data[f"plano_{prefix}"] = lama
    return render(
        request,
        "kalkulator/form.html",
        _form_context(data, asal_nomor=quotation.nomor, telepon=quotation.telepon, tampilkan_hasil=True),
    )


def preset_list(request):
    return render(request, "kalkulator/preset_list.html", {"presets": RatePreset.objects.all()})


@require_POST
def preset_baru(request):
    return _simpan_preset(request, None)


@require_POST
def preset_ubah(request, pk):
    return _simpan_preset(request, get_object_or_404(RatePreset, pk=pk))


def _simpan_preset(request, preset):
    nama = (request.POST.get("nama_preset") or "").strip()
    data, errors = clean_input(request.POST)
    if not nama:
        errors["nama_preset"] = "Nama preset wajib diisi."
    if errors:
        return render(
            request,
            "kalkulator/form.html",
            _form_context(data, errors, preset=preset),
            status=400,
        )
    if preset is None:
        preset = RatePreset()
    preset.nama = nama
    preset.data = _jsonable(data)
    preset.save()
    messages.success(request, f"Preset '{nama}' tersimpan.")
    return redirect("kalkulator:preset_list")


def preset_form(request, pk):
    preset = get_object_or_404(RatePreset, pk=pk)
    data = dict(DEFAULTS)
    data.update({key: value for key, value in preset.data.items() if key in data})
    return render(
        request,
        "kalkulator/form.html",
        _form_context(data, preset=preset, tampilkan_hasil=True),
    )


@require_POST
def preset_hapus(request, pk):
    preset = get_object_or_404(RatePreset, pk=pk)
    preset.delete()
    messages.success(request, "Preset dihapus.")
    return redirect("kalkulator:preset_list")


class PaperGradeForm(forms.ModelForm):
    class Meta:
        model = PaperGrade
        fields = ["nama", "panjang_cm", "lebar_cm", "gramasi", "harga_per_kg", "aktif"]
        widgets = {"aktif": forms.CheckboxInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "aktif":
                field.widget.attrs["class"] = "form-control"


def kertas_list(request):
    return render(request, "kalkulator/kertas_list.html", {"kertas": PaperGrade.objects.all()})


def kertas_form(request, pk=None):
    instance = get_object_or_404(PaperGrade, pk=pk) if pk else None
    form = PaperGradeForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Data kertas tersimpan.")
        return redirect("kalkulator:kertas_list")
    return render(request, "kalkulator/kertas_form.html", {"form": form, "obj": instance})


@require_POST
def kertas_hapus(request, pk):
    get_object_or_404(PaperGrade, pk=pk).delete()
    messages.success(request, "Data kertas dihapus.")
    return redirect("kalkulator:kertas_list")


@require_POST
def api_hitung(request):
    try:
        payload = json.loads(request.body or "{}")
    except ValueError:
        return JsonResponse({"errors": {"__all__": ["Payload JSON tidak valid."]}}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"errors": {"__all__": ["Payload harus objek JSON."]}}, status=400)

    data, errors = clean_input(payload)
    provided = {key for key, value in payload.items() if str(value).strip() != ""}
    # Pratinjau: field kosong = 0; field terisi tetap divalidasi.
    if not errors:
        hasil = hitung(_angka_nol(data))
    if errors:
        return JsonResponse({"errors": errors}, status=400)
    ringkasan = render_to_string("kalkulator/_ringkasan.html", {"hasil": hasil}, request=request)
    rincian = render_to_string("kalkulator/_rincian.html", {"hasil": hasil}, request=request)
    partial = any(key not in provided for key in NUMERIC_KEYS | PLANO_KEYS)
    return JsonResponse({"ringkasan": ringkasan, "rincian": rincian, "partial": partial})
