#!/usr/bin/env python3
"""
Prodigit 34205A Electronic Load Controller
"""
from typing import Optional
from controllers.base_controller import BaseDeviceController
from models.device_config import DEVICE_SPECS, DeviceType
import time


class ProdigitController(BaseDeviceController):
    """Prodigit 34205A Electronic Load Controller"""

    def __init__(self, interface):
        super().__init__(interface, DEVICE_SPECS[DeviceType.PRODIGIT_34205A])
        self.current_mode = None

    def send_command(self, command: str):
        """Override send_command to add a delay for Prodigit devices."""
        super().send_command(command)
        time.sleep(0.2)

    def _set_mode(self, mode_cmd: str, mode_name: str):
        """Helper to set the device mode."""
        self.send_command(mode_cmd)
        self.current_mode = mode_name
        # time.sleep(0.2) # Delay is now in send_command

    def set_mode_cc(self):
        """Set Constant Current mode."""
        cmd = self.device_spec.default_commands['set_mode_cc']
        self._set_mode(cmd, 'CC')

    def set_mode_cv(self):
        """Set Constant Voltage mode."""
        cmd = self.device_spec.default_commands['set_mode_cv']
        self._set_mode(cmd, 'CV')

    def set_mode_cp(self):
        """Set Constant Power mode."""
        cmd = self.device_spec.default_commands['set_mode_cp']
        self._set_mode(cmd, 'CP')

    def set_mode_cr(self):
        """Set Constant Resistance mode."""
        cmd = self.device_spec.default_commands['set_mode_cr']
        self._set_mode(cmd, 'CR')

    def set_current(self, current: float):
        """Set current in Amperes (for CC mode)."""
        if not 0 <= current <= self.device_spec.max_current:
            raise ValueError(f"Current must be between 0 and {self.device_spec.max_current}A")
        cmd = self.device_spec.default_commands['set_current'].format(current)
        self.send_command(cmd)

    def set_voltage(self, voltage: float):
        """Set voltage in Volts (for CV mode)."""
        if not 0 <= voltage <= self.device_spec.max_voltage:
            raise ValueError(f"Voltage must be between 0 and {self.device_spec.max_voltage}V")
        cmd = self.device_spec.default_commands['set_voltage'].format(voltage)
        self.send_command(cmd)

    def set_power(self, power: float):
        """Set power in Watts (for CP mode)."""
        if not 0 <= power <= self.device_spec.max_power:
            raise ValueError(f"Power must be between 0 and {self.device_spec.max_power}W")
        cmd = self.device_spec.default_commands['set_power'].format(power)
        self.send_command(cmd)

    def set_resistance(self, resistance: float):
        """Set resistance in Ohms (for CR mode)."""
        # Add a reasonable upper limit for resistance if not specified
        if not 0 <= resistance:
             raise ValueError("Resistance must be a positive value")
        cmd = self.device_spec.default_commands['set_resistance'].format(resistance)
        self.send_command(cmd)

    def load_on(self):
        """Turn load on."""
        cmd = self.device_spec.default_commands['load_on']
        self.send_command(cmd)

    def load_off(self):
        """Turn load off."""
        cmd = self.device_spec.default_commands['load_off']
        self.send_command(cmd)

    def measure_voltage(self) -> Optional[float]:
        """Read voltage measurement."""
        try:
            cmd = self.device_spec.default_commands['measure_voltage']
            response = self.query_command(cmd)
            return float(response)
        except (ValueError, TypeError):
            return None

    def measure_current(self) -> Optional[float]:
        """Read current measurement."""
        try:
            cmd = self.device_spec.default_commands['measure_current']
            response = self.query_command(cmd)
            return float(response)
        except (ValueError, TypeError):
            return None

    def measure_power(self) -> Optional[float]:
        """Read power measurement."""
        try:
            cmd = self.device_spec.default_commands['measure_power']
            response = self.query_command(cmd)
            return float(response)
        except (ValueError, TypeError):
            return None

    def query_mode(self) -> Optional[str]:
        """Query the current operating mode."""
        try:
            cmd = self.device_spec.default_commands['query_mode']
            return self.query_command(cmd)
        except Exception:
            return None

    def query_load_status(self) -> Optional[str]:
        """Query the load status (ON/OFF)."""
        try:
            cmd = self.device_spec.default_commands['query_load']
            return self.query_command(cmd)
        except Exception:
            return None

    def query_error(self) -> Optional[str]:
        """Query for errors."""
        try:
            cmd = self.device_spec.default_commands['query_error']
            return self.query_command(cmd)
        except Exception:
            return None

    def output_on(self):
        """Wrapper for load_on to match base controller expectations."""
        self.load_on()

    def output_off(self):
        """Wrapper for load_off to match base controller expectations."""
        self.load_off()