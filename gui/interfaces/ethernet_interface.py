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
        cmd = command.strip() + '\r\n'
        self.connection.send(cmd.encode())
        
    def query(self, command):
        """Send command and read response via ethernet"""
        self.write(command)
        
        # For buffer data queries that return large amounts of data, use specialized reading
        if 'DATA:DATA?' in command.upper() or 'BUFFER' in command.upper():
            return self._read_large_response()
        
        # Simple response reading for small commands
        response = self.connection.recv(8192).decode().strip()
        return response
    
    def _read_large_response(self):
        """Read potentially large responses in chunks"""
        response_parts = []
        original_timeout = self.timeout
        self.connection.settimeout(5)  # Shorter timeout for buffer data
        
        try:
            # Read initial response
            initial_chunk = self.connection.recv(8192)
            if not initial_chunk:
                return ""
                
            response_parts.append(initial_chunk.decode())
            
            # Continue reading if there might be more data
            # For Keithley buffer data, usually comes in one large chunk
            try:
                while True:
                    self.connection.settimeout(0.5)  # Very short timeout for additional chunks
                    chunk = self.connection.recv(4096)
                    if not chunk:
                        break
                    response_parts.append(chunk.decode())
            except socket.timeout:
                pass  # Expected when no more data
                
        except socket.timeout:
            # If we timeout on initial read, there might be no data
            pass
        finally:
            self.connection.settimeout(original_timeout)  # Reset timeout
            
        result = ''.join(response_parts).strip()
        return result