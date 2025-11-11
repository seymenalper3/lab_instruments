# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Lab Instruments GUI Application
Builds a standalone Windows executable with all dependencies

Usage:
    pyinstaller lab_instruments.spec

Options:
    - To build without console window: Set console=False in EXE section
    - To create directory distribution instead of single file: Set onefile=False
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path

block_cipher = None

# Determine if we're on Windows
is_windows = sys.platform.startswith('win')

# Application metadata
app_name = 'LabInstruments'
version = '1.0.0'
description = 'Laboratory Instrument Control and Automation GUI'
author = 'Seymen Alper'

# Hidden imports - modules that PyInstaller might miss
hidden_imports = [
    # Core dependencies
    'pyvisa',
    'pyvisa_py',
    'serial',
    'serial.tools',
    'serial.tools.list_ports',

    # GUI framework
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',

    # Data processing
    'pandas',
    'numpy',  # pandas dependency

    # Image processing (for logo display)
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',

    # Standard library that might be missed
    'queue',
    'threading',
    'socket',
    'pathlib',
    'csv',
    'json',
    'logging',
    'logging.handlers',
    'datetime',
    'time',
    'platform',
    'locale',

    # Application modules
    'interfaces',
    'interfaces.base_interface',
    'interfaces.serial_interface',
    'interfaces.ethernet_interface',
    'interfaces.visa_interface',

    'controllers',
    'controllers.base_controller',
    'controllers.keithley_controller',
    'controllers.sorensen_controller',
    'controllers.prodigit_controller',

    'models',
    'models.device_config',

    'gui',
    'gui.main_window',
    'gui.device_tab',
    'gui.keithley_tab',
    'gui.sorensen_tab',
    'gui.prodigit_tab',
    'gui.connection_widget',
    'gui.monitoring_tab',
    'gui.debug_console_tab',

    'utils',
    'utils.app_logger',
    'utils.data_logger',
    'utils.keithley_logger',
    'utils.exception_handler',
    'utils.logging_migration_helper',
]

# Collect all pyvisa backends
hidden_imports += collect_submodules('pyvisa')
hidden_imports += collect_submodules('pyvisa_py')

# Data files to include (if any)
# Format: (source, destination_in_exe)
datas = []

# Add logo and icon assets
datas += [
    ('gui/assets/logo.png', 'gui/assets'),
    ('gui/assets/app_icon.ico', 'gui/assets'),
]

# If you have config files, add them here:
# datas += [('config/*.json', 'config')]

# Analysis - scan the entry point and dependencies
a = Analysis(
    ['gui/main.py'],  # Entry point
    pathex=['.'],  # Search path for imports
    binaries=[],  # No additional binaries needed
    datas=datas,  # Data files to include
    hiddenimports=hidden_imports,  # Modules to force include
    hookspath=[],  # Custom hooks directory
    hooksconfig={},
    runtime_hooks=[],  # Runtime hook scripts
    excludes=[
        # Exclude unnecessary packages to reduce size
        'matplotlib',  # Unless you're using it
        'scipy',       # Unless you're using it
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
        'pytest',
        'setuptools',
        'pip',
        'wheel',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ - Create compressed archive of Python modules
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# EXE - Create the executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,  # Set to True for debugging
    bootloader_ignore_signals=False,
    strip=False,  # Don't strip symbols (Windows doesn't benefit much)
    upx=True,  # Compress with UPX (set to False if you encounter issues)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False to hide console window (use True for debugging)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

    # Windows-specific options
    icon='gui/assets/app_icon.ico',  # Application icon for Windows executable
    version_file=None,  # Can generate a version file for Windows properties
    uac_admin=False,  # Don't require administrator privileges
    uac_uiaccess=False,
)

# COLLECT - For directory distribution (only if onefile=False above)
# Uncomment this section if you want a directory distribution instead of a single .exe
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name=app_name,
# )

# Build configuration notes:
"""
BUILD CONFIGURATIONS:

1. Single executable with console (for testing):
   - console=True, onefile=True (current setting)
   - Best for testing and debugging
   - Users can see error messages and logs
   - File size: ~50-100 MB (depends on dependencies)

2. Single executable without console (for distribution):
   - console=False, onefile=True
   - Professional appearance
   - No console window
   - Users should check log files for errors

3. Directory distribution (faster startup):
   - Uncomment COLLECT section above
   - Remove: a.binaries, a.zipfiles, a.datas from EXE
   - Add: exclude_binaries=True in EXE
   - Faster startup time
   - Multiple files in a directory

WINDOWS-SPECIFIC NOTES:

1. VISA Driver Requirement:
   - The executable STILL requires NI-VISA or Keysight IO Libraries
   - These cannot be bundled due to licensing and driver complexity
   - Include installation instructions in documentation

2. Antivirus False Positives:
   - PyInstaller executables may trigger antivirus warnings
   - This is normal and not a security issue
   - Users may need to add exception in antivirus software

3. File Size:
   - Single file .exe will be 50-150 MB depending on dependencies
   - This is normal for Python applications with scientific libraries
   - Consider directory distribution if size is a concern

4. First Launch:
   - First launch is slower (~5-10 seconds) as files are unpacked
   - Subsequent launches are faster
   - Directory distribution starts faster

5. Testing:
   - Test on clean Windows system without Python installed
   - Test with Windows Defender enabled
   - Test with different Windows versions (10, 11)
   - Verify all device connections work

BUILD COMMAND:
   pyinstaller lab_instruments.spec

OUTPUT:
   dist/LabInstruments.exe (or dist/LabInstruments/ directory)

DISTRIBUTION:
   Distribute the entire dist/ folder contents
   Include README and documentation
   Include VISA driver installation instructions
"""
