#!/usr/bin/env python3
"""
VISA communication interface for USB and GPIB
"""
from interfaces.base_interface import DeviceInterface

try:
    import pyvisa
    from pyvisa import constants
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
            print(f"VISA OPEN: {self.resource_string} (timeout {self.timeout}ms)")
            self.connection = rm.open_resource(self.resource_string)
            self.connection.timeout = self.timeout
            
            # Special handling for VISA-Serial (ASRL) resources like the Prodigit
            if 'ASRL' in self.resource_string:
                print("Configuring VISA-Serial port with Prodigit settings...")
                self.connection.baud_rate = 115200
                self.connection.data_bits = 8
                self.connection.parity = constants.Parity.none
                self.connection.stop_bits = constants.StopBits.one
                self.connection.flow_control = constants.VI_ASRL_FLOW_NONE
                self.connection.read_termination = '\r\n'
                self.connection.write_termination = '\r\n'
            else:
                # Default for USBTMC, TCPIP, GPIB, etc.
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
        print(f"VISA SEND: {command}")
        self.connection.write(command)
        
    def query(self, command):
        """Send command and read response via VISA"""
        if not self.connected:
            raise Exception("Not connected")
        print(f"VISA QUERY: {command}")
        response = self.connection.query(command).strip()
        print(f"VISA RECV: {response}")
        return response
        
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