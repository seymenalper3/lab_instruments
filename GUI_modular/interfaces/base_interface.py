#!/usr/bin/env python3
"""
Base interface class for device communication
"""
from abc import ABC, abstractmethod


class DeviceInterface(ABC):
    """Abstract base class for device communication interfaces"""
    
    def __init__(self):
        self.connected = False
        self.connection = None
        
    @abstractmethod
    def connect(self):
        """Establish connection to the device"""
        pass
        
    @abstractmethod
    def disconnect(self):
        """Close connection to the device"""
        pass
        
    @abstractmethod
    def write(self, command):
        """Send command to device"""
        pass
        
    @abstractmethod
    def query(self, command):
        """Send command and read response"""
        pass
        
    def is_connected(self):
        """Check if interface is connected"""
        return self.connected