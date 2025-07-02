#!/usr/bin/env python3
"""
Prodigit 34205A Electronic Load Controller
"""
from typing import Optional
from controllers.base_controller import BaseDeviceController
from models.device_config import DEVICE_SPECS, DeviceType


class ProdigitController(BaseDeviceController):
    """Prodigit 34205A Electronic Load Controller"""
    
    def __init__(self, interface):
        super().__init__(interface, DEVICE_SPECS[DeviceType.PRODIGIT_34205A])
        
    def identify(self):
        """Identify the device using device-specific command"""
        try:
            identify_cmd = self.device_spec.default_commands['identify']
            self.model = self.interface.query(identify_cmd)
        except:
            self.model = "Prodigit 34205A"
        
    def set_mode_cc(self, current: float):
        """Set constant current mode"""
        if current < 0 or current > self.device_spec.max_current:
            raise ValueError(f"Current must be between 0 and {self.device_spec.max_current}A")
            
        self.send_command(self.device_spec.default_commands['set_mode_cc'])
        cmd = self.device_spec.default_commands['set_current'].format(current)
        self.send_command(cmd)
        
    def set_mode_cv(self, voltage: float):
        """Set constant voltage mode"""
        if voltage < 0 or voltage > self.device_spec.max_voltage:
            raise ValueError(f"Voltage must be between 0 and {self.device_spec.max_voltage}V")
            
        self.send_command(self.device_spec.default_commands['set_mode_cv'])
        cmd = self.device_spec.default_commands['set_voltage'].format(voltage)
        self.send_command(cmd)
        
    def set_mode_cp(self, power: float):
        """Set constant power mode"""
        if power < 0 or power > self.device_spec.max_power:
            raise ValueError(f"Power must be between 0 and {self.device_spec.max_power}W")
            
        self.send_command(self.device_spec.default_commands['set_mode_cp'])
        cmd = self.device_spec.default_commands['set_power'].format(power)
        self.send_command(cmd)
        
    def set_mode_cr(self, resistance: float):
        """Set constant resistance mode"""
        if resistance <= 0:
            raise ValueError("Resistance must be greater than 0")
            
        self.send_command(self.device_spec.default_commands['set_mode_cr'])
        cmd = self.device_spec.default_commands['set_resistance'].format(resistance)
        self.send_command(cmd)
        
    def load_on(self):
        """Turn load on"""
        cmd = self.device_spec.default_commands['load_on']
        self.send_command(cmd)
        
    def load_off(self):
        """Turn load off"""
        cmd = self.device_spec.default_commands['load_off']
        self.send_command(cmd)
        
    def measure_voltage(self) -> Optional[float]:
        """Read actual voltage"""
        try:
            cmd = self.device_spec.default_commands['measure_voltage']
            response = self.query_command(cmd)
            return float(response)
        except:
            return None
        
    def measure_current(self) -> Optional[float]:
        """Read actual current"""
        try:
            cmd = self.device_spec.default_commands['measure_current']
            response = self.query_command(cmd)
            return float(response)
        except:
            return None
        
    def measure_power(self) -> Optional[float]:
        """Read actual power"""
        try:
            cmd = self.device_spec.default_commands['measure_power']
            response = self.query_command(cmd)
            return float(response)
        except:
            return None