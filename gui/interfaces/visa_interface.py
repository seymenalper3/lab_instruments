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
        import sys
        try:
            rm = pyvisa.ResourceManager()
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
                # Default for USBTMC, GPIB, etc.
                self.connection.read_termination = '\n'
                self.connection.write_termination = '\n'

            self.connected = True
            return True
        except Exception as e:
            error_msg = str(e).lower()

            # Windows-specific error handling and guidance
            if sys.platform == 'win32':
                if 'visa library' in error_msg or 'no backend' in error_msg or 'visa.dll' in error_msg:
                    raise Exception(
                        f"VISA driver not found on Windows.\n"
                        f"Please install NI-VISA from: https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html\n"
                        f"Or Keysight IO Libraries from: https://www.keysight.com/us/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html\n"
                        f"Original error: {e}"
                    )
                elif 'asrl' in self.resource_string.lower() and ('access' in error_msg or 'port' in error_msg):
                    # Extract COM port number from ASRL resource string (e.g., ASRL1::INSTR -> COM1)
                    import re
                    match = re.search(r'ASRL(\d+)', self.resource_string, re.IGNORECASE)
                    com_port = f"COM{match.group(1)}" if match else "COM port"
                    raise Exception(
                        f"Cannot access {com_port} on Windows.\n"
                        f"Possible causes:\n"
                        f"  - Port is already in use by another application\n"
                        f"  - USB driver not installed (check Device Manager)\n"
                        f"  - Insufficient permissions\n"
                        f"Original error: {e}"
                    )
                elif 'resource' in error_msg and 'not found' in error_msg:
                    raise Exception(
                        f"Device not found: {self.resource_string}\n"
                        f"Windows troubleshooting:\n"
                        f"  - Check Device Manager for device presence\n"
                        f"  - Verify USB cable connection\n"
                        f"  - Try a different USB port\n"
                        f"  - Reinstall device drivers\n"
                        f"Original error: {e}"
                    )

            # Generic error for non-Windows or unrecognized errors
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
        import sys
        if not VISA_AVAILABLE:
            return []
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            return resources
        except Exception as e:
            # Windows-specific error guidance
            if sys.platform == 'win32':
                error_msg = str(e).lower()
                if 'visa library' in error_msg or 'no backend' in error_msg:
                    print("WARNING: VISA driver not detected on Windows.")
                    print("Install NI-VISA to detect USB/GPIB devices: https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html")
            return []