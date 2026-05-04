#!/bin/bash
# Script to create Windows distribution ZIP archive
# Excludes unnecessary files and directories

echo "=========================================="
echo "Creating Windows Distribution ZIP"
echo "=========================================="
echo ""

# Navigate to parent directory
cd /home/seymenalper/seymen_projects

# Remove old archive if exists
if [ -f "lab_instruments_windows.tar.gz" ]; then
    echo "Removing old archive..."
    rm lab_instruments_windows.tar.gz
fi

echo "Creating archive with exclusions..."
echo "This may take a moment..."
echo ""

# Create tar.gz archive with all exclusions
tar -czf lab_instruments_windows.tar.gz \
    --exclude='lab_instruments/myenv' \
    --exclude='lab_instruments/__pycache__' \
    --exclude='lab_instruments/**/__pycache__' \
    --exclude='lab_instruments/build' \
    --exclude='lab_instruments/dist' \
    --exclude='lab_instruments/logs' \
    --exclude='lab_instruments/data' \
    --exclude='lab_instruments/archive' \
    --exclude='lab_instruments/instruments' \
    --exclude='lab_instruments/testBeforeGui' \
    --exclude='lab_instruments/.git' \
    --exclude='lab_instruments/docs/manuals/*.pdf' \
    --exclude='lab_instruments/.claude' \
    --exclude='lab_instruments/create_windows_zip.sh' \
    --exclude='lab_instruments/gui/examples/*.xlsx' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='Thumbs.db' \
    --exclude='lab_instruments/.vscode' \
    --exclude='lab_instruments/.idea' \
    --exclude='lab_instruments/.cursor' \
    --exclude='lab_instruments/CODEBASE_AUDIT_REPORT.md' \
    --exclude='lab_instruments/RISK_ANALYSIS.md' \
    --exclude='lab_instruments/keithley_battery_model_prompt.md' \
    --exclude='lab_instruments/gui/CIHAZ_MANUAL_DENETIM_RAPORU.md' \
    lab_instruments

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "SUCCESS: Archive created!"
    echo "=========================================="
    echo ""
    echo "File: lab_instruments_windows.tar.gz"
    echo "Location: /home/seymenalper/seymen_projects/"
    
    # Get file size
    SIZE=$(du -h lab_instruments_windows.tar.gz | cut -f1)
    echo "Size: $SIZE"
    echo ""
    
    echo "Verifying contents..."
    echo ""
    
    # Verify key files exist
    echo "Checking for required files:"
    tar -tzf lab_instruments_windows.tar.gz | grep -q "lab_instruments/build_windows.bat"
    if [ $? -eq 0 ]; then
        echo "  ✓ build_windows.bat"
    else
        echo "  ✗ build_windows.bat (MISSING!)"
    fi
    
    tar -tzf lab_instruments_windows.tar.gz | grep -q "lab_instruments/lab_instruments.spec"
    if [ $? -eq 0 ]; then
        echo "  ✓ lab_instruments.spec"
    else
        echo "  ✗ lab_instruments.spec (MISSING!)"
    fi
    
    tar -tzf lab_instruments_windows.tar.gz | grep -q "lab_instruments/gui/main.py"
    if [ $? -eq 0 ]; then
        echo "  ✓ gui/main.py"
    else
        echo "  ✗ gui/main.py (MISSING!)"
    fi
    
    tar -tzf lab_instruments_windows.tar.gz | grep -q "lab_instruments/gui/requirements.txt"
    if [ $? -eq 0 ]; then
        echo "  ✓ gui/requirements.txt"
    else
        echo "  ✗ gui/requirements.txt (MISSING!)"
    fi
    
    tar -tzf lab_instruments_windows.tar.gz | grep -q "lab_instruments/gui/controllers/keithley/tests/profile_runner.py"
    if [ $? -eq 0 ]; then
        echo "  ✓ gui/controllers/keithley/tests/ (modular structure)"
    else
        echo "  ✗ gui/controllers/keithley/tests/ (MISSING!)"
    fi
    
    tar -tzf lab_instruments_windows.tar.gz | grep -q "lab_instruments/README.md"
    if [ $? -eq 0 ]; then
        echo "  ✓ README.md"
    else
        echo "  ✗ README.md (MISSING!)"
    fi
    
    echo ""
    echo "Checking exclusions:"
    
    # Verify exclusions
    tar -tzf lab_instruments_windows.tar.gz | grep -q "lab_instruments/myenv"
    if [ $? -ne 0 ]; then
        echo "  ✓ myenv/ excluded"
    else
        echo "  ✗ myenv/ NOT excluded!"
    fi
    
    tar -tzf lab_instruments_windows.tar.gz | grep -q "lab_instruments/build/"
    if [ $? -ne 0 ]; then
        echo "  ✓ build/ excluded"
    else
        echo "  ✗ build/ NOT excluded!"
    fi
    
    tar -tzf lab_instruments_windows.tar.gz | grep -q "lab_instruments/dist"
    if [ $? -ne 0 ]; then
        echo "  ✓ dist/ excluded"
    else
        echo "  ✗ dist/ NOT excluded!"
    fi
    
    echo ""
    echo "=========================================="
    echo "Archive ready for Windows transfer!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Transfer lab_instruments_windows.tar.gz to Windows machine"
    echo "2. Extract using 7-Zip, WinRAR, or tar (if available)"
    echo "3. Run build_windows.bat on Windows"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "ERROR: Archive creation failed!"
    echo "=========================================="
    exit 1
fi

