@echo off
REM Build script for Lab Instruments GUI - Windows Executable
REM This script builds a standalone .exe using PyInstaller

echo ========================================
echo Lab Instruments GUI - Windows Build
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

echo [1/6] Checking Python version...
python --version

REM Check if PyInstaller is installed
echo.
echo [2/6] Checking PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing...
    python -m pip install pyinstaller
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
) else (
    echo PyInstaller is already installed
)

REM Check dependencies
echo.
echo [3/6] Checking dependencies...
python -c "import pyvisa; import serial; import pandas; import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo Some dependencies are missing. Installing from requirements.txt...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo All dependencies are installed
)

REM Clean previous builds
echo.
echo [4/6] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo Clean complete

REM Build the executable
echo.
echo [5/6] Building executable...
echo This may take several minutes...
pyinstaller lab_instruments.spec
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed
    echo Check the output above for errors
    pause
    exit /b 1
)

echo.
echo [6/6] Build complete!
echo.

REM Check if executable was created
if exist dist\LabInstruments.exe (
    echo ========================================
    echo SUCCESS: Executable created successfully
    echo ========================================
    echo.
    echo Location: dist\LabInstruments.exe
    echo.

    REM Get file size
    for %%A in (dist\LabInstruments.exe) do (
        echo File size: %%~zA bytes
        set /a sizeMB=%%~zA/1024/1024
    )
    echo File size: %sizeMB% MB (approx)
    echo.

    echo Next steps:
    echo 1. Test the executable: dist\LabInstruments.exe
    echo 2. Ensure VISA drivers are installed on target system
    echo 3. Review WINDOWS_TESTING_CHECKLIST.md for testing
    echo 4. Create distribution package with README
    echo.

    REM Ask if user wants to run the executable
    choice /C YN /M "Do you want to run the executable now for testing"
    if %errorlevel% equ 1 (
        echo.
        echo Launching executable...
        start dist\LabInstruments.exe
    )
) else (
    echo ========================================
    echo ERROR: Executable not found
    echo ========================================
    echo Build completed but executable was not created.
    echo Check build logs above for errors.
)

echo.
pause
