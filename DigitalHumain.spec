# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\saglikturizmi-37635\\Desktop\\Çalışmalar\\Geliştirmeler\\digital-humain\\config\\config.yaml', 'config'), ('C:\\Users\\saglikturizmi-37635\\Desktop\\Çalışmalar\\Geliştirmeler\\digital-humain\\digital_humain', 'digital_humain')],
    hiddenimports=['tiktoken_ext.openai_public', 'tiktoken_ext', 'digital_humain.core', 'digital_humain.vlm', 'digital_humain.agents', 'digital_humain.tools', 'digital_humain.memory', 'digital_humain.orchestration', 'digital_humain.utils'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['streamlit', 'matplotlib', 'IPython'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DigitalHumain',
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
)
