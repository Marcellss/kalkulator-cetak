# Kalkulator Cetak

Aplikasi web internal untuk menghitung harga penawaran cetak buku. Django 5 + SQLite + Bootstrap 5, tanpa SPA framework. Semua perhitungan ada di satu fungsi murni `kalkulator/services/pricing.py::hitung()`.

## Setup

1. Pastikan Python 3.11+ terpasang. Tidak perlu MySQL/Laragon.
2. (Opsional) Buat `.env` untuk mengganti default:

   ```
   DJANGO_SECRET_KEY=...
   DJANGO_DEBUG=1
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
   DB_PATH=calculator-cetak.sqlite3
   ```

   Tanpa `.env`, nilai default di `config/settings.py` dipakai. File database SQLite dibuat otomatis oleh `migrate`.

3. Install dependensi:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Migrasi dan seed data default:

   ```bash
   python manage.py migrate
   python manage.py seed
   ```

5. Jalankan:

   ```bash
   python manage.py runserver
   ```

## Halaman

| URL | Fungsi |
|---|---|
| `/` | Dashboard penawaran terakhir |
| `/hitung/` | Form kalkulator + panel hasil sticky (live preview) |
| `/hitung/<id>/` | Detail penawaran tersimpan (read-only) |
| `/hitung/<id>/cetak/` | Tampilan print-friendly |
| `/hitung/<id>/duplikat/` | Salin input ke form baru |
| `/preset/` | Daftar / pakai / ubah / hapus preset tarif |
| `/kertas/` | CRUD master kertas |
| `/api/hitung/` | `POST` JSON → HTML hasil (live preview) |
| `/hitung/<id>/cetak-cust/` | Tampilan print-friendly untuk customer |
| `/ongkos-cetak/` | Daftar penawaran ongkos cetak saja |
| `/ongkos-cetak/baru/` | Form hitung ongkos cetak (tanpa biaya kertas) |
| `/ongkos-cetak/<id>/ubah/` | Ubah penawaran ongkos cetak |
| `/ongkos-cetak/<id>/cetak/` | Cetak internal (rincian komponen) |
| `/ongkos-cetak/<id>/cetak-cust/` | Cetak penawaran ongkos cetak untuk customer |
| `/api/ongkos-cetak/` | `POST` JSON → HTML hasil ongkos cetak |

## Ongkos cetak saja

Mode ini untuk customer yang menyediakan kertas/bahan sendiri; yang dihitung hanya jasa cetak. Komponen: plat, ongkos cetak, druk, lipat, dan potong. Kertas tidak dihitung.

- Komponen plat bisa lebih dari satu (mis. 4/1 dan 1/1). Tiap komponen punya unit plat, oplah, jumlah plat per keteran, jumlah keteran, pemilik plat, harga plat, dan tarif cetak sendiri.
- `jumlah plat komponen = plat per set × keteran`; total plat adalah jumlah semua komponen.
- Harga plat/ongkos cetak 1/1 (15.000/50.000) dan 2/1 (33.000/75.000) terisi otomatis dan tetap bisa diedit.
- Plat bisa ditandai "Disediakan customer" per komponen sehingga biaya plat komponen itu nol.
- Druk: `Σ((oplah komponen − 1.000) × jumlah plat komponen × tarif druk)`, dengan jumlah plat komponen = plat per set × keteran.
- Oplah penawaran = jumlah seluruh oplah komponen; harga per unit = total penawaran ÷ jumlah oplah tersebut.
- Komponen lipat juga bisa lebih dari satu. Jumlah lembar tiap komponen lipat otomatis diambil dari oplah komponen plat dengan urutan yang sama (lipat 1 ← plat 1), lalu dihitung dengan lipat 1/2/3 dan harga lipat sendiri.
- Ambang 3.000 lembar dipakai global dengan urutan FIFO dari baris pertama; biaya tetap Rp150.000 hanya sekali per penawaran.
- Potong: `berat × harga per kg`.
- Margin dan diskon mengikuti penawaran biasa.

Preset dibuat dari form kalkulator: isi tarif, isi "Nama preset", lalu "Simpan sebagai Preset". Preset menyimpan seluruh field input apa adanya.

## Struktur

```
kalkulator/
  fields.py                 # daftar field input §5 + default, satu sumber kebenaran
  models.py                 # PaperGrade, RatePreset, Quotation
  services/pricing.py       # hitung(input) -> dict, tanpa I/O
  services/validation.py    # validasi form & API
  views.py                  # validasi -> hitung() -> render/simpan
  templates/kalkulator/     # base, form, _hasil (dipakai juga oleh API), detail, cetak
  management/commands/seed.py
  tests.py                  # golden test §10 + alur simpan/API
```

- Uang memakai `Decimal` presisi 28; tidak ada `float` dan tidak ada pembulatan di tengah perhitungan.
- Satu rim selalu 500 lembar (konstanta `RIM` di `services/pricing.py`), tidak diinput dari form.
- Harga unit dibulatkan hanya saat ditampilkan (2 desimal) atau sesuai opsi pembulatan `none`/`up_100`/`up_500`/`up_1000`.
- Setiap penawaran menyimpan `input_snapshot` dan `hasil_snapshot` (JSON), jadi perubahan tarif tidak mengubah penawaran lama.
- Nomor penawaran: `RP-YYYYMMDD-####` (sequence harian).

## Test

```bash
python manage.py test kalkulator
```

Golden test memakai seluruh default §5 dan harus menghasilkan `subtotal = 22.877.523,75`, `total = 29.740.780,875`, `harga_unit = 14.870,3904375`.

## Asumsi — menunggu konfirmasi pemilik

Rumus mengikuti dokumen/Excel apa adanya. Label berikut belum dikonfirmasi:

1. Arti fisik `halaman per lembar = 8` dan `up per plano = 4`.
2. Alasan pengurang 1.000 pada perhitungan druk isi maupun cover.
3. Arti `faktor lipat A = 2` dan `faktor lipat B = 12`.
4. Satuan `jumlah bending = 23`/`tarif = 35` dan `jumlah wrapping = 21`/`tarif = 20`.
5. Apakah harga sudah termasuk PPN (Excel tidak punya baris pajak).
6. Kebijakan pembulatan harga unit yang dipakai saat menawarkan ke pelanggan.
7. Apakah diskon Rp2.000.000 bersifat tetap atau per penawaran.
8. Apakah `DOFF/GLOSSY` dan `SPOT UV/EMBOS/POLY` perlu biaya — belum ada rumusnya, jadi belum dihitung.

Catatan: pada Excel, wrapping memakai tebal bending (`D23`). Aplikasi memakai `wrapping_tebal` (`D24`) dengan default 1, sehingga hasil default identik tetapi logikanya benar.
