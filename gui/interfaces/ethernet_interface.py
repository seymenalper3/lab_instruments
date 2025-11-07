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
        import sys
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(self.timeout)
            self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.connection.connect((self.host, self.port))
            self.connected = True
            return True
        except socket.timeout:
            # Timeout-specific error message
            if sys.platform == 'win32':
                raise Exception(
                    f"Connection timeout to {self.host}:{self.port} on Windows.\n"
                    f"Possible causes:\n"
                    f"  - Device is not reachable on the network\n"
                    f"  - Incorrect IP address or port number\n"
                    f"  - Windows Firewall blocking connection\n"
                    f"  - Device firewall blocking incoming connections\n"
                    f"Troubleshooting:\n"
                    f"  1. Ping the device: ping {self.host}\n"
                    f"  2. Check firewall: Win+R -> firewalll.cpl\n"
                    f"  3. Verify device IP in instrument settings\n"
                    f"  4. Try temporarily disabling Windows Firewall for testing"
                )
            else:
                raise Exception(f"Connection timeout to {self.host}:{self.port}")
        except ConnectionRefusedError:
            # Connection refused - device reachable but port closed
            if sys.platform == 'win32':
                raise Exception(
                    f"Connection refused by {self.host}:{self.port} on Windows.\n"
                    f"The device is reachable, but not accepting connections on port {self.port}.\n"
                    f"Possible causes:\n"
                    f"  - Incorrect port number (check device manual)\n"
                    f"  - Device not configured for remote access\n"
                    f"  - Telnet/Socket interface disabled on device\n"
                    f"Troubleshooting:\n"
                    f"  - Verify port number in device settings\n"
                    f"  - Enable remote interface on device (typically port 5025 for SCPI)"
                )
            else:
                raise Exception(f"Connection refused by {self.host}:{self.port}")
        except OSError as e:
            # Network unreachable or other OS errors
            error_msg = str(e).lower()
            if sys.platform == 'win32':
                if 'network is unreachable' in error_msg or 'no route' in error_msg:
                    raise Exception(
                        f"Network unreachable to {self.host}:{self.port} on Windows.\n"
                        f"Possible causes:\n"
                        f"  - Device not on the same network\n"
                        f"  - Network cable unplugged\n"
                        f"  - Incorrect IP address\n"
                        f"  - Wi-Fi/Ethernet adapter disabled\n"
                        f"Troubleshooting:\n"
                        f"  - Check network connection: ipconfig\n"
                        f"  - Verify device and PC on same subnet\n"
                        f"  - Check network cable connection\n"
                        f"Original error: {e}"
                    )
                elif 'permission' in error_msg or 'access' in error_msg:
                    raise Exception(
                        f"Permission denied for {self.host}:{self.port} on Windows.\n"
                        f"Possible causes:\n"
                        f"  - Windows Firewall blocking outbound connection\n"
                        f"  - Security software blocking network access\n"
                        f"  - Insufficient user permissions\n"
                        f"Troubleshooting:\n"
                        f"  - Run as Administrator\n"
                        f"  - Check Windows Firewall settings\n"
                        f"  - Temporarily disable antivirus for testing\n"
                        f"Original error: {e}"
                    )
            raise Exception(f"Ethernet connection failed: {e}")
        except Exception as e:
            # Generic catch-all
            if sys.platform == 'win32':
                raise Exception(
                    f"Ethernet connection failed to {self.host}:{self.port} on Windows.\n"
                    f"Basic troubleshooting:\n"
                    f"  - Verify device IP address and port\n"
                    f"  - Check network connection (ping {self.host})\n"
                    f"  - Check Windows Firewall settings\n"
                    f"  - Ensure device is powered on and network-enabled\n"
                    f"Original error: {e}"
                )
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