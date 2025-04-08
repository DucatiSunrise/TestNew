# PacketInjector.spec
# -*- mode: python ; coding: utf-8 -*-
import pathlib
from PyInstaller.utils.hooks import collect_submodules

project_root = str(pathlib.Path().resolve())

block_cipher = None

# ✅ Collect all Scapy submodules to avoid runtime import errors
hiddenimports = collect_submodules('scapy')

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        ('scapy_cache/*', 'scapy_cache'),  # ✅ Ensure this folder exists at runtime
        ('icon.ico', '.'),                 # ✅ Optional: include app icon
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='PacketInjectorGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # ✅ No console window popup
    icon='icon.ico',         # ✅ Optional app icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='PacketInjectorGUI'
)
