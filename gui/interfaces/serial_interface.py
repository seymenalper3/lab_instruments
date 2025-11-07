#!/usr/bin/env python3
"""
RS232 Serial communication interface
"""
import time
import serial
import serial.tools.list_ports
from interfaces.base_interface import DeviceInterface


class SerialInterface(DeviceInterface):
    """RS232 Serial communication interface"""
    
    def __init__(self, port, baudrate=9600, timeout=5, bytesize=8, parity='N', stopbits=1, rtscts=False):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.rtscts = rtscts
        
    def connect(self):
        """Establish serial connection"""
        import sys
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.timeout,
                rtscts=self.rtscts
            )
            self.connected = True
            return True
        except Exception as e:
            error_msg = str(e).lower()

            # Windows-specific error handling and guidance
            if sys.platform == 'win32':
                if 'could not open port' in error_msg or 'access is denied' in error_msg:
                    # Get available ports for suggestion
                    available_ports = SerialInterface.get_available_ports()
                    ports_list = ', '.join(available_ports) if available_ports else 'None found'
                    raise Exception(
                        f"Cannot open {self.port} on Windows.\n"
                        f"Possible causes:\n"
                        f"  - Port is already in use by another application\n"
                        f"  - USB-to-Serial driver not installed (check Device Manager)\n"
                        f"  - Incorrect COM port number\n"
                        f"  - Device not properly connected\n"
                        f"Available ports: {ports_list}\n"
                        f"Original error: {e}"
                    )
                elif 'filenotfounderror' in error_msg or 'cannot find' in error_msg:
                    available_ports = SerialInterface.get_available_ports()
                    ports_list = ', '.join(available_ports) if available_ports else 'None found'
                    raise Exception(
                        f"Port {self.port} not found on Windows.\n"
                        f"Windows uses COM ports (e.g., COM1, COM3).\n"
                        f"Check Device Manager (devmgmt.msc) under 'Ports (COM & LPT)'.\n"
                        f"Available ports: {ports_list}\n"
                        f"Original error: {e}"
                    )

            # Generic error for non-Windows or unrecognized errors
            raise Exception(f"Serial connection failed: {e}")
            
    def disconnect(self):
        """Close serial connection"""
        if self.connection:
            self.connection.close()
            self.connected = False
            
    def write(self, command):
        """Send command via serial"""
        if not self.connected:
            raise Exception("Not connected")
        cmd = command.strip() + '\r\n'
        print(f"SERIAL SEND: {command}")
        self.connection.write(cmd.encode())
        
    def query(self, command):
        """Send command and read response via serial"""
        self.write(command)
        time.sleep(0.3)  # Increased delay for slower devices
        response = self.connection.readline().decode().strip()
        print(f"SERIAL RECV: {response}")
        return response
        
    @staticmethod
    def get_available_ports():
        """Get list of available serial ports"""
        import sys
        ports = serial.tools.list_ports.comports()

        # On Windows, provide additional helpful information
        if sys.platform == 'win32' and ports:
            print("\nAvailable COM ports on Windows:")
            for port in ports:
                desc = port.description if port.description else "Unknown device"
                print(f"  {port.device}: {desc}")
            print("  (Check Device Manager for more details: Win+X -> Device Manager)\n")

        return [port.device for port in ports]