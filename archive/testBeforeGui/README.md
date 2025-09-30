# Prodigit 34205A Electronic Load Controller

Python controller for Prodigit 34205A DC Electronic Load via USB connection.

## Quick Start

1. **Connect device** to USB port (should appear as `/dev/ttyUSB0`)
2. **Run quick test**: `python3 quick_test.py`
3. **Use in your code**: `from prodigit_final import Prodigit34205A`

## Files Overview

### Core Files
- **`prodigit_final.py`** - Main controller class
- **`quick_test.py`** - Fast verification test  
- **`test_suite.py`** - Comprehensive test suite
- **`examples.py`** - Usage examples

### Discovery Files (Reference)
- `discovery.py` - Command discovery script
- `debug_mode.py` - Mode debugging script
- `device_info.py` - Device information test

## Basic Usage

```python
from prodigit_final import Prodigit34205A

# Connect to device
load = Prodigit34205A()

# Set 2A constant current load
load.set_current(2.0)
load.enable()

# Take measurements
voltage, current, power = load.get_measurements()
print(f"V={voltage:.3f}V, I={current:.3f}A, P={power:.3f}W")

# Disable and close
load.disable()
load.close()
```

## Verified Working Commands

Based on extensive testing, these commands are confirmed working:

### Measurements ✅
- `MEAS:VOLT?` - Read voltage
- `MEAS:CURR?` - Read current  
- `MEAS:POW?` - Read power

### Parameter Setting ✅
- `CURR <value>` - Set current
- `VOLT <value>` - Set voltage
- `POW <value>` - Set power
- `RES <value>` - Set resistance

### Control ✅
- `INP ON/OFF` - Enable/disable input
- `LOAD ON/OFF` - Enable/disable load
- `LOAD?` - Query load status

### Status ✅
- `MODE?` - Query current mode
- `ERR?` - Query error code
- `*IDN?` - Device identification

### Mode Control ⚠️
- `MODE CV` - **Only CV mode works reliably**
- Other mode commands have limited functionality

## Connection Settings

- **Port**: `/dev/ttyUSB0` (adjust as needed)
- **Baudrate**: 115200
- **Data bits**: 8
- **Parity**: None
- **Stop bits**: 1
- **Line ending**: `\r\n`
- **Delay**: 0.3s between commands

## Error Codes

- `0` - No error
- `20` - Parameter error (normal without power source)
- `21` - Over voltage
- `22` - Over current
- `23` - Over power
- `24` - Over temperature

## Hardware Setup

1. **USB Driver**: Uses Prolific PL2303 chip (built-in Linux driver)
2. **Permissions**: Add user to `dialout` group or `chmod 666 /dev/ttyUSB0`
3. **Power Source**: Connect power supply to load terminals for real measurements

## Testing Without Power Source

Without connecting a power source, you can still test:
- ✅ Device communication
- ✅ Parameter setting
- ✅ Control functions (enable/disable)
- ✅ Status queries
- ❌ Actual load measurements (will read 0)

## Safety Notes

⚠️ **Always disable load when done**
⚠️ **Check power source ratings**  
⚠️ **Start with low currents for testing**
⚠️ **Monitor device temperature**

## Troubleshooting

**Device not found**:
```bash
ls /dev/ttyUSB*
sudo usermod -a -G dialout $USER
```

**Permission denied**:
```bash
sudo chmod 666 /dev/ttyUSB0
```

**Communication errors**:
- Check USB cable quality
- Verify baudrate (115200)
- Try different USB port

## Next Steps

1. **Test with power source** - Connect battery/PSU for real measurements
2. **Create test profiles** - Automated test sequences
3. **Add data logging** - Save measurements to file
4. **Build GUI** - Graphical interface for easy control
5. **Integration** - Use in larger test systems
