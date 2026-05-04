# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Lab Instruments GUI
# Build: pyinstaller lab_instruments.spec  (run from project root)

block_cipher = None

a = Analysis(
    ['gui/main.py'],
    pathex=['.', 'gui'],
    binaries=[],
    datas=[
        ('gui/assets', 'assets'),
    ],
    hiddenimports=[
        'pyvisa',
        'pyvisa_py',
        'pyvisa.resources',
        'pyvisa.resources.serial',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'pandas',
        'openpyxl',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'jupyter', 'notebook', 'IPython'],
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
    name='LabInstruments',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No console window on launch
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='gui/assets/app_icon.ico',
)
