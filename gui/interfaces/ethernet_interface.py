#!/usr/bin/env python3
"""
Ethernet TCP socket communication interface
"""
import socket
from interfaces.base_interface import DeviceInterface


class EthernetInterface(DeviceInterface):
    """Ethernet TCP socket communication interface"""
    
    def __init__(self, host, port, timeout=15, eol='\n'):
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout
        self.eol = eol  # Line termination for SCPI over TCP (default "\n")
        
    def connect(self):
        """Establish ethernet connection"""
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(self.timeout)
            self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # Enable TCP keepalive (best-effort cross-platform)
            try:
                self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            except Exception:
                pass
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
        cmd = command.strip() + self.eol
        self.connection.send(cmd.encode())
        
    def query(self, command):
        """Send command and read response via ethernet"""
        # For buffer/trace queries that return large payloads, use specialized reader
        upper = command.upper()
        if ('DATA:DATA?' in upper) or ('BUFFER' in upper) or ('TRAC' in upper and '?' in upper):
            self.write(command)
            return self._read_large_response()
        
        self.write(command)
        # Read until newline (SCPI terminator) or timeout
        chunks = []
        try:
            self.connection.settimeout(self.timeout)
            while True:
                chunk = self.connection.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
                if self.eol.encode() in chunk or chunk.endswith(b'\n'):
                    break
        except socket.timeout:
            pass
        finally:
            # Restore default timeout
            self.connection.settimeout(self.timeout)
        response = b''.join(chunks).decode().strip()
        return response
    
    def _read_large_response(self):
        """Read potentially large responses in chunks"""
        response_parts = []
        original_timeout = self.timeout
        self.connection.settimeout(5)  # Shorter timeout for buffer data bursts
        
        try:
            # Read initial response
            initial_chunk = self.connection.recv(8192)
            if not initial_chunk:
                return ""
                
            response_parts.append(initial_chunk.decode())
            
            # Continue reading while data keeps arriving
            try:
                while True:
                    self.connection.settimeout(0.5)  # Very short timeout for trailing chunks
                    chunk = self.connection.recv(8192)
                    if not chunk:
                        break
                    response_parts.append(chunk.decode())
            except socket.timeout:
                # No more data available
                pass
                
        except socket.timeout:
            # If we timeout on initial read, there might be no data
            pass
        finally:
            self.connection.settimeout(original_timeout)  # Reset timeout
            
        result = ''.join(response_parts).strip()
        return result