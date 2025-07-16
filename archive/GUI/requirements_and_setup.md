# Multi-Device Test GUI - Setup Guide

## Overview
This GUI application allows you to connect to and test three devices:
- **Sorensen SGX400-12 D** Power Supply (RS232, Ethernet, GPIB)
- **Keithley 2281S** Battery Simulator/Emulator (USB, Ethernet, GPIB)  
- **Prodigit 34205A** Electronic Load (RS232, Ethernet, USB, GPIB)

## System Requirements
- **Python 3.6 or later**
- **Operating System**: Windows, Linux, or macOS
- **Hardware**: Devices connected via supported interfaces

## Installation

### 1. Install Python Dependencies

Create a `requirements.txt` file:

```text
pyserial>=3.5
pyvisa>=1.11.3
pyvisa-py>=0.5.2
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Optional: Install VISA Runtime

For **USB and GPIB** communication, you may need to install VISA runtime:

#### Windows:
- Download and install **NI-VISA Runtime** from National Instruments
- Alternatively, use **pyvisa-py** (pure Python backend, included in requirements)

#### Linux:
```bash
# For Ubuntu/Debian
sudo apt-get install libusb-1.0-0-dev

# Alternative: Install linux-gpib for GPIB support
sudo apt-get install linux-gpib-dev
```

#### macOS:
```bash
# Install using Homebrew
brew install libusb
```

## Device-Specific Setup

### Sorensen SGX400-12 D
- **RS232**: Configure baud rate on front panel (default: 9600)
- **Ethernet**: Configure IP address (default: 192.168.0.200, port 9221)
- **GPIB**: Set GPIB address on front panel (default: varies)

### Keithley 2281S
- **USB**: Install Keithley drivers if needed
- **Ethernet**: Configure LAN settings (default port: 5025)
- **GPIB**: Set GPIB address (default: 5)

### Prodigit 34205A
- **RS232**: Set baud rate (recommended: 115200)
- **Ethernet**: Configure network settings (default port: 4001)
- **USB**: Install USB-to-Serial drivers
- **GPIB**: Set GPIB address

## Running the Application

1. **Save the GUI code** as `device_test_gui.py`

2. **Run the application**:
```bash
python device_test_gui.py
```

3. **Connect your devices**:
   - Select appropriate interface for each device
   - Configure connection parameters
   - Click "Connect" for each device

## Usage Guide

### Connection Setup
1. **Select Interface Type**: Choose RS232, Ethernet, USB, or GPIB
2. **Configure Parameters**: 
   - RS232: Select COM port and baud rate
   - Ethernet: Enter IP address and port
   - USB/GPIB: Enter VISA resource string or use "Detect"
3. **Connect**: Click Connect button for each device

### Device Control
- **Sorensen SGX400-12**: Set voltage, current limit, and OVP; control output
- **Keithley 2281S**: Set voltage/current, select function mode, control output
- **Prodigit 34205A**: Set load mode (CC/CV/CP/CR) and value, control load

### Monitoring & Logging
- **Start Monitoring**: Begin real-time data collection
- **Set Sample Interval**: Configure measurement frequency
- **Save Data**: Export measurements to CSV file
- **Clear Data**: Reset monitoring display

## Troubleshooting

### Common Issues

1. **"PyVISA not available"**
   - Install PyVISA: `pip install pyvisa pyvisa-py`
   - USB/GPIB functionality will be limited without PyVISA

2. **Serial port not found**
   - Check device connections
   - Verify COM port assignments (Windows Device Manager)
   - Install appropriate USB-to-Serial drivers

3. **Ethernet connection failed**
   - Verify device IP addresses and network settings
   - Check firewall settings
   - Ensure devices are on same network segment

4. **VISA resource not found**
   - Use "Detect" button to find available resources
   - Install proper device drivers
   - Check GPIB/USB connections

### Device-Specific Issues

**Sorensen SGX400-12**:
- Set rear panel switch to "Remote" position
- Verify Ethernet configuration via front panel or web interface

**Keithley 2281S**:
- Check USB drivers installation
- Verify VISA resource string format: `USB0::0x05E6::0x2281S::[serial]::INSTR`

**Prodigit 34205A**:
- Ensure proper RS232 handshaking (RTS/CTS enabled)
- Check network configuration for Ethernet connection

## Advanced Features

### Custom Scripts Integration
You can integrate your existing Python scripts by:
1. Adding custom test sequences
2. Implementing automated test procedures
3. Creating device-specific measurement functions

### Data Export
- CSV files include timestamps and all device measurements
- Compatible with Excel, MATLAB, Python pandas
- Real-time plotting can be added using matplotlib

### Multi-Device Coordination
- Synchronize operations across devices
- Implement power supply + load testing scenarios
- Create battery charge/discharge cycles

## File Structure
```
project/
├── device_test_gui.py          # Main GUI application
├── requirements.txt            # Python dependencies
├── README.md                   # This setup guide
└── data/                       # Exported measurement data
    ├── monitoring_YYYYMMDD_HHMMSS.csv
    └── ...
```

## Support

For additional support:
1. Check device manuals for communication protocols
2. Verify PyVISA installation: `python -c "import pyvisa; print(pyvisa.__version__)"`
3. Test device connections using simple scripts first
4. Review manufacturer software/drivers

## License
This software is provided as-is for educational and testing purposes.
