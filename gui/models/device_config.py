#!/usr/bin/env python3
"""
Device configuration models
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from enum import Enum


class InterfaceType(Enum):
    """Supported interface types"""
    RS232 = "RS232"
    ETHERNET = "Ethernet"
    USB = "USB"
    GPIB = "GPIB"


class DeviceType(Enum):
    """Supported device types"""
    SORENSEN_SGX = "Sorensen SGX400-12"
    KEITHLEY_2281S = "Keithley 2281S"
    PRODIGIT_34205A = "Prodigit 34205A"


@dataclass
class ConnectionConfig:
    """Connection configuration for a device"""
    interface_type: InterfaceType
    parameters: Dict[str, Union[str, int, float]]
    
    @classmethod
    def create_serial(cls, port: str, baudrate: int = 9600, timeout: float = 5.0):
        """Create serial connection configuration"""
        return cls(
            interface_type=InterfaceType.RS232,
            parameters={
                'port': port,
                'baudrate': baudrate,
                'timeout': timeout
            }
        )
    
    @classmethod
    def create_ethernet(cls, host: str, port: int, timeout: float = 5.0):
        """Create ethernet connection configuration"""
        return cls(
            interface_type=InterfaceType.ETHERNET,
            parameters={
                'host': host,
                'port': port,
                'timeout': timeout
            }
        )
    
    @classmethod
    def create_visa(cls, resource_string: str, timeout: int = 5000):
        """Create VISA connection configuration"""
        interface_type = InterfaceType.USB if 'USB' in resource_string else InterfaceType.GPIB
        return cls(
            interface_type=interface_type,
            parameters={
                'resource_string': resource_string,
                'timeout': timeout
            }
        )


@dataclass
class DeviceSpec:
    """Device specifications and capabilities"""
    name: str
    device_type: DeviceType
    max_voltage: float
    max_current: float
    max_power: Optional[float] = None
    supported_interfaces: List[InterfaceType] = None
    default_commands: Dict[str, str] = None
    
    def __post_init__(self):
        if self.supported_interfaces is None:
            self.supported_interfaces = []
        if self.default_commands is None:
            self.default_commands = {}


# Device specifications
DEVICE_SPECS = {
    DeviceType.SORENSEN_SGX: DeviceSpec(
        name="Sorensen SGX400-12 D",
        device_type=DeviceType.SORENSEN_SGX,
        max_voltage=400.0,
        max_current=12.0,
        max_power=4800.0,
        supported_interfaces=[InterfaceType.RS232, InterfaceType.ETHERNET, InterfaceType.GPIB],
        default_commands={
            'identify': '*IDN?',
            'set_voltage': 'SOUR:VOLT {}',
            'set_current': 'SOUR:CURR {}',
            'set_ovp': 'SOUR:VOLT:PROT {}',
            'output_on': 'OUTP:STAT ON',
            'output_off': 'OUTP:STAT OFF',
            'measure_voltage': 'MEAS:VOLT?',
            'measure_current': 'MEAS:CURR?'
        }
    ),
    
    DeviceType.KEITHLEY_2281S: DeviceSpec(
        name="Keithley 2281S",
        device_type=DeviceType.KEITHLEY_2281S,
        max_voltage=20.0,
        max_current=6.0,
        max_power=120.0,
        supported_interfaces=[InterfaceType.USB, InterfaceType.ETHERNET, InterfaceType.GPIB],
        default_commands={
            'identify': '*IDN?',
            'set_voltage': ':SOUR:VOLT {}',
            'set_current': ':SOUR:CURR {}',
            'output_on': ':OUTP ON',
            'output_off': ':OUTP OFF',
            'battery_output_on': ':BATT:OUTP ON',
            'battery_output_off': ':BATT:OUTP OFF',
            'measure_voltage': ':MEAS:VOLT?',
            'measure_current': ':MEAS:CURR?',
            'measure_combined': ':MEAS:VOLT?',
            'power_supply_mode': ':ENTRy:FUNC POWer',
            'battery_test_mode': ':ENTRy:FUNC TEST',
            'query_mode': ':ENTRy:FUNC?',
            'battery_discharge_mode': ':BATT:TEST:MODE DIS',
            'battery_current_limit': ':BATT:TEST:CURR:LIM:SOUR {}',
            'battery_current_end': ':BATT:TEST:CURR:END {}',
            'battery_data_buffer': ':BATT:DATA:DATA? "VOLT,CURR,REL"',
            'battery_data_clear': ':BATT:DATA:CLE',
            'battery_data_status_on': ':BATT:DATA:STAT ON',
            'battery_data_status_off': ':BATT:DATA:STAT OFF',
            'set_voltage_protection': ':VOLT:PROT {}',
            'system_key': ':SYST:KEY {}',
            'remote_mode': 'SYST:REM',
            'local_mode': 'SYST:LOC',
            'clear': '*CLS',
            'reset': '*RST'
        }
    ),
    
    DeviceType.PRODIGIT_34205A: DeviceSpec(
        name="Prodigit 34205A",
        device_type=DeviceType.PRODIGIT_34205A,
        max_voltage=600.0,
        max_current=160.0,
        max_power=5000.0,
        supported_interfaces=[InterfaceType.RS232, InterfaceType.USB],
        default_commands={
            'identify': '*IDN?',
            'set_mode_cc': 'MODE CC',
            'set_current': 'CC:HIGH {}',
            'set_mode_cv': 'MODE CV',
            'set_voltage': 'CV:HIGH {}',
            'set_mode_cp': 'MODE CP',
            'set_power': 'CP:HIGH {}',
            'set_mode_cr': 'MODE CR',
            'set_resistance': 'CR:HIGH {}',
            'load_on': 'LOAD ON',
            'load_off': 'LOAD OFF',
            'measure_voltage': 'MEAS:VOLT?',
            'measure_current': 'MEAS:CURR?',
            'measure_power': 'MEAS:POW?',
            'query_mode': 'MODE?',
            'query_load': 'LOAD?',
            'query_error': 'ERR?'
        }
    )
}


@dataclass
class MeasurementData:
    """Data structure for device measurements"""
    timestamp: str
    voltage: Optional[float] = None
    current: Optional[float] = None
    power: Optional[float] = None
    
    def to_dict(self):
        """Convert to dictionary for CSV export"""
        return {
            'timestamp': self.timestamp,
            'voltage': self.voltage,
            'current': self.current,
            'power': self.power
        }