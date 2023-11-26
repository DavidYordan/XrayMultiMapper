# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.__main__ import PyiBlockCipher
import random
import string

def generate_random_key(length=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

block_cipher = PyiBlockCipher(key=generate_random_key())

json_files = collect_data_files('json_model', includes=['*.json'])

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=json_files,
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
