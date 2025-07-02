#!/usr/bin/env python3
"""
Ethernet TCP socket communication interface
"""
import socket
from interfaces.base_interface import DeviceInterface


class EthernetInterface(DeviceInterface):
    """Ethernet TCP socket communication interface"""
    
    def __init__(self, host, port, timeout=5):
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
        response = self.connection.recv(1024).decode().strip()
        return response