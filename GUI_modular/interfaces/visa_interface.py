#!/usr/bin/env python3
"""
VISA communication interface for USB and GPIB
"""
from interfaces.base_interface import DeviceInterface

try:
    import pyvisa
    VISA_AVAILABLE = True
except ImportError:
    VISA_AVAILABLE = False


class VISAInterface(DeviceInterface):
    """VISA communication interface for USB and GPIB"""
    
    def __init__(self, resource_string, timeout=5000):
        super().__init__()
        self.resource_string = resource_string
        self.timeout = timeout
        if not VISA_AVAILABLE:
            raise Exception("PyVISA not available")
            
    def connect(self):
        """Establish VISA connection"""
        try:
            rm = pyvisa.ResourceManager()
            self.connection = rm.open_resource(self.resource_string)
            self.connection.timeout = self.timeout
            self.connection.read_termination = '\n'
            self.connection.write_termination = '\n'
            self.connected = True
            return True
        except Exception as e:
            raise Exception(f"VISA connection failed: {e}")
            
    def disconnect(self):
        """Close VISA connection"""
        if self.connection:
            self.connection.close()
            self.connected = False
            
    def write(self, command):
        """Send command via VISA"""
        if not self.connected:
            raise Exception("Not connected")
        self.connection.write(command)
        
    def query(self, command):
        """Send command and read response via VISA"""
        if not self.connected:
            raise Exception("Not connected")
        return self.connection.query(command).strip()
        
    @staticmethod
    def get_available_resources():
        """Get list of available VISA resources"""
        if not VISA_AVAILABLE:
            return []
        try:
            rm = pyvisa.ResourceManager()
            return rm.list_resources()
        except Exception:
            return []