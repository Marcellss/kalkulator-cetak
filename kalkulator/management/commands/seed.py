from decimal import Decimal

from django.core.management.base import BaseCommand

from kalkulator.fields import DEFAULTS
from kalkulator.models import PaperGrade, RatePreset


class Command(BaseCommand):
    help = "Seed preset tarif default dari spesifikasi bagian 5."

    def handle(self, *args, **options):
        data = {
            key: (format(value, "f") if isinstance(value, Decimal) else value)
            for key, value in DEFAULTS.items()
        }
        data["pembulatan"] = "none"
        preset, created = RatePreset.objects.update_or_create(
            nama="Default Excel", defaults={"data": data, "is_default": True}
        )
        status = "Dibuat" if created else "Diperbarui"
        self.stdout.write(self.style.SUCCESS(f"{status}: preset '{preset.nama}'"))

        for nama, gramasi in (("Kertas isi 80 gsm", 80), ("Kertas cover 230 gsm", 230)):
            PaperGrade.objects.get_or_create(
                nama=nama,
                defaults={
                    "panjang_cm": Decimal("65"),
                    "lebar_cm": Decimal("90"),
                    "gramasi": Decimal(str(gramasi)),
                    "harga_per_kg": Decimal("19000"),
                },
            )
        self.stdout.write(self.style.SUCCESS("Seed master kertas selesai."))
