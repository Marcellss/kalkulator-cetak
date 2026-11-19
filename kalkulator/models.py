from django.db import models


class PaperGrade(models.Model):
    nama = models.CharField(max_length=120)
    panjang_cm = models.DecimalField(max_digits=10, decimal_places=2, default=65)
    lebar_cm = models.DecimalField(max_digits=10, decimal_places=2, default=90)
    gramasi = models.DecimalField(max_digits=10, decimal_places=2, default=80)
    harga_per_kg = models.DecimalField(max_digits=18, decimal_places=2, default=19000)
    aktif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nama"]

    def __str__(self):
        return f"{self.nama} {self.gramasi} gsm"


class RatePreset(models.Model):
    nama = models.CharField(max_length=150, unique=True)
    data = models.JSONField(default=dict)
    is_default = models.BooleanField(default=False)
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nama"]

    def __str__(self):
        return self.nama


class Quotation(models.Model):
    nomor = models.CharField(max_length=30, unique=True)
    pelanggan = models.CharField(max_length=150, blank=True)
    telepon = models.CharField(max_length=50, blank=True)
    judul_buku = models.CharField(max_length=200, blank=True)
    ukuran_buku = models.CharField(max_length=100, blank=True)
    bahan_isi = models.CharField(max_length=100, blank=True)
    bahan_cover = models.CharField(max_length=100, blank=True)
    oplah = models.PositiveIntegerField()
    margin_persen = models.DecimalField(max_digits=8, decimal_places=4)
    diskon = models.DecimalField(max_digits=18, decimal_places=2)
    subtotal = models.DecimalField(max_digits=18, decimal_places=2)
    nilai_margin = models.DecimalField(max_digits=18, decimal_places=2)
    total = models.DecimalField(max_digits=18, decimal_places=2)
    harga_unit = models.DecimalField(max_digits=18, decimal_places=4)
    total_setelah_diskon = models.DecimalField(max_digits=18, decimal_places=2)
    harga_unit_setelah_diskon = models.DecimalField(max_digits=18, decimal_places=4)
    input_snapshot = models.JSONField()
    hasil_snapshot = models.JSONField()
    dibuat_oleh = models.CharField(max_length=150, blank=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-dibuat_pada"]

    def __str__(self):
        return self.nomor


class PrintingQuotation(models.Model):
    nomor = models.CharField(max_length=30, unique=True)
    pelanggan = models.CharField(max_length=150, blank=True)
    telepon = models.CharField(max_length=50, blank=True)
    judul_buku = models.CharField(max_length=200, blank=True)
    oplah = models.PositiveIntegerField()
    margin_persen = models.DecimalField(max_digits=8, decimal_places=4)
    diskon = models.DecimalField(max_digits=18, decimal_places=2)
    subtotal = models.DecimalField(max_digits=18, decimal_places=2)
    nilai_margin = models.DecimalField(max_digits=18, decimal_places=2)
    total = models.DecimalField(max_digits=18, decimal_places=2)
    harga_unit = models.DecimalField(max_digits=18, decimal_places=4)
    total_setelah_diskon = models.DecimalField(max_digits=18, decimal_places=2)
    harga_unit_setelah_diskon = models.DecimalField(max_digits=18, decimal_places=4)
    input_snapshot = models.JSONField()
    hasil_snapshot = models.JSONField()
    dibuat_oleh = models.CharField(max_length=150, blank=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-dibuat_pada"]

    def __str__(self):
        return self.nomor
