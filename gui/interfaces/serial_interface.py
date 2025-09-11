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
        return [port.device for port in serial.tools.list_ports.comports()]