# Modular Laboratory Instruments GUI

A modular, extensible GUI application for controlling multiple laboratory instruments including:
- Sorensen SGX400-12 D Power Supply
- Keithley 2281S Battery Simulator/Emulator
- Prodigit 34205A Electronic Load

## Architecture

This modular design provides better maintainability, testability, and extensibility compared to monolithic approaches.

### Directory Structure

```
GUI_modular/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── interfaces/               # Communication interfaces
│   ├── __init__.py
│   ├── base_interface.py     # Abstract interface base class
│   ├── serial_interface.py   # RS232 communication
│   ├── ethernet_interface.py # TCP/IP communication
│   └── visa_interface.py     # USB/GPIB via PyVISA
├── controllers/              # Device-specific controllers
│   ├── __init__.py
│   ├── base_controller.py    # Abstract controller base class
│   ├── sorensen_controller.py
│   ├── keithley_controller.py
│   └── prodigit_controller.py
├── models/                   # Data models and configuration
│   ├── __init__.py
│   └── device_config.py      # Device specs and data structures
├── gui/                      # GUI components
│   ├── __init__.py
│   ├── main_window.py        # Main application window
│   ├── connection_widget.py  # Reusable connection interface
│   ├── device_tab.py         # Generic device tab base
│   ├── sorensen_tab.py       # Sorensen-specific controls
│   ├── keithley_tab.py       # Keithley-specific controls
│   ├── prodigit_tab.py       # Prodigit-specific controls
│   └── monitoring_tab.py     # Data logging and monitoring
└── utils/                    # Utility modules
    ├── __init__.py
    └── data_logger.py        # Data collection and CSV export
```

## Key Features

### Modular Design Benefits

1. **Separation of Concerns**: Each component has a single responsibility
2. **Code Reusability**: Common functionality is abstracted and shared
3. **Easy Testing**: Business logic is separated from GUI
4. **Extensibility**: Adding new devices requires minimal changes
5. **Maintainability**: Clear structure makes bugs easier to find and fix

### Device Support

- **Multiple Interface Types**: RS232, Ethernet, USB, GPIB
- **Automatic Resource Detection**: VISA resource scanning
- **Device-Specific Features**: Specialized controls for each device
- **Battery Pulse Testing**: Advanced Keithley 2281S test sequences

### Data Management

- **Real-time Monitoring**: Configurable sample intervals
- **CSV Export**: Compatible with Excel, MATLAB, Python pandas
- **Thread-safe Logging**: Non-blocking data collection
- **Multiple Device Coordination**: Synchronized measurements

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Optional: Install VISA Runtime** (for USB/GPIB):
   - **Windows**: Download NI-VISA Runtime from National Instruments
   - **Linux**: `sudo apt-get install libusb-1.0-0-dev`
   - **macOS**: `brew install libusb`

## Usage

### Running the Application

```bash
python main.py
```

### Adding New Devices

To add support for a new device:

1. **Create Device Specification** in `models/device_config.py`:
   ```python
   NEW_DEVICE: DeviceSpec(
       name="New Device Name",
       device_type=DeviceType.NEW_DEVICE,
       max_voltage=100.0,
       max_current=10.0,
       supported_interfaces=[InterfaceType.RS232, InterfaceType.ETHERNET],
       default_commands={
           'identify': '*IDN?',
           'measure_voltage': 'MEAS:VOLT?',
           # ... other commands
       }
   )
   ```

2. **Create Controller** in `controllers/new_device_controller.py`:
   ```python
   class NewDeviceController(BaseDeviceController):
       def __init__(self, interface):
           super().__init__(interface, DEVICE_SPECS[DeviceType.NEW_DEVICE])
           
       def measure_voltage(self):
           # Device-specific implementation
           pass
   ```

3. **Create GUI Tab** in `gui/new_device_tab.py`:
   ```python
   class NewDeviceTab(DeviceTab):
       def __init__(self, parent):
           super().__init__(parent, DEVICE_SPECS[DeviceType.NEW_DEVICE], NewDeviceController)
           
       def create_controls(self):
           # Device-specific GUI controls
           pass
   ```

4. **Register in Main Window** in `gui/main_window.py`:
   ```python
   self.device_tabs['new_device'] = NewDeviceTab(self.notebook)
   self.notebook.add(self.device_tabs['new_device'].frame, text="New Device")
   ```

### Configuration Examples

**Serial Connection**:
- Port: /dev/ttyUSB0 (Linux) or COM3 (Windows)
- Baud Rate: Device-specific (9600 for Sorensen, 115200 for Prodigit)

**Ethernet Connection**:
- Sorensen: 192.168.0.200:9221
- Keithley: 192.168.1.100:5025
- Prodigit: 192.168.1.101:4001

**VISA Connection**:
- USB: `USB0::0x05E6::0x2281S::4587429::0::INSTR`
- GPIB: `GPIB0::5::INSTR`

## Testing

The modular design allows for easy unit testing:

```python
# Example test for Sorensen controller
def test_sorensen_voltage_setting():
    mock_interface = MockInterface()
    controller = SorensenController(mock_interface)
    controller.connected = True
    
    controller.set_voltage(12.5)
    
    assert mock_interface.last_command == "SOUR:VOLT 12.5"
```

## Error Handling

- **Connection Errors**: Detailed error messages with troubleshooting hints
- **Command Errors**: Device-specific error handling and recovery
- **GUI Protection**: Safe execution with user feedback
- **Thread Safety**: Protected data access in monitoring system

## Performance

- **Non-blocking GUI**: Monitoring runs in separate thread
- **Efficient Updates**: Only updates changed values
- **Memory Management**: Automatic cleanup and resource disposal
- **Scalable Architecture**: Supports multiple devices without performance degradation

## Troubleshooting

1. **PyVISA Issues**: Check VISA driver installation
2. **Serial Port Access**: Verify user permissions on Linux/macOS
3. **Network Connection**: Check firewall settings for Ethernet devices
4. **Device Communication**: Use connection widget's "Detect" button

## Comparison with Original

| Feature | Original GUI | Modular GUI |
|---------|-------------|-------------|
| Lines of Code | 1300+ in single file | ~200 per module |
| Code Duplication | High | Minimal |
| Testability | Difficult | Easy |
| Adding Devices | Major refactoring | ~100 lines |
| Maintainability | Poor | Excellent |
| Error Isolation | System-wide failures | Component-level |

## License

This software is provided as-is for educational and testing purposes.