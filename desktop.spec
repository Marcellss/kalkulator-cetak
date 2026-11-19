# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = [("kalkulator/templates", "kalkulator/templates")]
datas += collect_data_files("tzdata")

hiddenimports = collect_submodules("kalkulator") + [
    "django.db.backends.sqlite3",
    "django.core.management.commands.migrate",
]
a = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["reportlab", "PIL", "openpyxl", "MySQLdb", "tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Kalkulator Cetak",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon="assets/app.ico",
    favicon="assets/app.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Kalkulator Cetak",
)
