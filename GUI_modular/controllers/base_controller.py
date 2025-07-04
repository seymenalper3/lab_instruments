#!/usr/bin/env python3
"""
Base device controller class
"""
from abc import ABC, abstractmethod
from typing import Optional
from models.device_config import DeviceSpec, MeasurementData
from interfaces.base_interface import DeviceInterface


class BaseDeviceController(ABC):
    """Abstract base class for device controllers"""
    
    def __init__(self, interface: DeviceInterface, device_spec: DeviceSpec):
        self.interface = interface
        self.device_spec = device_spec
        self.model = ""
        self.connected = False
        self.busy = False  # Flag to indicate device is busy with special operations
        
    def connect(self) -> bool:
        """Connect to the device"""
        try:
            self.interface.connect()
            self.connected = True
            self.identify()
            # Set to remote mode if available
            if hasattr(self, 'remote_mode'):
                self.remote_mode()
            return True
        except Exception as e:
            self.connected = False
            raise e
            
    def disconnect(self):
        """Disconnect from the device"""
        try:
            if hasattr(self, 'output_off'):
                self.output_off()
        except:
            pass
        try:
            # Set to local mode if available
            if hasattr(self, 'local_mode'):
                self.local_mode()
        except:
            pass
        self.interface.disconnect()
        self.connected = False
        
    def identify(self):
        """Identify the device"""
        try:
            identify_cmd = self.device_spec.default_commands.get('identify', '*IDN?')
            self.model = self.interface.query(identify_cmd)
        except:
            self.model = "Unknown"
            
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.connected and self.interface.is_connected()
        
    def set_busy(self, busy: bool):
        """Set device busy state"""
        self.busy = busy
        
    def is_busy(self) -> bool:
        """Check if device is busy with special operations"""
        return self.busy
        
    def is_available_for_monitoring(self) -> bool:
        """Check if device is available for monitoring"""
        return self.is_connected() and not self.is_busy()
        
    @abstractmethod
    def measure_voltage(self) -> Optional[float]:
        """Read voltage measurement"""
        pass
        
    @abstractmethod
    def measure_current(self) -> Optional[float]:
        """Read current measurement"""
        pass
        
    def measure_power(self) -> Optional[float]:
        """Read power measurement (if supported)"""
        return None
        
    def get_measurements(self) -> MeasurementData:
        """Get all measurements as structured data"""
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        return MeasurementData(
            timestamp=timestamp,
            voltage=self.measure_voltage(),
            current=self.measure_current(),
            power=self.measure_power()
        )
        
    def send_command(self, command: str):
        """Send command to device"""
        if not self.connected:
            raise Exception("Device not connected")
        self.interface.write(command)
        
    def query_command(self, command: str) -> str:
        """Send command and get response"""
        if not self.connected:
            raise Exception("Device not connected")
        return self.interface.query(command)