# Building Windows Executable - Lab Instruments GUI

This guide explains how to build a standalone Windows executable (.exe) from the Lab Instruments GUI application.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Build (Windows)](#quick-build-windows)
- [Manual Build Process](#manual-build-process)
- [Build Configurations](#build-configurations)
- [Troubleshooting](#troubleshooting)
- [Distribution](#distribution)

---

## Prerequisites

### Required Software
1. **Python 3.8 or higher**
   - Download: https://www.python.org/downloads/
   - During installation: Check "Add Python to PATH"
   - Verify: `python --version`

2. **PyInstaller**
   - Install: `pip install pyinstaller`
   - Verify: `pyinstaller --version`

3. **Application Dependencies**
   - Install: `pip install -r requirements.txt`
   - Includes: pyvisa, pyserial, pandas, tkinter

### Build Environment
- **OS**: Windows 10 or Windows 11
- **Disk Space**: ~500 MB for build process
- **RAM**: 4 GB minimum, 8 GB recommended

---

## Quick Build (Windows)

### Using the Build Script

The easiest way to build is using the provided batch script:

```cmd
build_windows.bat
```

This script will:
1. Check Python installation
2. Install PyInstaller if needed
3. Install dependencies
4. Clean previous builds
5. Build the executable
6. Report results

**Output**: `dist/LabInstruments.exe`

---

## Manual Build Process

### Step 1: Prepare Environment

```cmd
# Open Command Prompt or PowerShell

# Navigate to project directory
cd C:\path\to\lab_instruments

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 2: Install Dependencies

```cmd
# Install PyInstaller
pip install pyinstaller

# Install application dependencies
pip install -r requirements.txt

# Verify installations
python -c "import pyvisa; import serial; import pandas; print('Dependencies OK')"
```

### Step 3: Build Executable

```cmd
# Clean previous builds (if any)
rmdir /s /q build dist

# Build using spec file
pyinstaller lab_instruments.spec

# Wait for build to complete (may take 2-5 minutes)
```

### Step 4: Verify Build

```cmd
# Check if executable exists
dir dist\LabInstruments.exe

# Check file size (should be 50-150 MB)
# Test run
dist\LabInstruments.exe
```

---

## Build Configurations

The build is controlled by `lab_instruments.spec`. You can modify the following settings:

### Configuration Options

#### 1. Console Window

**With Console** (Default - Recommended for testing):
```python
console=True
```
- Shows command line window
- Displays error messages and logs
- Easier debugging

**Without Console** (For distribution):
```python
console=False
```
- No console window
- Professional appearance
- Errors only in log files

#### 2. Distribution Type

**Single File** (Default):
```python
# In EXE section:
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # Included
    a.zipfiles,  # Included
    a.datas,     # Included
    ...
)
```
- Everything in one .exe file
- Slower first launch (~5-10 seconds)
- Easier distribution
- Larger file size

**Directory Distribution** (Alternative):
```python
# In EXE section - change to:
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    ...
)

# Uncomment COLLECT section at bottom
coll = COLLECT(...)
```
- Multiple files in a folder
- Faster startup
- Slightly smaller total size
- Must distribute entire folder

#### 3. Compression

**UPX Compression** (Default - enabled):
```python
upx=True
```
- Smaller executable size
- Slightly slower startup

**No Compression**:
```python
upx=False
```
- Larger file size
- Faster startup
- More compatible

### Modifying the Spec File

Edit `lab_instruments.spec`:
1. Open in text editor
2. Find the EXE section
3. Modify `console=` parameter
4. Save and rebuild: `pyinstaller lab_instruments.spec`

---

## Troubleshooting

### Common Build Issues

#### Issue: "Python not found"
```
'python' is not recognized as an internal or external command
```

**Solution**:
1. Reinstall Python with "Add to PATH" checked
2. Or manually add Python to PATH:
   - System Properties → Environment Variables
   - Add `C:\Python3X\` and `C:\Python3X\Scripts\` to PATH

#### Issue: "Module not found"
```
ModuleNotFoundError: No module named 'pyvisa'
```

**Solution**:
```cmd
pip install -r requirements.txt
```

#### Issue: Build fails with permission error
```
PermissionError: [WinError 32] The process cannot access the file...
```

**Solution**:
1. Close any running instances of the app
2. Delete build and dist folders manually
3. Run Command Prompt as Administrator
4. Rebuild

#### Issue: Antivirus blocks PyInstaller
```
Access denied / File quarantined
```

**Solution**:
1. Add PyInstaller to antivirus exceptions
2. Temporarily disable antivirus during build
3. Add project folder to exclusions
4. Use `upx=False` in spec file (UPX can trigger false positives)

#### Issue: ImportError in built executable
```
Executable runs but crashes with ImportError
```

**Solution**:
1. Add missing module to `hidden_imports` in spec file:
```python
hidden_imports = [
    # ...existing imports...
    'missing_module_name',
]
```
2. Rebuild: `pyinstaller lab_instruments.spec`

#### Issue: Executable too large (>200 MB)
**Solution**:
1. Check if unnecessary packages are included
2. Add to `excludes` in spec file:
```python
excludes=[
    'matplotlib',  # If not used
    'scipy',       # If not used
    ...
]
```
3. Use directory distribution instead of single file
4. Enable UPX compression: `upx=True`

### Testing Built Executable

#### On Build Machine
```cmd
# Test from dist folder
cd dist
LabInstruments.exe

# Check for errors
# Test device connections
# Verify all features work
```

#### On Clean Test Machine
1. **Set up clean Windows VM or separate PC**
2. **Do NOT install Python** (testing standalone)
3. **Copy** `dist/LabInstruments.exe` to test machine
4. **Install VISA drivers**:
   - NI-VISA: https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html
5. **Run executable**
6. **Test all features** using WINDOWS_TESTING_CHECKLIST.md

---

## Distribution

### Creating Distribution Package

#### Option 1: Simple Distribution
```
lab_instruments_v1.0_windows.zip
├── LabInstruments.exe
├── README_WINDOWS.txt
└── VISA_DRIVER_INSTALL.txt
```

#### Option 2: Complete Distribution
```
lab_instruments_v1.0_windows.zip
├── LabInstruments.exe
├── README.md
├── WINDOWS_USER_GUIDE.md
├── LICENSE.txt
├── example_profiles/
│   └── sample_profile.csv
└── drivers/
    └── visa_driver_links.txt
```

### Distribution Checklist
- [ ] Executable tested on clean Windows system
- [ ] README includes VISA driver installation
- [ ] Version number in filename
- [ ] License file included
- [ ] Example files included (if needed)
- [ ] User guide included
- [ ] Antivirus tested (executable not flagged)

### File Naming Convention
```
lab_instruments_v{VERSION}_windows_{ARCH}.zip

Examples:
- lab_instruments_v1.0.0_windows_x64.zip
- lab_instruments_v1.1.0_windows_x86.zip
```

### Distribution Notes for Users

**Include in README**:
```
IMPORTANT: This executable REQUIRES NI-VISA or Keysight IO Libraries
to communicate with USB and GPIB devices.

Installation:
1. Install NI-VISA from:
   https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html

2. Run LabInstruments.exe

3. If Windows Defender or antivirus flags the file:
   - This is a false positive (common with PyInstaller)
   - Add exception in antivirus settings
   - Or scan with VirusTotal for verification

4. For Ethernet connections:
   - Allow through Windows Firewall when prompted
   - Or manually add firewall rule

Troubleshooting:
- Check log files in ./logs/ directory
- Refer to WINDOWS_USER_GUIDE.md
- Report issues on GitHub
```

---

## Build Validation

### Pre-Distribution Checklist

- [ ] Builds without errors
- [ ] Executable runs on build machine
- [ ] Executable runs on clean Windows 10
- [ ] Executable runs on clean Windows 11
- [ ] All device types connect successfully
- [ ] All features work (pulse test, current profile, etc.)
- [ ] Log files created correctly
- [ ] CSV exports work
- [ ] No crashes during extended use
- [ ] File size reasonable (<200 MB single file)
- [ ] Antivirus doesn't flag as malware
- [ ] Windows Firewall allows network connections
- [ ] Error messages are user-friendly
- [ ] Documentation is complete and accurate

---

## Advanced Topics

### Custom Icon

To add a custom icon to the executable:

1. Create or obtain an `.ico` file (256x256 recommended)
2. Save as `gui/icons/app_icon.ico`
3. Modify spec file:
```python
exe = EXE(
    ...
    icon='gui/icons/app_icon.ico',
    ...
)
```
4. Rebuild

### Version Information

To add Windows version info (visible in file properties):

1. Create `version_info.txt`:
```python
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    ...
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'Your Company'),
        StringStruct('FileDescription', 'Lab Instruments Control'),
        StringStruct('FileVersion', '1.0.0.0'),
        StringStruct('ProductName', 'Lab Instruments'),
        StringStruct('ProductVersion', '1.0.0.0')])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
```

2. Generate resource file:
```cmd
pyi-set_version version_info.txt dist\LabInstruments.exe
```

### Code Signing

For production distribution, consider code signing:

1. Obtain code signing certificate
2. Sign executable:
```cmd
signtool sign /f certificate.pfx /p password /t http://timestamp.server dist\LabInstruments.exe
```
3. Verify signature:
```cmd
signtool verify /pa dist\LabInstruments.exe
```

---

## Support

### Build Issues
- Check PyInstaller documentation: https://pyinstaller.org/
- Review spec file comments
- Check build logs in `build/` directory

### Runtime Issues
- Check application logs in `./logs/`
- Enable console mode for debugging
- Test on clean system to rule out environment issues

---

**End of Build Instructions**
