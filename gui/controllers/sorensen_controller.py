#!/usr/bin/env python3
"""
Sorensen SGX400-12 D Power Supply Controller
"""
from typing import Optional
from controllers.base_controller import BaseDeviceController
from models.device_config import DEVICE_SPECS, DeviceType


class SorensenController(BaseDeviceController):
    """Sorensen SGX400-12 D Power Supply Controller"""
    
    def __init__(self, interface):
        super().__init__(interface, DEVICE_SPECS[DeviceType.SORENSEN_SGX])
        
    def set_voltage(self, voltage: float):
        """Set output voltage in volts"""
        if voltage < 0 or voltage > self.device_spec.max_voltage:
            raise ValueError(f"Voltage must be between 0 and {self.device_spec.max_voltage}V")
        
        cmd = self.device_spec.default_commands['set_voltage'].format(voltage)
        self.send_command(cmd)
        
    def set_current(self, current: float):
        """Set current limit in amperes"""
        if current < 0 or current > self.device_spec.max_current:
            raise ValueError(f"Current must be between 0 and {self.device_spec.max_current}A")
            
        cmd = self.device_spec.default_commands['set_current'].format(current)
        self.send_command(cmd)
        
    def set_ovp(self, ovp_voltage: float):
        """Set overvoltage protection"""
        if ovp_voltage < 0 or ovp_voltage > self.device_spec.max_voltage:
            raise ValueError(f"OVP voltage must be between 0 and {self.device_spec.max_voltage}V")
            
        cmd = self.device_spec.default_commands['set_ovp'].format(ovp_voltage)
        self.send_command(cmd)
        
    def output_on(self):
        """Turn output on"""
        cmd = self.device_spec.default_commands['output_on']
        self.send_command(cmd)
        
    def output_off(self):
        """Turn output off"""
        cmd = self.device_spec.default_commands['output_off']
        self.send_command(cmd)
        
    def measure_voltage(self) -> Optional[float]:
        """Read actual output voltage"""
        try:
            cmd = self.device_spec.default_commands['measure_voltage']
            response = self.query_command(cmd)
            return float(response)
        except:
            return None
        
    def measure_current(self) -> Optional[float]:
        """Read actual output current"""
        try:
            cmd = self.device_spec.default_commands['measure_current']
            response = self.query_command(cmd)
            return float(response)
        except:
            return None
            
    def measure_power(self) -> Optional[float]:
        """Calculate power from voltage and current"""
        try:
            voltage = self.measure_voltage()
            current = self.measure_current()
            if voltage is not None and current is not None:
                return voltage * current
        except:
            pass
        return None