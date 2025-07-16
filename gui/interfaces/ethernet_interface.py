#!/usr/bin/env python3
"""
Ethernet TCP socket communication interface
"""
import socket
from interfaces.base_interface import DeviceInterface


class EthernetInterface(DeviceInterface):
    """Ethernet TCP socket communication interface"""
    
    def __init__(self, host, port, timeout=15):
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout
        
    def connect(self):
        """Establish ethernet connection"""
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(self.timeout)
            self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.connection.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            raise Exception(f"Ethernet connection failed: {e}")
            
    def disconnect(self):
        """Close ethernet connection"""
        if self.connection:
            self.connection.close()
            self.connected = False
            
    def write(self, command):
        """Send command via ethernet"""
        if not self.connected:
            raise Exception("Not connected")
        cmd = command.strip() + '\n'
        self.connection.send(cmd.encode())
        
    def query(self, command):
        """Send command and read response via ethernet"""
        self.write(command)
        # Use larger buffer for data-heavy commands like battery data
        if ':BATT:DATA:DATA?' in command:
            response = self._read_large_response()
        else:
            response = self.connection.recv(4096).decode().strip()
        return response
    
    def _read_large_response(self):
        """Read potentially large responses in chunks"""
        response_parts = []
        self.connection.settimeout(15)  # Longer timeout for large data
        
        try:
            while True:
                chunk = self.connection.recv(4096).decode()
                if not chunk or chunk.endswith('\n'):
                    response_parts.append(chunk)
                    break
                response_parts.append(chunk)
        except socket.timeout:
            pass  # Expected for end of data
        finally:
            self.connection.settimeout(self.timeout)  # Reset timeout
            
        return ''.join(response_parts).strip()