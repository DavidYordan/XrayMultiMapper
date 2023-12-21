# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

current_dir = os.getcwd()

datas = [
    (os.path.join(current_dir, 'json_model', '*.json'), 'json_model'),
    (os.path.join(current_dir, 'v2ray', 'v2ray.exe'), 'v2ray'),
    (os.path.join(current_dir, 'xray', 'xray.exe'), 'xray'),
    (os.path.join(current_dir, 'img', '*.ico'), 'img'),
    (os.path.join(current_dir, 'dist', 'V2XrayMultiMapper.exe'), 'dist'),
]

a = Analysis(
    ['bootstrap.py'],
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
    name='V2XrayResourceExtractor',
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
    icon='img/V2XrayResourceExtractor.ico',
)
