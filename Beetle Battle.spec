# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['beetle-battle.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    version='version.rc'
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Beetle Battle',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Beetle Battle',
)
app = BUNDLE(
    coll,
    name='Beetle Battle.app',
    icon='icon.icns',
    bundle_identifier='com.computerguided.beetle-battle',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleGetInfoString': 'Beetle Battle',
        'NSHumanReadableCopyright': '© 2023 Computerguided Systems B.V.',
    }
)
