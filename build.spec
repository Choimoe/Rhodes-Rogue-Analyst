import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None
project_root = os.path.dirname(os.path.abspath(__file__))

datas = []
datas += collect_data_files('src')
datas += [
    (os.path.join(project_root, 'config/app_config.ini'), 'config'),
    (os.path.join(project_root, 'config/ui_theme.json'), 'config')
]

datas += [(os.path.join(project_root, '.env.example'), '.')]

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Rhodes-Rogue-Analyst',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='assets/bunny.ico',
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)