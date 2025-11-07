# Lab Instruments GUI - Windows User Guide

Complete guide for installing and using the Lab Instruments Control GUI on Windows.

## Table of Contents
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [First Time Setup](#first-time-setup)
- [Connecting Devices](#connecting-devices)
- [Using the Application](#using-the-application)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10 (64-bit) or Windows 11
- **RAM**: 4 GB
- **Disk Space**: 500 MB free
- **Display**: 1280x800 or higher
- **USB Ports**: Available for device connections

### Recommended Requirements
- **Operating System**: Windows 11 (latest updates)
- **RAM**: 8 GB or more
- **Disk Space**: 2 GB free
- **Display**: 1920x1080 or higher
- **Network**: Ethernet port for network-connected devices

### Required Drivers
- **NI-VISA** (National Instruments VISA) or **Keysight IO Libraries**
  - Required for USB and GPIB device communication
  - Download links provided in installation section

---

## Installation

### Option 1: Standalone Executable (Recommended for Most Users)

If you received a `LabInstruments.exe` file:

1. **Extract files** (if in ZIP archive)
   ```
   Right-click ZIP file → Extract All
   ```

2. **Install NI-VISA Driver** (REQUIRED)
   - Download: https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html
   - Run installer
   - Accept license agreement
   - Choose "Typical" installation
   - Restart computer when prompted

3. **Run the Application**
   - Double-click `LabInstruments.exe`
   - Windows may show security warning (this is normal)
   - Click "More info" → "Run anyway"

### Option 2: Python Installation (For Developers)

If you have the source code:

1. **Install Python 3.8+**
   - Download: https://www.python.org/downloads/
   - During installation: **CHECK "Add Python to PATH"**
   - Verify: Open Command Prompt, type `python --version`

2. **Install NI-VISA** (same as above)

3. **Install Dependencies**
   ```cmd
   cd path\to\lab_instruments
   pip install -r requirements.txt
   ```

4. **Run Application**
   ```cmd
   python gui\main.py
   ```

---

## First Time Setup

### 1. Windows Firewall Configuration

If using Ethernet-connected devices:

1. When first running, Windows may show firewall dialog
2. Check **both** "Private networks" and "Public networks"
3. Click "Allow access"

**Manual Configuration** (if needed):
1. Press `Win + R`, type `firewall.cpl`, press Enter
2. Click "Allow an app or feature through Windows Firewall"
3. Click "Change settings"
4. Find "Python" or "LabInstruments" in the list
5. Check boxes for Private and Public
6. Click OK

### 2. Verify VISA Installation

1. Press `Win + R`, type `ni-max`, press Enter
2. NI Measurement & Automation Explorer should open
3. Expand "Devices and Interfaces"
4. You should see connected USB/GPIB devices listed

**If NI-MAX doesn't open**:
- VISA driver not installed correctly
- Reinstall NI-VISA
- Restart computer

### 3. Check COM Ports (for Serial Devices)

1. Press `Win + X`, select "Device Manager"
2. Expand "Ports (COM & LPT)"
3. Note COM port numbers (e.g., COM3, COM4)
4. If devices show "Unknown" or with yellow warning:
   - Right-click → Update driver
   - Let Windows search automatically

---

## Connecting Devices

The application supports three types of connections:

### USB Connection (VISA)

**Best for**: Keithley, Sorensen (when available)

**Setup**:
1. Connect device via USB cable
2. Wait for Windows to recognize device
3. Open application
4. In device tab, select "VISA" interface
5. Click "Scan" to detect device
6. Select device from dropdown
7. Click "Connect"

**Resource String Format**:
```
USB0::0x05E6::0x2281::SERIAL::INSTR
```

**Troubleshooting**:
- Device not found? Check Device Manager
- Install manufacturer's USB driver if needed
- Try different USB port
- Restart computer

### Ethernet Connection

**Best for**: Remote operation, multiple devices

**Setup**:
1. Ensure device is on same network as PC
2. Note device IP address (from device menu)
3. Open application
4. In device tab, select "Ethernet" interface
5. Enter IP address (e.g., `192.168.1.100`)
6. Enter port (usually `5025` for SCPI devices)
7. Click "Connect"

**Limitations for Keithley 2281S**:
- ⚠️ Pulse tests: NOT supported over Ethernet
- ⚠️ Current profiles: NOT supported over Ethernet
- ✅ Basic measurements: Supported (with delays)
- ✅ Manual control: Fully supported

**Troubleshooting**:
- Cannot connect? Ping device: `ping 192.168.1.100`
- Check firewall settings
- Verify device IP in instrument menu
- Ensure device has remote interface enabled

### Serial (RS232) Connection

**Best for**: Prodigit electronic load

**Setup**:
1. Connect device via RS232 cable or USB-to-Serial adapter
2. Note COM port from Device Manager
3. Open application
4. In device tab, select "Serial" interface
5. Select COM port (e.g., COM3)
6. Set baud rate: `115200`
7. Click "Connect"

**Troubleshooting**:
- Port in use? Close other applications using the port
- Wrong COM port? Check Device Manager
- Driver issue? Update USB-to-Serial driver

---

## Using the Application

### Main Window

The application has multiple tabs:

```
┌─────────────────────────────────────────┐
│  Keithley | Sorensen | Prodigit | More  │
├─────────────────────────────────────────┤
│                                         │
│  [Connection Widget]                    │
│  [Device Controls]                      │
│  [Measurements Display]                 │
│                                         │
└─────────────────────────────────────────┘
```

### Device Tabs

Each device has its own tab with specific controls.

---

## Keithley 2281S Battery Simulator

### Basic Operation

**Connecting**:
1. Go to "Keithley" tab
2. Select connection type (USB recommended)
3. Click "Scan" → Select device → "Connect"
4. Status should show "Connected"

**Power Supply Mode**:
```
Use for charging operations
```
1. Click "Power Supply Mode" button
2. Set voltage: Use slider or enter value (e.g., `4.2V`)
3. Set current limit: (e.g., `1.0A`)
4. Click "Output ON"
5. Monitor voltage and current in real-time
6. Click "Output OFF" when done

**Battery Test Mode**:
```
Use for discharge operations
```
1. Click "Battery Test Mode" button
2. Set discharge current: (e.g., `1.0A`)
3. Set end voltage: (e.g., `3.0V`)
4. Click "Output ON"
5. Monitor discharge progress
6. Output turns off automatically at end voltage

### Advanced Features

#### Pulse Test

**Purpose**: Measure battery ESR and EVOC characteristics

**Requirements**:
- ✅ USB connection (REQUIRED)
- ⚠️ Ethernet NOT supported

**Steps**:
1. Connect via USB
2. Click "Pulse Test" button
3. Configure parameters:
   - Number of pulses: `5`
   - Pulse duration: `60` seconds
   - Rest duration: `60` seconds
   - Pulse current: `1.0A`
4. Click "Start"
5. Wait for test to complete (may take several minutes)
6. Results saved to `logs/pulse_bt_YYYYMMDD_HHMMSS.csv`

**Output Files**:
- `pulse_bt_*.csv`: Voltage, current, time during pulses
- `rest_evoc_*.csv`: EVOC, ESR measurements during rest

**Viewing Results**:
- Open CSV files in Excel or spreadsheet software
- Plot voltage vs time to visualize discharge curves
- Use ESR data for battery health analysis

#### Current Profile Execution

**Purpose**: Run automated charge/discharge cycles

**Requirements**:
- ✅ USB connection (REQUIRED)
- ⚠️ Ethernet NOT supported
- CSV profile file with `time_s` and `current_a` columns

**Creating a Profile**:

Create `my_profile.csv`:
```csv
time_s,current_a
0,0.5
10,1.0
20,-0.5
30,-1.0
40,0
```
- Positive current = charge
- Negative current = discharge
- Time in seconds

**Running Profile**:
1. Connect via USB
2. Click "Current Profile" button
3. Select profile CSV file
4. Set parameters:
   - Discharge current: `1.0A`
   - Charge voltage: `4.2V`
5. Click "Start"
6. Monitor progress in console
7. Log saved to `logs/keithley_log_YYYYMMDD_HHMMSS.csv`

**During Execution**:
- Application shows current step
- Mode switches automatically (charge ↔ discharge)
- Progress logged to file
- Can take several minutes to hours depending on profile

#### Battery Model Generation

**Purpose**: Full battery characterization with ESR mapping

**Requirements**:
- ✅ USB connection recommended
- ⏱️ Time: 2-6 hours (depends on battery capacity)
- Fully charged battery

**Steps**:
1. Connect via USB
2. Click "Battery Model" button
3. Configure parameters:
   - Discharge end voltage: `3.0V`
   - Discharge end current: `0.4A`
   - Charge voltage: `4.2V`
   - Charge current limit: `1.0A`
   - ESR interval: `30s`
   - Model slot: `4`
4. Click "Start"
5. **Wait for discharge phase** (may take hours)
6. **Wait for charge phase** (may take hours)
7. Model saved to device slot
8. CSV exported to `battery_models/battery_model_slot4_*.csv`

**During Test**:
- Progress logged every 30 seconds
- Console shows voltage, current, phase
- Do NOT disconnect or close application
- Can monitor in real-time

**After Completion**:
- Model stored in device memory
- CSV file contains SOC, Voc, ESR data
- Use for simulation or analysis

---

## Sorensen SGX400-12 Power Supply

### Basic Operation

**Connecting**:
1. Go to "Sorensen" tab
2. Select connection (USB/GPIB/Ethernet)
3. Connect

**Setting Output**:
1. Set voltage: `100V`
2. Set current limit: `5A`
3. Set OVP (overvoltage protection): `110V`
4. Click "Output ON"
5. Monitor measurements
6. Click "Output OFF"

**Safety**:
- ⚠️ High voltage capable (up to 400V)
- Always set OVP
- Start with low voltage for testing
- Ensure load can handle voltage/current

---

## Prodigit 34205A Electronic Load

### Basic Operation

**Connecting**:
1. Go to "Prodigit" tab
2. Select connection (Serial or USB-VISA)
3. For Serial: Select COM port, set baud to `115200`
4. Connect

**Operating Modes**:

**CC (Constant Current)**:
```
Load draws constant current
```
1. Select "CC" mode
2. Set current: `1.0A`
3. Click "Load ON"
4. Monitor voltage, current, power

**CV (Constant Voltage)**:
```
Load maintains constant voltage
```
1. Select "CV" mode
2. Set voltage: `12V`
3. Click "Load ON"

**CP (Constant Power)**:
```
Load draws constant power
```
1. Select "CP" mode
2. Set power: `24W`
3. Click "Load ON"

**CR (Constant Resistance)**:
```
Load acts as constant resistance
```
1. Select "CR" mode
2. Set resistance: `10Ω`
3. Click "Load ON"

---

## Troubleshooting

### Connection Issues

#### "VISA driver not found"

**Windows Solution**:
1. Install NI-VISA: https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html
2. Restart computer
3. Verify with NI-MAX (Win+R → `ni-max`)

#### "Cannot open COM3"

**Windows Solution**:
1. Open Device Manager (Win+X → Device Manager)
2. Check Ports (COM & LPT)
3. Verify COM port number
4. Close other apps using the port
5. Update USB-to-Serial driver

#### "Connection timeout" (Ethernet)

**Windows Solution**:
1. Ping device: `ping 192.168.1.100`
2. Check Windows Firewall:
   - Win+R → `firewall.cpl`
   - Allow Python/LabInstruments
3. Verify device IP address
4. Check network cable connection

#### "Device not found"

**Windows Solution**:
1. Check Device Manager for device
2. Reinstall device drivers
3. Try different USB port
4. Restart computer

### Application Issues

#### Application won't start

**Windows Solution**:
1. Check log files in `logs/` folder
2. Install missing dependencies (if source install)
3. Run as Administrator
4. Check antivirus (may be blocking)

#### "Pulse test not supported over Ethernet"

**This is expected behavior**:
- Pulse tests REQUIRE USB connection
- Disconnect Ethernet
- Connect via USB
- Retry pulse test

#### Application freezes during long operations

**Normal behavior for**:
- Pulse tests (can take 10-30 minutes)
- Current profiles (can take hours)
- Battery model generation (can take 2-6 hours)

**Check**:
- Look for progress messages in console
- Check if disk activity (writing logs)
- Wait for completion
- Do NOT force close

### Data and Logging Issues

#### Cannot find log files

**Windows Location**:
```
.\logs\
```
- Same folder as executable
- Or where you ran `python gui\main.py`

**Open Location**:
1. In File Explorer, navigate to application folder
2. Look for `logs` folder
3. Log files: `app_YYYYMMDD.log`
4. CSV files: `pulse_bt_*.csv`, etc.

#### CSV files won't open

**Windows Solution**:
1. Install Microsoft Excel or LibreOffice Calc
2. Right-click CSV → Open with → Excel
3. If encoding issues: Open in Notepad first to verify data

---

## FAQ

### General

**Q: Do I need Python installed?**
A: No, if using the standalone .exe. Yes, if running from source.

**Q: Do I need VISA drivers?**
A: Yes, always. NI-VISA or Keysight IO Libraries required for USB/GPIB devices.

**Q: Can I use this on Windows 7?**
A: Not recommended. Windows 10 or 11 required.

**Q: Is internet required?**
A: No, works completely offline after installation.

### Connections

**Q: Can I connect multiple devices at once?**
A: Yes, each device type has its own tab. Connect one per tab.

**Q: USB or Ethernet - which is better?**
A:
- USB: Full functionality, faster, more reliable
- Ethernet: Remote operation, but limited for some Keithley functions

**Q: Why doesn't pulse test work over Ethernet?**
A: Instrument limitation. Buffered data retrieval unreliable over TCP sockets.

### Data and Files

**Q: Where are log files saved?**
A: In `logs/` folder next to the executable.

**Q: Can I change log location?**
A: Currently no, always saves to `./logs/`

**Q: What format are the data files?**
A: CSV (Comma-Separated Values) - open with Excel, Calc, or any spreadsheet.

**Q: How long are logs kept?**
A: Indefinitely. Delete old logs manually if needed.

### Errors and Issues

**Q: Windows Defender says it's dangerous**
A: False positive. PyInstaller executables often trigger this. Click "More info" → "Run anyway" or add to exclusions.

**Q: Application crashes on startup**
A:
1. Check `logs/app_YYYYMMDD.log` for errors
2. Ensure VISA drivers installed
3. Run as Administrator
4. Check antivirus settings

**Q: I get "Permission denied" errors**
A: Run as Administrator (right-click .exe → Run as administrator)

### Device-Specific

**Q: Can I run battery model test overnight?**
A: Yes, but:
- Don't let computer sleep (disable sleep mode)
- Ensure stable power (use UPS if possible)
- Application must stay open

**Q: How do I know pulse test is working?**
A: Watch console for progress messages. CSV files grow as test runs.

---

## Getting Help

### Check Logs
Application logs are in `logs/` folder:
- `app_YYYYMMDD.log`: General application log
- Includes platform info, errors, device communication

### Report Issues
When reporting problems, include:
1. Windows version (Settings → System → About)
2. Application version
3. Error message (screenshot or copy from log)
4. Steps to reproduce
5. Device type and connection method
6. Log file (if possible)

### Resources
- Project README: Technical details
- Windows Testing Checklist: Comprehensive testing guide
- Build Instructions: For building from source

---

**End of Windows User Guide**

---

## Quick Reference Card

### Essential Windows Shortcuts
- `Win + X`: Quick access menu → Device Manager
- `Win + R`: Run dialog
  - `firewall.cpl`: Firewall settings
  - `devmgmt.msc`: Device Manager
  - `ni-max`: NI VISA Manager

### Common Error Solutions (Quick)

| Error | Quick Fix |
|-------|-----------|
| VISA not found | Install NI-VISA, restart |
| COM port in use | Close other apps, check Device Manager |
| Connection timeout | Check firewall, ping device |
| Device not found | Check USB cable, restart computer |
| Permission denied | Run as Administrator |
| Pulse test not supported | Use USB instead of Ethernet |

### File Locations (Windows)
```
Executable location:        dist\LabInstruments.exe
Logs:                      .\logs\
Settings:                  C:\Users\YourName\.lab_instruments\
Pulse test output:         .\logs\pulse_bt_YYYYMMDD_HHMMSS.csv
Current profile log:       .\logs\keithley_log_YYYYMMDD_HHMMSS.csv
Battery models:            .\battery_models\
```

---

*Last Updated: 2025*
