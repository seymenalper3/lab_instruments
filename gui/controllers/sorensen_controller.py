#!/usr/bin/env python3
"""
Sorensen SGX400-12 D Power Supply Controller
"""
import logging
from typing import Optional
from controllers.base_controller import BaseDeviceController
from models.device_config import DEVICE_SPECS, DeviceType

logger = logging.getLogger(__name__)


class SorensenController(BaseDeviceController):
    """Sorensen SGX400-12 D Power Supply Controller"""
    
    def __init__(self, interface):
        super().__init__(interface, DEVICE_SPECS[DeviceType.SORENSEN_SGX])
        self._last_voltage: Optional[float] = None  # Track last set voltage for power calculation
        self._last_current: Optional[float] = None  # Track last set current for power calculation
        
    def set_voltage(self, voltage: float):
        """Set output voltage in volts"""
        if voltage < 0 or voltage > self.device_spec.max_voltage:
            raise ValueError(f"Voltage must be between 0 and {self.device_spec.max_voltage}V")
        
        # Check power limit if we have current value
        if self._last_current is not None and self.device_spec.max_power:
            power = voltage * self._last_current
            if power > self.device_spec.max_power:
                raise ValueError(
                    f"Power limit exceeded: {power:.1f}W > {self.device_spec.max_power}W. "
                    f"Reduce voltage ({voltage}V) or current ({self._last_current}A)."
                )
        
        cmd = self.device_spec.default_commands['set_voltage'].format(voltage)
        self.send_command(cmd)
        self._last_voltage = voltage
        
    def set_current(self, current: float):
        """Set current limit in amperes"""
        if current < 0 or current > self.device_spec.max_current:
            raise ValueError(f"Current must be between 0 and {self.device_spec.max_current}A")
        
        # Check power limit if we have voltage value
        if self._last_voltage is not None and self.device_spec.max_power:
            power = self._last_voltage * current
            if power > self.device_spec.max_power:
                raise ValueError(
                    f"Power limit exceeded: {power:.1f}W > {self.device_spec.max_power}W. "
                    f"Reduce voltage ({self._last_voltage}V) or current ({current}A)."
                )
            
        cmd = self.device_spec.default_commands['set_current'].format(current)
        self.send_command(cmd)
        self._last_current = current
        
    def set_ovp(self, ovp_voltage: float):
        """Set overvoltage protection"""
        if ovp_voltage < 0 or ovp_voltage > self.device_spec.max_voltage:
            raise ValueError(f"OVP voltage must be between 0 and {self.device_spec.max_voltage}V")
            
        logger.info(f"Setting OVP to {ovp_voltage}V")
        cmd = self.device_spec.default_commands['set_ovp'].format(ovp_voltage)
        self.send_command(cmd, check_errors=True)
        logger.info(f"OVP set successfully to {ovp_voltage}V")
    
    def set_ocp(self, ocp_current: float):
        """Set overcurrent protection"""
        if ocp_current < 0 or ocp_current > self.device_spec.max_current:
            raise ValueError(f"OCP current must be between 0 and {self.device_spec.max_current}A")
        
        logger.info(f"Setting OCP to {ocp_current}A")
        cmd = 'SOUR:CURR:PROT {}'.format(ocp_current)
        self.send_command(cmd, check_errors=True)
        logger.info(f"OCP set successfully to {ocp_current}A")
        
    def output_on(self):
        """Turn output on"""
        logger.warning("Turning output ON - safety critical operation")
        cmd = self.device_spec.default_commands['output_on']
        self.send_command(cmd, check_errors=True)
        logger.info("Output turned ON successfully")
        
    def output_off(self):
        """Turn output off"""
        logger.info("Turning output OFF")
        cmd = self.device_spec.default_commands['output_off']
        self.send_command(cmd, check_errors=True)
        logger.info("Output turned OFF successfully")
        
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