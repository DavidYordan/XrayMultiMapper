# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

current_dir = os.getcwd()

json_files = [(os.path.join(current_dir, 'json_model', '*.json'), 'json_model')]

extra_files = [
    (os.path.join(current_dir, 'v2ray', 'run_v2ray.bat'), 'v2ray'),
    (os.path.join(current_dir, 'xray', 'run_xray.bat'), 'xray'),
]

datas = json_files + extra_files

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='V2XrayMultiMapper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='',
    icon='img/logo.ico',
)
