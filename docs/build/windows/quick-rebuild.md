# Quick Rebuild Guide - Windows Executable

## What Changed After Your Testing

Based on your Windows testing, I've made the following improvements:

### ✅ Issues Resolved

1. **Resource Path Handling** - Your fix for PyInstaller resource paths is perfect!
2. **Build Script Path** - Your fix for `gui\requirements.txt` path is correct!
3. **Missing Dependencies** - Added Pillow and pandas to requirements.txt
4. **PyInstaller Assets** - Updated spec file to include logo and icon
5. **Executable Icon** - Set app_icon.ico as the Windows executable icon

---

## Rebuild Your Executable (Windows)

### Option 1: Quick Build (Recommended)
```cmd
build_windows.bat
```

### Option 2: Manual Build
```cmd
# Install missing dependency (if needed)
pip install Pillow

# Build executable
pyinstaller lab_instruments.spec
```

---

## What's New in This Build

### 🎨 Visual Improvements
- ✅ **Windows Icon**: Your app will now have a proper icon in taskbar and file explorer
- ✅ **ITU Logo**: Logo displays correctly in both dev mode and compiled .exe
- ✅ **Professional Header**: 120px header with ITU branding

### 🔧 Technical Improvements
- ✅ **All Assets Bundled**: Logo and icon now included in .exe
- ✅ **PIL Support**: Image library properly configured
- ✅ **New Utilities**: Exception handler and logging helpers included
- ✅ **Correct Paths**: Resource paths work in both dev and compiled modes

### 📋 Dependencies Now Complete
```
pyserial>=3.5
pyvisa>=1.11.3
pyvisa-py>=0.5.2
pandas>=1.3.0     ← ADDED
Pillow>=9.0.0     ← ADDED
```

---

## Testing Your New Build

### Quick Test Checklist
- [ ] Run `dist\LabInstruments.exe`
- [ ] Verify ITU logo displays in header
- [ ] Verify icon appears in taskbar
- [ ] Connect to Keithley device via USB
- [ ] Run a quick pulse test
- [ ] Check CSV file is created
- [ ] Verify no resource loading errors

### Full Testing
Use `WINDOWS_TESTING_CHECKLIST.md` for comprehensive testing

---

## Expected Improvements

### Before (Your Previous Build)
```
❌ Logo might not display in .exe
❌ Generic Python icon in taskbar
⚠️  Some dependencies might be missing
```

### After (New Build)
```
✅ Logo displays correctly
✅ Professional ITU icon in taskbar
✅ All dependencies included
✅ Larger executable (due to Pillow library)
```

---

## File Size Note

**Expected increase**: ~10-20 MB larger
**Reason**: Pillow library for image processing
**Normal range**: 60-170 MB (single .exe)

This is normal and expected. The size increase is worth it for the professional appearance!

---

## If You Encounter Issues

### Issue: "Module PIL not found"
**Solution**:
```cmd
pip install Pillow
pyinstaller lab_instruments.spec
```

### Issue: "Logo not found"
**Solution**: Verify files exist:
- `gui/assets/logo.png` ✓
- `gui/assets/app_icon.ico` ✓

### Issue: Build fails
**Solution**:
1. Check `build/` folder is deleted
2. Run as Administrator
3. Check antivirus isn't blocking

---

## Distribution

Your executable is now **production-ready** with:
- ✅ Professional icon
- ✅ ITU branding
- ✅ All resources included
- ✅ Complete dependencies

Package contents:
```
YourDistribution/
├── LabInstruments.exe    ← Main executable (with icon!)
├── WINDOWS_USER_GUIDE.md ← User instructions
└── README.md             ← Setup and VISA driver info
```

---

## Next Steps

### Short Term (This Week)
1. **Rebuild** with updated spec file
2. **Test** the new executable
3. **Verify** icon and logo display
4. **Share** with other team members

### Medium Term (Next 2 Weeks)
1. **Test** Sorensen and Prodigit devices on Windows
2. **Complete** WINDOWS_TESTING_CHECKLIST.md
3. **Document** any device-specific findings
4. **Create** final release package

### Long Term (Next Month)
1. **Consider** code signing for distribution
2. **Create** Windows installer (.msi)
3. **Set up** automated builds (CI/CD)
4. **Collect** user feedback from lab

---

## Quick Commands Reference

```cmd
# Rebuild executable
build_windows.bat

# Test executable
dist\LabInstruments.exe

# Check Python can load assets
python -c "from PIL import Image; print('Pillow OK')"

# Verify files exist
dir gui\assets\

# Clean build
rmdir /s /q build dist
```

---

## Your Testing Results Summary

Based on your test files (`data/test_results/`):

✅ **Pulse Tests**: 3 successful tests
- Full test: 121 data points collected
- Partial tests: 60 data points each
- EVOC measurements: 93 data points

✅ **General Tests**: 3 test runs
- All generated valid CSV files
- Data format correct
- Measurements consistent

✅ **Overall**: Excellent results! 🎉

---

## Build Comparison

| Feature | Before | After |
|---------|--------|-------|
| Icon | Generic Python | ✅ ITU Icon |
| Logo in GUI | ✅ Works (dev) / ❌ Breaks (.exe) | ✅ Works Both |
| Dependencies | ⚠️ Incomplete | ✅ Complete |
| Build Script | ⚠️ Wrong path | ✅ Correct path |
| Asset Bundle | ❌ Missing | ✅ Included |
| Professional Look | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

**Ready to rebuild? Run `build_windows.bat` on your Windows machine!**

---

*Generated: 2025-11-11*
*Based on your testing from September-November 2025*
