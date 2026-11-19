"""Entry point aplikasi desktop (PyInstaller)."""

import os
import secrets
import socket
import sys
import threading
import traceback
import webbrowser
from pathlib import Path

APP_NAME = "Kalkulator Cetak"


def data_dir():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def siapkan_frozen():
    """Mode exe: konfigurasi eksplisit, tanpa file .env."""
    folder = data_dir()
    secret_file = folder / "secret.key"
    if not secret_file.exists():
        secret_file.write_text(secrets.token_urlsafe(64), encoding="utf-8")
    os.environ.setdefault("DJANGO_SECRET_KEY", secret_file.read_text(encoding="utf-8").strip())
    os.environ.setdefault("DJANGO_DEBUG", "0")
    os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")
    os.environ.setdefault("DJANGO_CSRF_TRUSTED_ORIGINS", "")
    os.environ.setdefault("DB_PATH", str(folder / "calculator-cetak.sqlite3"))
    return folder


def arahkan_log(folder):
    if sys.stdout is None or sys.stderr is None:
        log = open(folder / "app.log", "a", buffering=1, encoding="utf-8")
        sys.stdout = sys.stderr = log


def port_bebas():
    for port in range(8000, 8010):
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    frozen = bool(getattr(sys, "frozen", False))
    folder = siapkan_frozen() if frozen else None
    if frozen:
        arahkan_log(folder)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from waitress import serve

    django.setup()

    call_command("migrate", interactive=False, verbosity=0)

    from kalkulator.models import RatePreset

    if not RatePreset.objects.exists():
        call_command("seed", verbosity=0)

    port = port_bebas()
    url = f"http://127.0.0.1:{port}/"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"{APP_NAME} berjalan di {url} - tekan Ctrl+C untuk berhenti.", flush=True)

    try:
        serve(get_wsgi_application(), host="127.0.0.1", port=port, threads=4)
    except KeyboardInterrupt:
        print("Aplikasi berhenti.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        lokasi = data_dir() if getattr(sys, "frozen", False) else Path.cwd()
        try:
            with open(lokasi / "startup-error.log", "a", encoding="utf-8") as log:
                traceback.print_exc(file=log)
        finally:
            traceback.print_exc()
        raise
