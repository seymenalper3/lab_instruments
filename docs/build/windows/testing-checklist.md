# Windows Testing Checklist for Lab Instruments GUI

This checklist ensures comprehensive testing of the lab automation application on Windows.

## Pre-Testing Setup

### 1. Windows Environment Setup
- [ ] Windows version verified (Windows 10 or 11 recommended)
- [ ] Python 3.8+ installed and added to PATH
- [ ] Administrator privileges available if needed
- [ ] Internet connection available for driver downloads

### 2. Driver Installation
- [ ] **NI-VISA Driver** installed (for USB/GPIB devices)
  - Download: https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html
  - Verify installation: Run `ni-visa` or check "NI MAX" (Measurement & Automation Explorer)
  - Alternative: Keysight IO Libraries (https://www.keysight.com/us/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html)

- [ ] **USB-to-Serial Drivers** (if using serial devices)
  - Check Device Manager (Win+X → Device Manager)
  - Look under "Ports (COM & LPT)" for device listings
  - Install manufacturer drivers if devices show as "Unknown"

### 3. Python Dependencies
- [ ] Create virtual environment (recommended):
  ```
  python -m venv venv
  venv\Scripts\activate
  ```
- [ ] Install requirements:
  ```
  pip install -r requirements.txt
  ```
- [ ] Verify installations:
  ```
  python -c "import pyvisa; print(pyvisa.__version__)"
  python -c "import serial; print(serial.__version__)"
  python -c "import tkinter; print('Tkinter OK')"
  ```

### 4. Firewall Configuration
- [ ] Open Windows Firewall settings (firewall.cpl)
- [ ] Allow Python through firewall (for Ethernet connections)
- [ ] Note firewall rules for rollback if needed
- [ ] Consider temporarily disabling for initial testing

---

## Device Connection Testing

### Test Matrix Overview
| Device | Connection Type | Status | Notes |
|--------|----------------|--------|-------|
| Keithley 2281S | USB (VISA) | ☐ | Required for pulse tests |
| Keithley 2281S | Ethernet | ☐ | Limited functionality |
| Sorensen SGX400-12 | USB/GPIB (VISA) | ☐ | |
| Sorensen SGX400-12 | Ethernet | ☐ | |
| Prodigit 34205A | RS232 (COM) | ☐ | |
| Prodigit 34205A | USB-VISA (ASRL) | ☐ | |

---

## Keithley 2281S Battery Simulator

### Connection Setup
#### USB Connection (VISA)
- [ ] Device connected via USB cable
- [ ] Device appears in Device Manager
- [ ] Run NI MAX and verify device is listed
- [ ] Note VISA resource string (e.g., `USB0::0x05E6::0x2281::04420926::INSTR`)
- [ ] Launch application and test connection

#### Ethernet Connection
- [ ] Device IP address configured: ______________
- [ ] Device port number noted (typically 5025): ______________
- [ ] Ping test successful: `ping <device_ip>`
- [ ] Firewall allows connection to device port
- [ ] Launch application and test connection

### Functionality Testing - USB Connection

#### Basic Functions
- [ ] Connect to device successfully
- [ ] Read device identification (*IDN?)
- [ ] Set voltage (test: 3.7V)
- [ ] Set current limit (test: 1.0A)
- [ ] Turn output ON
- [ ] Measure voltage and current
- [ ] Turn output OFF
- [ ] Disconnect from device

#### Power Supply Mode
- [ ] Switch to Power Supply mode
- [ ] Set voltage: 4.2V
- [ ] Set current limit: 1.0A
- [ ] Enable output
- [ ] Verify measurements update
- [ ] Disable output

#### Battery Test Mode
- [ ] Switch to Battery Test mode
- [ ] Configure discharge parameters
- [ ] Enable battery output
- [ ] Verify measurements update
- [ ] Disable battery output

#### Pulse Test (USB ONLY)
- [ ] **Prerequisites:** USB connection verified
- [ ] Load pulse test parameters:
  - Pulses: 5
  - Pulse time: 10s (short test)
  - Rest time: 10s
  - Pulse current: 0.5A
- [ ] Execute pulse test
- [ ] Monitor progress in console/GUI
- [ ] Verify CSV files created in `./logs/`
  - pulse_bt_YYYYMMDD_HHMMSS.csv
  - rest_evoc_YYYYMMDD_HHMMSS.csv
- [ ] Open CSV files and verify data format
- [ ] Check for EVOC and ESR values in rest file

#### Current Profile Execution (USB ONLY)
- [ ] **Prerequisites:** USB connection verified
- [ ] Prepare test profile CSV:
  - Create simple profile: 10s charge, 10s discharge
  - File: `current_profile_test.csv`
- [ ] Load profile in application
- [ ] Set parameters:
  - Discharge current: 1.0A
  - Charge voltage: 4.2V
- [ ] Execute profile
- [ ] Monitor mode switching (charge ↔ discharge)
- [ ] Verify log file created: `./logs/keithley_log_YYYYMMDD_HHMMSS.csv`
- [ ] Check measurements in log file

#### Battery Model Generation
- [ ] **Prerequisites:** USB connection preferred
- [ ] **Note:** This test takes several hours - plan accordingly
- [ ] Configure parameters:
  - Discharge voltage: 3.0V
  - Discharge current end: 0.4A
  - Charge full voltage: 4.2V
  - Charge current limit: 1.0A
  - ESR interval: 30s
- [ ] Start battery model test
- [ ] Monitor progress (logged every 30s)
- [ ] Wait for discharge phase completion
- [ ] Wait for charge phase completion
- [ ] Verify model saved to slot
- [ ] Check CSV export: `./battery_models/battery_model_slotX_YYYYMMDD_HHMMSS.csv`
- [ ] Verify model data contains SOC, Voc, ESR values

#### Real-time Monitoring
- [ ] Enable monitoring (if available in GUI)
- [ ] Verify voltage readings update
- [ ] Verify current readings update
- [ ] Verify power calculations
- [ ] Check update frequency (should be smooth)
- [ ] Stop monitoring

### Functionality Testing - Ethernet Connection

#### Basic Functions
- [ ] Connect to device successfully
- [ ] Read device identification (*IDN?)
- [ ] Set voltage (test: 3.7V)
- [ ] Set current limit (test: 1.0A)
- [ ] Turn output ON
- [ ] Measure voltage and current (may have delays)
- [ ] Turn output OFF
- [ ] Disconnect from device

#### Known Limitations
- [ ] Pulse Test: Verify error message is shown (not supported over Ethernet)
- [ ] Current Profile: Verify error message is shown (not supported over Ethernet)
- [ ] Basic measurements: May be slower than USB
- [ ] Buffer data: May not work reliably

---

## Sorensen SGX400-12 Power Supply

### Connection Setup
- [ ] Device connection type: ______________ (USB/GPIB/Ethernet)
- [ ] Resource string or IP: ______________
- [ ] Connection successful

### Functionality Testing
#### Basic Control
- [ ] Read device identification
- [ ] Set voltage: 100V
- [ ] Set current limit: 5A
- [ ] Set OVP (overvoltage protection): 110V
- [ ] Enable output
- [ ] Measure voltage
- [ ] Measure current
- [ ] Disable output

#### Monitoring
- [ ] Enable real-time monitoring
- [ ] Verify voltage updates
- [ ] Verify current updates
- [ ] Stop monitoring

#### Edge Cases
- [ ] Test maximum voltage setting (400V - if safe)
- [ ] Test maximum current setting (12A - if safe)
- [ ] Test rapid on/off cycles
- [ ] Verify OVP triggers correctly (if testable)

---

## Prodigit 34205A Electronic Load

### Connection Setup

#### RS232 Serial Connection
- [ ] Device connected via RS232 cable or USB-to-Serial adapter
- [ ] Check Device Manager for COM port number: COM____
- [ ] Verify COM port settings:
  - Baud rate: 115200
  - Data bits: 8
  - Parity: None
  - Stop bits: 1
- [ ] Connection successful

#### USB-VISA (ASRL) Connection
- [ ] Device connected via USB
- [ ] Check NI MAX for ASRL resource (e.g., ASRL1::INSTR)
- [ ] Resource string noted: ______________
- [ ] Connection successful

### Functionality Testing
#### Basic Control
- [ ] Read device identification
- [ ] Set mode to CC (Constant Current)
- [ ] Set current: 1A
- [ ] Enable load
- [ ] Measure voltage
- [ ] Measure current
- [ ] Measure power
- [ ] Disable load

#### Mode Testing
- [ ] **CC Mode (Constant Current)**
  - Set current: 2A
  - Enable load
  - Verify current measurement
  - Disable load

- [ ] **CV Mode (Constant Voltage)**
  - Set voltage: 12V
  - Enable load
  - Verify voltage measurement
  - Disable load

- [ ] **CP Mode (Constant Power)**
  - Set power: 24W
  - Enable load
  - Verify power measurement
  - Disable load

- [ ] **CR Mode (Constant Resistance)**
  - Set resistance: 10Ω
  - Enable load
  - Verify resistance calculation
  - Disable load

#### Monitoring
- [ ] Enable real-time monitoring
- [ ] Verify all measurements update
- [ ] Stop monitoring

---

## GUI Testing

### Application Launch
- [ ] Launch application: `python gui/main.py`
- [ ] Window opens successfully
- [ ] Window is properly sized and visible
- [ ] All tabs are visible
- [ ] No Python errors in console

### Connection Widget
- [ ] Connection widget loads for each device tab
- [ ] Interface types listed correctly:
  - VISA resources show up (if NI-VISA installed)
  - Serial ports show COM ports
  - Ethernet option available
- [ ] "Scan" button finds devices
- [ ] "Connect" button works
- [ ] "Disconnect" button works
- [ ] Connection status indicator updates correctly

### Device Tabs
- [ ] **Keithley Tab**
  - All controls visible and accessible
  - Voltage/current sliders work
  - Output on/off buttons work
  - Pulse test button available
  - Current profile button available
  - Battery model button available

- [ ] **Sorensen Tab**
  - All controls visible and accessible
  - Voltage/current controls work
  - OVP control works
  - Output control works

- [ ] **Prodigit Tab**
  - All controls visible and accessible
  - Mode selection works
  - Value setting works
  - Load on/off works

### Monitoring Tab
- [ ] Monitoring tab visible
- [ ] Start monitoring works
- [ ] Real-time data updates
- [ ] Graphs update (if implemented)
- [ ] Stop monitoring works
- [ ] Data export works

### Debug Console Tab
- [ ] Debug console tab visible
- [ ] Log messages appear
- [ ] Messages are properly formatted
- [ ] Scrolling works
- [ ] Clear button works (if implemented)
- [ ] Log level filtering works (if implemented)

---

## Data Logging and File Operations

### Log Files
- [ ] `./logs/` directory created automatically
- [ ] Application log file created: `app_YYYYMMDD.log`
- [ ] Log file contains startup information
- [ ] Log file contains Windows platform information
- [ ] Log file readable and properly formatted

### CSV Exports
- [ ] Pulse test CSV files created correctly
- [ ] Current profile log CSV created correctly
- [ ] Battery model CSV created correctly
- [ ] CSV files open in Excel/Calc without errors
- [ ] Data properly formatted (voltage, current, time)
- [ ] UTF-8 encoding correct (no encoding issues)

### Configuration Files
- [ ] Settings file created: `~/.lab_instruments/connection_settings.json`
- [ ] Settings persist between sessions
- [ ] Last connection settings restored on launch

---

## Error Handling and Recovery

### VISA Driver Errors
- [ ] Test without NI-VISA: Verify helpful error message
- [ ] Test with corrupted VISA installation: Verify error guidance
- [ ] Verify error message includes download link

### Serial Port Errors
- [ ] Test with invalid COM port: Verify error message lists available ports
- [ ] Test with port in use: Verify "port in use" error and guidance
- [ ] Test with disconnected device: Verify appropriate error

### Network Errors
- [ ] Test with invalid IP: Verify timeout error and troubleshooting steps
- [ ] Test with firewall blocking: Verify error mentions firewall
- [ ] Test with unreachable device: Verify network troubleshooting guidance

### Application Errors
- [ ] Test graceful shutdown (close window)
- [ ] Test force quit (task manager kill)
- [ ] Test rapid connect/disconnect cycles
- [ ] Verify no crashes or hangs
- [ ] Verify error messages are user-friendly

---

## Performance Testing

### Resource Usage
- [ ] Check Task Manager during idle: CPU __% / Memory __MB
- [ ] Check during monitoring: CPU __% / Memory __MB
- [ ] Check during pulse test: CPU __% / Memory __MB
- [ ] No memory leaks after extended operation (1+ hour)

### Responsiveness
- [ ] GUI remains responsive during operations
- [ ] No freezing or "Not Responding" states
- [ ] Progress indicators update smoothly
- [ ] Long operations can be cancelled (if implemented)

---

## Windows-Specific Issues

### Path Handling
- [ ] Log files created in correct location
- [ ] Settings file created in user home directory
- [ ] CSV exports save to correct location
- [ ] No path errors with spaces in directory names
- [ ] No issues with forward/backslash mixing

### Permissions
- [ ] Application runs without administrator privileges
- [ ] File creation works without admin rights
- [ ] Device access works without admin rights
- [ ] Note if admin rights are required: ______________

### Compatibility
- [ ] Test on Windows 10: Version ______
- [ ] Test on Windows 11: Version ______
- [ ] Test on different display scaling (125%, 150%)
- [ ] Test on multiple monitors
- [ ] Test with different keyboard layouts

---

## Security Software Testing

### Antivirus
- [ ] Test with Windows Defender enabled
- [ ] Test with third-party antivirus: ______________
- [ ] Verify no false positives
- [ ] Application not flagged as malware

### Firewall
- [ ] Test with Windows Firewall enabled
- [ ] Test Ethernet connections with firewall active
- [ ] Add firewall exception if needed
- [ ] Document firewall configuration

---

## Final Checklist

### Documentation
- [ ] All errors encountered documented with screenshots
- [ ] Workarounds noted for any issues
- [ ] Performance metrics recorded
- [ ] Windows version and configuration documented

### Sign-off
- [ ] All critical features tested successfully
- [ ] Known issues documented
- [ ] Testing completed by: ______________
- [ ] Date: ______________
- [ ] Windows Version: ______________
- [ ] Python Version: ______________
- [ ] NI-VISA Version: ______________

---

## Known Issues / Notes

```
Document any issues found during testing:

1. Issue: ___________________________
   Severity: [ ] Critical  [ ] High  [ ] Medium  [ ] Low
   Workaround: ___________________________

2. Issue: ___________________________
   Severity: [ ] Critical  [ ] High  [ ] Medium  [ ] Low
   Workaround: ___________________________

[Add more as needed]
```

---

## Testing Results Summary

### Overall Status
- [ ] All tests passed
- [ ] Minor issues found (documented above)
- [ ] Major issues found (requires attention)
- [ ] Critical issues found (blocks release)

### Recommended Actions
```
List any recommended fixes or improvements:

1. ___________________________
2. ___________________________
3. ___________________________
```

---

**End of Windows Testing Checklist**
