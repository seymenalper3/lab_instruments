#!/usr/bin/env python3
"""
Keithley 2281S Battery Simulator/Emulator Controller
Refactored with modular test runners (delegation pattern)
"""
import csv
import time
import datetime
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from controllers.base_controller import BaseDeviceController
from models.device_config import DEVICE_SPECS, DeviceType
from utils.keithley_logger import KeithleyLogger

# Import test runners (modular)
from controllers.keithley.tests.pulse_test import KeithleyPulseTest
from controllers.keithley.tests.battery_model import KeithleyBatteryModel
from controllers.keithley.tests.profile_runner import KeithleyProfileRunner

logger = logging.getLogger(__name__)


class KeithleyController(BaseDeviceController):
    """
    Keithley 2281S Battery Simulator/Emulator Controller
    
    Refactored Architecture:
    - Core controller handles device communication and basic operations
    - Test runners handle complex test logic (composition over inheritance)
    - Backward compatible - existing code continues to work
    """
    
    def __init__(self, interface):
        super().__init__(interface, DEVICE_SPECS[DeviceType.KEITHLEY_2281S])
        self.current_mode: Optional[str] = None  # Track current mode
        self.logger = KeithleyLogger()  # Structured logging
        self.mode_switch_delay = 3.0  # Delay after mode switch (seconds)
        self._last_voltage: Optional[float] = None  # Track last set voltage for power calculation
        self._last_current: Optional[float] = None  # Track last set current for power calculation
        
        # Test runners (composition - modular design)
        self._pulse_test = KeithleyPulseTest(self)
        self._battery_model = KeithleyBatteryModel(self)
        self._profile_runner = KeithleyProfileRunner(self)
        
    def set_voltage(self, voltage: float):
        """Set output voltage in volts - mode dependent"""
        if voltage < 0 or voltage > self.device_spec.max_voltage:
            raise ValueError(f"Voltage must be between 0 and {self.device_spec.max_voltage}V")
        
        # Check power limit using actual device current
        if self.device_spec.max_power:
            # Try to get actual current from device for accurate power calculation
            try:
                actual_current = self.measure_current()
                if actual_current is not None:
                    power = voltage * actual_current
                    if power > self.device_spec.max_power:
                        raise ValueError(
                            f"Power limit exceeded: {power:.1f}W > {self.device_spec.max_power}W. "
                            f"Reduce voltage ({voltage}V) or current ({actual_current:.3f}A)."
                        )
            except Exception as e:
                # If measurement fails, use cached value as fallback
                if self._last_current is not None:
                    power = voltage * self._last_current
                    if power > self.device_spec.max_power:
                        print(f"Warning: Using cached current value for power check (measurement failed: {e})")
                        raise ValueError(
                            f"Power limit exceeded: {power:.1f}W > {self.device_spec.max_power}W (using cached current). "
                            f"Reduce voltage ({voltage}V) or current ({self._last_current}A)."
                        )
        
        # Use different commands based on current mode
        if self.current_mode == 'test':
            # In Battery Test mode, voltage setting is more complex
            # For discharge, we typically set end voltage
            print(f"Setting Battery Test end voltage to {voltage}V")
            self.send_command(f':BATT:TEST:VOLT {voltage}')
            # Also set discharge current as voltage control is different in battery test
            print("Note: In Battery Test mode, current control is primary")
        else:
            # Power Supply mode
            cmd = self.device_spec.default_commands['set_voltage'].format(voltage)
            self.send_command(cmd)
        
        self._last_voltage = voltage
        
    def set_current_limit(self, current: float):
        """Set current limit in amperes - mode dependent"""
        if current < 0 or current > self.device_spec.max_current:
            raise ValueError(f"Current must be between 0 and {self.device_spec.max_current}A")

        # Check power limit using actual device voltage
        if self.device_spec.max_power:
            # Try to get actual voltage from device for accurate power calculation
            try:
                actual_voltage = self.measure_voltage()
                if actual_voltage is not None:
                    power = actual_voltage * current
                    if power > self.device_spec.max_power:
                        raise ValueError(
                            f"Power limit exceeded: {power:.1f}W > {self.device_spec.max_power}W. "
                            f"Reduce voltage ({actual_voltage:.3f}V) or current ({current}A)."
                        )
            except Exception as e:
                # If measurement fails, use cached value as fallback
                if self._last_voltage is not None:
                    power = self._last_voltage * current
                    if power > self.device_spec.max_power:
                        print(f"Warning: Using cached voltage value for power check (measurement failed: {e})")
                        raise ValueError(
                            f"Power limit exceeded: {power:.1f}W > {self.device_spec.max_power}W (using cached voltage). "
                            f"Reduce voltage ({self._last_voltage}V) or current ({current}A)."
                        )

        # Use different commands based on current mode
        if self.current_mode == 'test':
            # In Battery Test mode, set I-Limit parameter
            print(f"Setting Battery Test I-Limit to {current}A")
            self.send_command(f':BATT:TEST:SENS:AH:ILIM {current}')
        else:
            # Power Supply mode
            cmd = self.device_spec.default_commands['set_current'].format(current)
            self.send_command(cmd)
        
        self._last_current = current
        
    def output_on(self):
        """Turn output on - mode dependent"""
        logger.warning(f"Turning output ON (mode: {self.current_mode}) - safety critical operation")
        if self.current_mode == 'test':
            # In Battery Test mode, use battery output
            logger.info("Turning on Battery Test output")
            self.send_command(':BATT:OUTP ON', check_errors=True)
        else:
            # Power Supply mode
            cmd = self.device_spec.default_commands['output_on']
            self.send_command(cmd, check_errors=True)
        logger.info("Output turned ON successfully")
        
    def output_off(self):
        """Turn output off - mode dependent"""
        logger.info(f"Turning output OFF (mode: {self.current_mode})")
        if self.current_mode == 'test':
            # In Battery Test mode, use battery output
            logger.info("Turning off Battery Test output")
            self.send_command(':BATT:OUTP OFF', check_errors=True)
        else:
            # Power Supply mode
            cmd = self.device_spec.default_commands['output_off']
            self.send_command(cmd, check_errors=True)
        logger.info("Output turned OFF successfully")
        
    def battery_test_mode(self):
        """Switch to battery test function"""
        cmd = self.device_spec.default_commands['battery_test_mode']
        self.send_command(cmd)
        
    def remote_mode(self):
        """Set device to remote mode"""
        cmd = self.device_spec.default_commands['remote_mode']
        self.send_command(cmd)
        
    def local_mode(self):
        """Set device to local mode"""
        cmd = self.device_spec.default_commands['local_mode']
        self.send_command(cmd)
    
    def switch_to_power_supply_mode(self) -> bool:
        """
        Switch instrument to Power Supply mode for charging
        Based on reference script auto_mode_profile.py
        """
        if self.current_mode == 'power':
            return True
            
        print("Switching to Power Supply mode...")
        try:
            # Turn off any outputs first and verify
            output_off_success = False
            try:
                self.send_command(self.device_spec.default_commands['output_off'])
                time.sleep(0.2)
                # Verify output is off
                try:
                    output_state = self.query_command(':OUTP?').strip()
                    if output_state.upper() in ['0', 'OFF']:
                        output_off_success = True
                        print("Power Supply output verified OFF")
                    else:
                        print(f"Warning: Power Supply output may still be ON (state: {output_state})")
                except Exception as e:
                    print(f"Warning: Could not verify Power Supply output state: {e}")
            except Exception as e:
                print(f"Warning: Failed to turn off Power Supply output: {e}")
            
            battery_output_off_success = False
            try:
                self.send_command(self.device_spec.default_commands['battery_output_off'])
                time.sleep(0.2)
                # Verify battery output is off
                try:
                    battery_output_state = self.query_command(':BATT:OUTP?').strip()
                    if battery_output_state.upper() in ['0', 'OFF']:
                        battery_output_off_success = True
                        print("Battery output verified OFF")
                    else:
                        print(f"Warning: Battery output may still be ON (state: {battery_output_state})")
                except Exception as e:
                    print(f"Warning: Could not verify Battery output state: {e}")
            except Exception as e:
                print(f"Warning: Failed to turn off Battery output: {e}")
            
            if not output_off_success and not battery_output_off_success:
                print("Warning: Could not verify that outputs are OFF before mode switch")
            
            # Clear any pending data
            self.send_command(self.device_spec.default_commands['clear'])
            time.sleep(0.5)
            
            # Switch to Power Supply mode
            print("Sending Power Supply mode command...")
            self.send_command(self.device_spec.default_commands['power_supply_mode'])
            print("Waiting for mode switch to complete...")
            time.sleep(self.mode_switch_delay)
            
            # Verify mode switch with retries
            for attempt in range(3):
                try:
                    current_func = self.query_command(self.device_spec.default_commands['query_mode']).strip()
                    print(f"Mode query returned: '{current_func}'")
                    if current_func.upper() in ['POWER', 'POW']:
                        self.current_mode = 'power'
                        print("Successfully switched to Power Supply mode")
                        return True
                    else:
                        print(f"Attempt {attempt + 1}: Expected POWER mode, got '{current_func}'")
                        if attempt < 2:
                            time.sleep(1)
                except Exception as e:
                    print(f"Mode verification attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        time.sleep(1)
            
            # If verification failed after all retries, raise an error
            error_msg = "Failed to verify Power Supply mode switch after 3 attempts"
            print(f"ERROR: {error_msg}")
            raise RuntimeError(error_msg)

        except RuntimeError:
            # Re-raise runtime errors from verification failure
            raise
        except Exception as e:
            print(f"Failed to switch to Power Supply mode: {e}")
            raise RuntimeError(f"Mode switch failed: {e}")

    def switch_to_battery_test_mode(self) -> bool:
        """
        Switch instrument to Battery Test mode for discharging
        Based on reference script auto_mode_profile.py
        """
        if self.current_mode == 'test':
            return True
            
        print("Switching to Battery Test mode...")
        try:
            # Turn off any outputs first and verify
            output_off_success = False
            try:
                self.send_command(self.device_spec.default_commands['output_off'])
                time.sleep(0.2)
                # Verify output is off
                try:
                    output_state = self.query_command(':OUTP?').strip()
                    if output_state.upper() in ['0', 'OFF']:
                        output_off_success = True
                        print("Power Supply output verified OFF")
                    else:
                        print(f"Warning: Power Supply output may still be ON (state: {output_state})")
                except Exception as e:
                    print(f"Warning: Could not verify Power Supply output state: {e}")
            except Exception as e:
                print(f"Warning: Failed to turn off Power Supply output: {e}")
            
            battery_output_off_success = False
            try:
                self.send_command(self.device_spec.default_commands['battery_output_off'])
                time.sleep(0.2)
                # Verify battery output is off
                try:
                    battery_output_state = self.query_command(':BATT:OUTP?').strip()
                    if battery_output_state.upper() in ['0', 'OFF']:
                        battery_output_off_success = True
                        print("Battery output verified OFF")
                    else:
                        print(f"Warning: Battery output may still be ON (state: {battery_output_state})")
                except Exception as e:
                    print(f"Warning: Could not verify Battery output state: {e}")
            except Exception as e:
                print(f"Warning: Failed to turn off Battery output: {e}")
            
            if not output_off_success and not battery_output_off_success:
                print("Warning: Could not verify that outputs are OFF before mode switch")
            
            # Clear any pending data
            self.send_command(self.device_spec.default_commands['clear'])
            time.sleep(0.5)
            
            # Switch to Battery Test mode
            print("Sending Battery Test mode command...")
            self.send_command(self.device_spec.default_commands['battery_test_mode'])
            print("Waiting for mode switch to complete...")
            time.sleep(self.mode_switch_delay)
            
            # Configure Battery Test mode defaults
            try:
                self.send_command(':BATT:TEST:MODE DIS')  # Set to discharge mode
                print("Battery Test mode configured for discharge")
            except Exception as e:
                print(f"Warning: Could not configure Battery Test defaults: {e}")
            
            # Verify mode switch with retries
            for attempt in range(3):
                try:
                    current_func = self.query_command(self.device_spec.default_commands['query_mode']).strip()
                    print(f"Mode query returned: '{current_func}'")
                    if current_func.upper() in ['TEST', 'BATT']:
                        self.current_mode = 'test'
                        print("Successfully switched to Battery Test mode")
                        return True
                    else:
                        print(f"Attempt {attempt + 1}: Expected TEST mode, got '{current_func}'")
                        if attempt < 2:
                            time.sleep(1)
                except Exception as e:
                    print(f"Mode verification attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        time.sleep(1)
            
            # If verification failed after all retries, raise an error
            error_msg = "Failed to verify Battery Test mode switch after 3 attempts"
            print(f"ERROR: {error_msg}")
            raise RuntimeError(error_msg)

        except RuntimeError:
            # Re-raise runtime errors from verification failure
            raise
        except Exception as e:
            print(f"Failed to switch to Battery Test mode: {e}")
            raise RuntimeError(f"Mode switch failed: {e}")
    
    def connect_and_prep(self) -> bool:
        """
        Connect to instrument and prepare for commands
        Based on reference script pattern
        """
        try:
            if not self.connected:
                print("Connecting to instrument...")
                # Connection is handled by base class, just verify
                if hasattr(self.interface, 'connection'):
                    # Clear any pending data
                    self.send_command(self.device_spec.default_commands['clear'])
                    
                    # Test basic communication
                    idn_response = self.query_command(self.device_spec.default_commands['identify'])
                    print(f"Connected: {idn_response.strip()}")
                    return True
            return True
        except Exception as e:
            print(f"Connection Failed: {e}")
            return False
    
    def is_ethernet_connection(self):
        """Check if using ethernet connection"""
        return hasattr(self.interface, 'host')
    
    def send_command_with_delay(self, command, delay=None):
        """Send command with appropriate delay for connection type"""
        self.send_command(command)
        if delay is None:
            delay = 0.1 if self.is_ethernet_connection() else 0.01
        if delay > 0:
            time.sleep(delay)
        
    def measure_voltage(self) -> Optional[float]:
        """Read actual output voltage"""
        try:
            cmd = self.device_spec.default_commands['measure_voltage']
            response = self.query_command(cmd)
            return float(response)
        except Exception:
            return None
        
    def measure_current(self) -> Optional[float]:
        """Read actual output current"""
        try:
            cmd = self.device_spec.default_commands['measure_current']
            response = self.query_command(cmd)
            return float(response)
        except Exception:
            return None
    
    def measure_voltage_current_combined(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Combined voltage/current measurement using reference script pattern
        Returns (voltage, current) tuple
        """
        try:
            # Use reference script's approach - combined query
            meas = self.query_command(self.device_spec.default_commands['measure_combined']).strip()
            parts = [x.strip() for x in meas.split(',')]
            
            if len(parts) >= 2:
                # Parse based on reference script pattern
                measured_i = float(parts[0].replace('A','').replace('V','').strip())
                measured_v = float(parts[1].replace('A','').replace('V','').strip())
                return measured_v, measured_i
            else:
                # Single value response - fallback to separate queries
                if 'A' in meas:
                    measured_i = float(meas.replace('A','').replace('V','').strip())
                    v_resp = self.query_command(self.device_spec.default_commands['measure_voltage']).strip()
                    measured_v = float(v_resp.replace('A','').replace('V','').strip())
                else:
                    measured_v = float(meas.replace('A','').replace('V','').strip())
                    i_resp = self.query_command(self.device_spec.default_commands['measure_current']).strip()
                    measured_i = float(i_resp.replace('A','').replace('V','').strip())
                return measured_v, measured_i
                
        except Exception as e:
            print(f"Combined measurement failed: {e}")
            # Fallback to separate measurements
            try:
                voltage = self.measure_voltage()
                current = self.measure_current()
                return voltage, current
            except Exception:
                return None, None
    
    def measure_battery_data_buffer(self) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Get last voltage, current and relative time from device buffer
        Based on reference script pattern
        Returns (voltage, current, rel_time) tuple
        """
        is_ethernet = False
        try:
            # Store original timeout - handle both socket and VISA connections
            is_ethernet = self.is_ethernet_connection()
            if is_ethernet:
                original_timeout = getattr(self.interface.connection, 'timeout', None)
                if hasattr(self.interface.connection, 'settimeout'):
                    self.interface.connection.settimeout(15.0)  # 15 second timeout for Ethernet
                time.sleep(0.1)  # Delay for ethernet
            else:
                original_timeout = getattr(self.interface.connection, 'timeout', 5000)
                if hasattr(self.interface.connection, 'timeout'):
                    self.interface.connection.timeout = 5000  # 5 second timeout for USB
            
            # Try buffer method first
            buf = self.query_command(self.device_spec.default_commands['battery_data_buffer'])
            
            if buf and len(buf.split(',')) >= 3:
                vals = list(map(float, buf.split(',')[-3:]))
                # Restore original timeout
                if is_ethernet and hasattr(self.interface.connection, 'settimeout'):
                    self.interface.connection.settimeout(original_timeout)
                elif hasattr(self.interface.connection, 'timeout'):
                    self.interface.connection.timeout = original_timeout
                return vals[0], vals[1], vals[2]
            
            # If buffer fails, try MEAS commands (work in Battery Test mode)
            # In Battery Test mode, :BATT:VOLT? doesn't work, use :MEAS:VOLT? instead
            for retry in range(3):  # Fewer retries for MEAS commands
                try:
                    if is_ethernet:
                        time.sleep(0.2)  # Longer delay for ethernet
                    
                    # Use MEAS commands which work in Battery Test mode
                    volt_response = self.query_command(':MEAS:VOLT?')
                    if is_ethernet:
                        time.sleep(0.1)  # Additional delay between commands
                    curr_response = self.query_command(':MEAS:CURR?')
                    
                    if volt_response and curr_response:
                        try:
                            voltage = float(volt_response.strip())
                            current = float(curr_response.strip())
                            rel_time = time.time()  # Current time as fallback
                            # Restore original timeout
                            if is_ethernet and hasattr(self.interface.connection, 'settimeout'):
                                self.interface.connection.settimeout(original_timeout)
                            elif hasattr(self.interface.connection, 'timeout'):
                                self.interface.connection.timeout = original_timeout
                            return voltage, current, rel_time
                        except ValueError as ve:
                            print(f'Could not parse measurement data: V="{volt_response}" I="{curr_response}"')
                except Exception as e:
                    if retry < 4:
                        wait_time = 0.5 * (retry + 1)  # Progressive backoff
                        print(f'Measurement retry {retry + 1}/5 failed: {e}, waiting {wait_time}s')
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f'Direct measurement failed after 5 retries: {e}')
            
            # Restore original timeout
            if is_ethernet and hasattr(self.interface.connection, 'settimeout'):
                self.interface.connection.settimeout(original_timeout)
            elif hasattr(self.interface.connection, 'timeout'):
                self.interface.connection.timeout = original_timeout
            return None, None, None
            
        except Exception as e:
            print(f'Exception in measure_battery_data_buffer(): {e}')
            try:
                if is_ethernet and hasattr(self.interface.connection, 'settimeout'):
                    self.interface.connection.settimeout(original_timeout)
                elif hasattr(self.interface.connection, 'timeout'):
                    self.interface.connection.timeout = original_timeout
            except Exception:
                pass
            return None, None, None
            
    def measure_power(self) -> Optional[float]:
        """Calculate power from voltage and current"""
        try:
            voltage, current = self.measure_voltage_current_combined()
            if voltage is not None and current is not None:
                return voltage * current
        except Exception:
            pass
        return None
    
    def get_measurements(self) -> 'MeasurementData':
        """
        Get all measurements as structured data - enhanced for mode-dependent operation
        """
        from datetime import datetime
        from models.device_config import MeasurementData
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        try:
            # Use our enhanced measurement functions
            if self.current_mode == 'test':
                # In Battery Test mode, try buffer method first
                voltage, current, _ = self.measure_battery_data_buffer()
                if voltage is None or current is None:
                    # Fallback to combined measurement
                    voltage, current = self.measure_voltage_current_combined()
            else:
                # In Power Supply mode, use combined measurement
                voltage, current = self.measure_voltage_current_combined()
            
            # Calculate power if we have both values
            power = None
            if voltage is not None and current is not None:
                power = voltage * current
                
            return MeasurementData(
                timestamp=timestamp,
                voltage=voltage,
                current=current, 
                power=power
            )
            
        except Exception as e:
            print(f"Error getting measurements: {e}")
            # Return empty measurement data on error
            return MeasurementData(
                timestamp=timestamp,
                voltage=None,
                current=None,
                power=None
            )
        
    def run_pulse_test(self, pulses: int = 5,
                      pulse_time: float = 60.0,
                      rest_time: float = 60.0,
                      i_pulse: float = 1.0,
                      i_rest: float = 0.0001,
                      sample_interval: float = 0.5) -> Tuple[str, str]:
        """
        Run battery pulse test to measure EVOC and ESR characteristics.

        **IMPORTANT - Connection Requirement:**
        This function REQUIRES a USB connection. Ethernet connections are NOT supported
        due to instrument limitations with buffered data retrieval over TCP sockets.
        The function will raise an exception if called over Ethernet.

        **Platform Compatibility:**
        - Linux: Fully supported (USB/GPIB via VISA)
        - Windows: Fully supported (USB/GPIB via NI-VISA driver)
        - Connection: USB or GPIB ONLY (NOT Ethernet)

        Args:
            pulses: Number of pulse cycles (1-100)
            pulse_time: Duration of each pulse in seconds (1-300)
            rest_time: Duration of rest period in seconds (1-300)
            i_pulse: Pulse current in amperes (0.001 - max_current)
            i_rest: Rest current in amperes (typically very small)
            sample_interval: Data sampling interval in seconds

        Returns:
            tuple: (pulse_data_file, rest_data_file) - Paths to CSV files

        Raises:
            Exception: If device not connected, busy, or using Ethernet connection
            ValueError: If parameters out of valid range

        Note:
            Data is saved to ./logs/pulse_bt_YYYYMMDD_HHMMSS.csv and
            ./logs/rest_evoc_YYYYMMDD_HHMMSS.csv
        """
        if not self.connected:
            raise Exception("Device not connected")
        
        # Check for Ethernet connection and prevent test run
        if self.is_ethernet_connection():
            raise Exception(
                "Pulse test data logging is not supported over Ethernet due to instrument limitations. "
                "Please use a USB connection for this test."
            )
            
        if self.is_busy():
            raise Exception("Device is busy with another operation")
            
        # Set device as busy for pulse test
        self.set_busy(True)
        
        try:
            # Validate parameters
            if pulses < 1 or pulses > 100:
                raise ValueError("Pulses must be between 1 and 100")
            if pulse_time < 1 or pulse_time > 300:
                raise ValueError("Pulse time must be between 1 and 300 seconds")
            if rest_time < 1 or rest_time > 300:
                raise ValueError("Rest time must be between 1 and 300 seconds")
            if i_pulse < 0.001 or i_pulse > self.device_spec.max_current:
                raise ValueError(f"Pulse current must be between 0.001 and {self.device_spec.max_current}A")
            
            # Test parameters - simplified for Keithley 2281S Battery Test mode
            # Note: Keithley 2281S can only discharge at ~1A, no variable discharge current
            I_PULSE, I_REST = i_pulse, i_rest
            # Use same timing as working script for all connections
            STEP = 0.5
            EVOC_DLY = 0.05
            
            # Determine if ethernet connection
            is_ethernet = self.is_ethernet_connection()
            
            # Initialize device with ethernet-specific timeouts
            try:
                print("Initializing Keithley for pulse test...")
                print(f"Connection type: {'Ethernet' if is_ethernet else 'USB/GPIB'}")
                
                # Set timeout like working script (5 seconds = 5000ms)
                if is_ethernet and hasattr(self.interface.connection, 'settimeout'):
                    self.interface.connection.settimeout(5.0)  # 5 second timeout like working script
                    print("Set ethernet timeout to 5 seconds like working script")
                elif hasattr(self.interface.connection, 'timeout'):
                    self.interface.connection.timeout = 5000  # 5000ms for VISA connections
                    print("Set VISA timeout to 5000ms like working script")
                
                # Exact initialization sequence from working script
                self.send_command('*CLS')
                self.send_command('SYST:REM')
                self.send_command(':FUNC TEST')
                self.send_command(':BATT:TEST:MODE DIS')
                self.send_command(f':BATT:TEST:SENS:SAMP:INT {sample_interval}')
                self.send_command(f':BATT:TEST:SENS:EVOC:DELA {EVOC_DLY}')
                self.send_command(':FORM:UNITS OFF')
                self.send_command(':SYST:AZER OFF')
                
                # Data logger setup exactly like working script
                self.send_command(':BATT:DATA:CLE')
                self.send_command(':BATT:DATA:STAT ON')
                self.send_command(':BATT:TEST:EXEC STAR')
                
                # Add delay like working script has between init and pulse start
                time.sleep(1.0)  # Allow data logger to initialize properly
                
                # Check if data logging is active (debug for ethernet)
                if is_ethernet:
                    try:
                        data_status = self.query_command(':BATT:DATA:STAT?')
                        print(f'DEBUG: Data logging status: {data_status}')
                    except Exception as e:
                        print(f'DEBUG: Could not query data status: {e}')
                
                print('DEBUG: Simple initialization completed')
                print("Device initialization complete")
                
            except Exception as e:
                raise Exception(f"Failed to initialize device for pulse test: {e}")
            
            # Create output files in logs directory
            logs_dir = Path('./logs')
            logs_dir.mkdir(exist_ok=True)

            stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            pulse_file = logs_dir / f'pulse_bt_{stamp}.csv'
            rest_file = logs_dir / f'rest_evoc_{stamp}.csv'

            print(f"Creating output files in logs directory: {pulse_file.name}, {rest_file.name}")
            
            try:
                with open(pulse_file, 'w', newline='') as fpulse, \
                     open(rest_file, 'w', newline='') as frest:
                    
                    wp = csv.writer(fpulse)
                    wr = csv.writer(frest)
                    wp.writerow(['t_rel_s', 'volt_v', 'curr_a'])
                    wr.writerow(['t_rel_s', 'voc_v', 'esr_ohm'])
                    fpulse.flush()
                    frest.flush()
                    
                    t0 = time.time()
                    print(f"Starting pulse test: {pulses} pulses...")
                    
                    def last_vi():
                        """Simple buffer read exactly like working script - works for both USB and Ethernet"""
                        try:
                            buf = self.query_command(':BATT:DATA:DATA? "VOLT,CURR,REL"')
                            # Enhanced debug output for ethernet connections
                            if is_ethernet and (cyc <= 2):  # Show debug for first two pulses
                                print(f'[DEBUG] Buffer response length: {len(buf) if buf else 0}')
                                if buf:
                                    print(f'[DEBUG] Buffer response: "{buf[:200]}..."' if len(buf) > 200 else f'[DEBUG] Buffer response: "{buf}"')
                                else:
                                    print('[DEBUG] Buffer response: empty string')
                            
                            if not buf or buf.strip() == '':  # empty string or whitespace only
                                return None, None, None
                                
                            # Split and get last three values
                            parts = buf.split(',')
                            if len(parts) < 3:
                                if is_ethernet and (cyc <= 2):
                                    print(f'[DEBUG] Not enough data parts: {len(parts)}')
                                return None, None, None
                                
                            vals = list(map(float, parts[-3:]))  # last three numbers
                            v, i, rel = vals
                            return v, i, rel
                        except Exception as e:
                            if is_ethernet and (cyc <= 2):  # Show debug for first two pulses
                                print(f'[DEBUG] last_vi() exception: {e}')
                            return None, None, None
                    
                    for cyc in range(1, pulses + 1):
                        print(f"Executing pulse {cyc}/{pulses}...")
                        
                        # PULSE - Direct on/off for Keithley 2281S Battery Test mode
                        # Set discharge current and turn on output
                        self.send_command(f':BATT:TEST:CURR:LIM:SOUR {I_PULSE}')
                        self.send_command(':BATT:OUTP ON')
                        
                        # Give buffer time to start collecting data after output is turned on
                        time.sleep(0.5)
                        
                        print(f'>>> {cyc}. PULSE — {pulse_time}s @ ~1A (Battery Test mode)')
                        end = time.time() + pulse_time
                        while time.time() < end:
                            v, i, rel = last_vi()
                            if v is not None: 
                                wp.writerow([f'{rel:.3f}', f'{v:.6f}', f'{i:.6f}'])
                                fpulse.flush()
                            time.sleep(STEP)
                        
                        # REST + EVOC exactly like working script
                        self.send_command(':BATT:OUTP OFF')
                        self.send_command(f':BATT:TEST:CURR:LIM:SOUR {I_REST}')
                        print(f'>>> Dinlenme — {rest_time}s')
                        end = time.time() + rest_time
                        while time.time() < end:
                            try:
                                evoc_response = self.query_command(':BATT:TEST:MEAS:EVOC?')
                                esr, voc = map(float, evoc_response.split(','))
                                wr.writerow([f'{time.time()-t0:.3f}', f'{voc:.6f}', f'{esr:.6f}'])
                                frest.flush()
                            except Exception as e:
                                print(f'EVOC measurement failed: {e}')
                            time.sleep(STEP)
                    
                    print("Pulse test completed successfully")
                    print(f"Data saved to: {pulse_file}")
                    print(f"Data saved to: {rest_file}")

                    # Return file paths (as strings)
                    return (str(pulse_file), str(rest_file))
                    
            except Exception as e:
                # Clean up on error - turn off both outputs for safety
                try:
                    self.send_command(':OUTP OFF')  # Power Supply output
                except Exception:
                    pass
                try:
                    self.send_command(':BATT:OUTP OFF')  # Battery Test output
                except Exception:
                    pass
                raise Exception(f"Pulse test execution failed: {e}")
                
        finally:
            # Always clear busy state
            self.set_busy(False)
            
            # Clean up device state - turn off both outputs for safety
            try:
                self.send_command(':OUTP OFF')  # Power Supply output
            except Exception:
                pass
            try:
                self.send_command(':BATT:OUTP OFF')  # Battery Test output
            except Exception:
                pass
                
    def run_battery_model_test(self,
                          discharge_voltage: float = 3.0,
                          discharge_current_end: float = 0.4,
                          charge_vfull: float = 4.20,
                          charge_ilimit: float = 1.00,
                          charge_current_end: float = 0.05,
                          esr_interval: int = 30,
                          model_slot: int = 4,
                          v_min: float = 2.5,
                          v_max: float = 4.2,
                          export_csv: bool = True) -> dict:
        """
        Run complete battery model generation test

        This function follows the procedure from Keithley 2281S manual.
        It will wait indefinitely until discharge and charge phases complete.
        Total duration can be several hours depending on battery capacity.

        Args:
            discharge_voltage: End voltage for discharge (V)
            discharge_current_end: End current for discharge (A)
            charge_vfull: Full charge voltage (V)
            charge_ilimit: Charge current limit (A)
            esr_interval: ESR measurement interval (s)
            model_slot: Internal memory slot (1-9)
            v_min: Model voltage range minimum
            v_max: Model voltage range maximum
            export_csv: Whether to export model to CSV

        Returns:
            Dictionary with test results and file paths

        Note:
            No timeout limits - test will run until battery reaches end conditions.
            Progress is displayed every 30 seconds.
        """
        if not self.connected:
            raise Exception("Device not connected")
        
        if self.is_busy():
            raise Exception("Device is busy with another operation")
            
        # Validate parameters
        if discharge_voltage < 2.0 or discharge_voltage > 4.5:
            raise ValueError("Discharge voltage must be between 2.0 and 4.5V")
        if discharge_current_end < 0.1 or discharge_current_end > 2.0:
            raise ValueError("Discharge end current must be between 0.1 and 2.0A")
        if charge_vfull < 3.0 or charge_vfull > 4.5:
            raise ValueError("Charge voltage must be between 3.0 and 4.5V")
        if charge_ilimit < 0.1 or charge_ilimit > self.device_spec.max_current:
            raise ValueError(f"Charge current must be between 0.1 and {self.device_spec.max_current}A")
        if model_slot < 1 or model_slot > 9:
            raise ValueError("Model slot must be between 1 and 9")
        if charge_current_end < 0.01 or charge_current_end > charge_ilimit:
            raise ValueError(f"Charge end current must be between 0.01A and {charge_ilimit}A (current limit)")
        if esr_interval < 1 or esr_interval > 300:
            raise ValueError("ESR interval must be between 1 and 300 seconds")
            
        # Delegate to modular test runner (replaces old inline implementation)
        return self._battery_model.run(
            discharge_voltage=discharge_voltage,
            discharge_current_end=discharge_current_end,
            charge_vfull=charge_vfull,
            charge_ilimit=charge_ilimit,
            charge_current_end=charge_current_end,
            esr_interval=esr_interval,
            model_slot=model_slot,
            v_min=v_min,
            v_max=v_max,
            export_csv=export_csv
        )
    
    def load_current_profile(self, csv_path: str):
        """
        Load a current profile from CSV or Excel file and calculate segment durations
        Supports: .csv, .xlsx

        Returns:
            pandas.DataFrame or None
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas paketi gerekli: pip install pandas")

        print(f"Loading profile from: {csv_path}")
        try:
            # Check if file exists
            if not Path(csv_path).exists():
                print(f"Profile file not found: {csv_path}")
                return None
                
            start_time = time.time()
            
            # Read file based on extension (optimized)
            if csv_path.endswith('.xlsx') or csv_path.endswith('.xls'):
                try:
                    import openpyxl  # Lazy import
                    df = pd.read_excel(csv_path, engine='openpyxl')
                    print(f"Excel loaded in {time.time() - start_time:.2f}s with columns: {list(df.columns)}")
                except ImportError:
                    raise Exception("Excel support requires openpyxl. Install: pip install openpyxl")
            else:
                df = pd.read_csv(csv_path)
                print(f"CSV loaded in {time.time() - start_time:.2f}s with columns: {list(df.columns)}")
            
            # Check required columns
            if 'time_s' not in df.columns or 'current_a' not in df.columns:
                print(f"Error: CSV must have 'time_s' and 'current_a' columns. Found: {list(df.columns)}")
                return None
            
            # Remove empty rows and clean data
            df = df.dropna(subset=['time_s', 'current_a'])
            if len(df) == 0:
                print("Error: No valid data rows found in CSV")
                return None
                
            # Sort by time to ensure proper order
            df = df.sort_values('time_s').reset_index(drop=True)
            
            # Validate monotonic time values
            if len(df) > 1:
                time_diffs = df['time_s'].diff()
                if (time_diffs[1:] < 0).any():
                    print("Warning: Non-monotonic time values detected after sorting. Check your CSV file.")
                if (time_diffs[1:] == 0).any():
                    print("Warning: Duplicate time values detected. This may cause issues.")

            # Calculate durations. The time in the CSV is the START time of the segment.
            # Duration = next_time - current_time
            if len(df) > 1:
                # For all rows except the last: duration = next time - current time
                df['duration_s'] = df['time_s'].shift(-1) - df['time_s']
            
                # For the last row, use average duration of previous segments as estimate
                avg_duration = df['duration_s'][:-1].mean()
                if pd.notna(avg_duration) and avg_duration > 0:
                    df.loc[df.index[-1], 'duration_s'] = avg_duration
                    print(f"Last segment duration set to average: {avg_duration:.1f}s")
                else:
                    df.loc[df.index[-1], 'duration_s'] = 10.0
                    print("Last segment duration set to default: 10.0s")
            elif len(df) == 1:
                df.loc[df.index[0], 'duration_s'] = 10.0  # Default 10s for single point profile
                print("Single-point profile: duration set to 10.0s")

            # Validate all durations are positive
            negative_durations = df[df['duration_s'] <= 0]
            if len(negative_durations) > 0:
                print(f"Warning: {len(negative_durations)} negative/zero durations found, setting to 10.0s")
            df.loc[df['duration_s'] <= 0, 'duration_s'] = 10.0
            
            print(f"Profile loaded successfully: {len(df)} segments")
            print(f"Time range: {df['time_s'].min():.1f}s to {df['time_s'].max():.1f}s")
            print(f"Current range: {df['current_a'].min():.3f}A to {df['current_a'].max():.3f}A")
            return df
            
        except FileNotFoundError:
            print(f"Profile file not found: {csv_path}")
            return None
        except pd.errors.EmptyDataError:
            print("Error: CSV file is empty")
            return None
        except pd.errors.ParserError as e:
            print(f"Error parsing CSV file: {e}")
            return None
        except Exception as e:
            print(f"Failed to load profile: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_charge_segments(self, segments: List[Dict], step_offset: int = 0, 
                           charge_voltage: float = 4.2, protection_voltage: float = 4.3,
                           sample_period: float = 1.0) -> bool:
        """
        Execute charging segments in Power Supply mode
        Based on reference script pattern
        
        Args:
            segments: List of segments to execute
            step_offset: Offset for segment numbering
            charge_voltage: Charging voltage limit
            protection_voltage: Over-voltage protection limit
            sample_period: Measurement interval in seconds (default: 1.0s)
        """
        if not self.connect_and_prep():
            return False

        if not self.switch_to_power_supply_mode():
            print("Failed to switch to Power Supply mode, skipping charge segments")
            return False

        print(f"--- Executing Batch of {len(segments)} CHARGE segments (sampling every {sample_period}s) ---")
        try:
            # Configure voltage settings for Power Supply mode
            self.send_command(f':SOUR:VOLT {charge_voltage}')
            self.send_command(f':SOUR:VOLT:PROT {protection_voltage}')
            print(f"Configured charge voltage: {charge_voltage}V, Protection: {protection_voltage}V")

            for i, segment in enumerate(segments):
                current = segment['current_a']
                duration = segment['duration_s']
                step_no = step_offset + i + 1
                print(f"  -> Segment {step_no}: Setting current limit {current:.3f}A for {duration:.2f}s")
                
                # Set current limit for charging
                self.send_command(f':SOUR:CURR {abs(current)}')  # Use positive current for charging
                
                # Turn on output for this segment
                if i == 0:
                    self.send_command(':OUTP ON')
                    print(f"Output ON for charging")
                
                # Take measurements at regular intervals during the segment
                elapsed_in_segment = 0.0
                measurement_count = 0
                while elapsed_in_segment < duration:
                    try:
                        measured_v, measured_i = self.measure_voltage_current_combined()
                        if measured_v is not None and measured_i is not None:
                            measurement_count += 1
                            if measurement_count == 1 or measurement_count % 5 == 0:  # Print every 5th measurement
                                print(f"    Measurement #{measurement_count}: V={measured_v:.3f}V, I={measured_i:.3f}A")
                            self.logger.log_segment(step_no, 'charge', current, measured_v, measured_i, 
                                                  self.logger.elapsed(), 'OK')
                        else:
                            print(f"    Measurement #{measurement_count + 1} failed: No data received")
                        
                    except Exception as e:
                        print(f"    Measurement failed: {e}")
                        self.logger.log_error(step_no, 'charge', str(e))
                    
                    # Sleep for sample period or remaining time, whichever is shorter
                    sleep_time = min(sample_period, duration - elapsed_in_segment)
                    time.sleep(sleep_time)
                    elapsed_in_segment += sleep_time
                
                print(f"    Segment {step_no} complete: {measurement_count} measurements taken")
                
        except Exception as e:
            print(f"ERROR during charge batch: {e}")
            return False
        finally:
            # Turn off both outputs for safety
            try:
                self.send_command(':OUTP OFF')  # Power Supply output (primary for charge)
                print("Power Supply output turned OFF after charge batch")
            except Exception:
                pass
            try:
                self.send_command(':BATT:OUTP OFF')  # Battery Test output (safety)
            except Exception:
                pass
        print("--- Charge batch finished ---")
        return True

    def run_discharge_segments(self, segments: List[Dict], step_offset: int = 0, 
                             discharge_current: float = 1.0, sample_period: float = 1.0) -> bool:
        """
        Execute discharge segments in Battery Test mode
        Based on reference script pattern
        
        Args:
            segments: List of segments to execute
            step_offset: Offset for segment numbering
            discharge_current: Constant discharge current in amperes
            sample_period: Measurement interval in seconds (default: 1.0s)
        """
        if not self.connect_and_prep():
            return False

        if not self.switch_to_battery_test_mode():
            print("Failed to switch to Battery Test mode, skipping discharge segments")
            return False

        print(f"--- Executing Batch of {len(segments)} DISCHARGE segments (sampling every {sample_period}s) ---")
        try:
            # Configure battery test for discharge (same as reference script)
            self.send_command(':BATT:TEST:MODE DIS')
            self.send_command(f':BATT:TEST:CURR:LIM:SOUR {discharge_current}')
            self.send_command(':BATT:OUTP ON')
            print(f"Output ON. Applying constant {discharge_current}A discharge...")

            # Calculate total discharge time
            total_duration = sum(segment['duration_s'] for segment in segments)
            print(f"Total discharge time: {total_duration:.1f}s")

            for i, segment in enumerate(segments):
                duration = segment['duration_s']
                step_no = step_offset + i + 1
                print(f"  -> Segment {step_no}: Discharging for {duration:.2f}s")

                # Take measurements at regular intervals during the segment
                elapsed_in_segment = 0.0
                measurement_count = 0
                
                # Initial settling delay
                time.sleep(0.3)
                
                while elapsed_in_segment < duration:
                    try:
                        measured_v, measured_i, _ = self.measure_battery_data_buffer()
                        if measured_v is not None and measured_i is not None:
                            measurement_count += 1
                            if measurement_count == 1 or measurement_count % 5 == 0:  # Print every 5th measurement
                                print(f"    Measurement #{measurement_count}: V={measured_v:.3f}V, I={measured_i:.4f}A")
                            # Log with measured current
                            self.logger.log_segment(step_no, 'discharge', discharge_current,
                                                  measured_v, measured_i, self.logger.elapsed(), 'OK')
                        else:
                            print(f"    Measurement #{measurement_count + 1} failed: No data received")
                            self.logger.log_segment(step_no, 'discharge', discharge_current,
                                                  None, None, self.logger.elapsed(), 'NO_MEASUREMENT')
                    except Exception as e:
                        print(f"    Measurement failed: {e}")
                        self.logger.log_segment(step_no, 'discharge', discharge_current,
                                              None, None, self.logger.elapsed(), f'MEAS_ERROR: {e}')

                    # Sleep for sample period or remaining time, whichever is shorter
                    sleep_time = min(sample_period, duration - elapsed_in_segment)
                    time.sleep(sleep_time)
                    elapsed_in_segment += sleep_time
                
                print(f"    Segment {step_no} complete: {measurement_count} measurements taken")
                
            # Take one final measurement after all segments complete
            print("Taking final measurement after discharge batch...")
            try:
                time.sleep(0.5)
                measured_v, measured_i, rel_time = self.measure_battery_data_buffer()
                if measured_v is not None and measured_i is not None:
                    print(f"Final measurement: V={measured_v:.3f}V, I={measured_i:.3f}A")
                    # Log final measurement
                    final_step = step_offset + len(segments)
                    self.logger.log_segment(final_step, 'discharge_final', discharge_current, 
                                          measured_v, measured_i, self.logger.elapsed(), 'FINAL')
                else:
                    print("Final measurement failed - continuing anyway")
            except Exception as e:
                print(f"Final measurement failed: {e} - continuing anyway")
                
        except Exception as e:
            print(f"ERROR during discharge batch: {e}")
            return False
        finally:
            # Turn off both outputs for safety
            try:
                self.send_command(':BATT:OUTP OFF')  # Battery Test output (primary for discharge)
                print("Battery Test output turned OFF after discharge batch")
            except Exception:
                pass
            try:
                self.send_command(':OUTP OFF')  # Power Supply output (safety)
            except Exception:
                pass
        print("--- Discharge batch finished ---")
        return True
    
    def run_current_profile(self, profile_path: str, discharge_current: float = 1.0,
                           charge_voltage: float = 4.2, protection_voltage: float = 4.3,
                           sample_period: float = 1.0, output_format: str = 'csv') -> Optional[str]:
        """
        Execute current profile with automatic mode switching between charge and discharge.

        **IMPORTANT - Connection Requirement:**
        This function REQUIRES a USB connection. Ethernet connections are NOT supported
        due to discharge measurement limitations with buffered data over TCP sockets.
        The function will raise an exception if called over Ethernet.

        **Platform Compatibility:**
        - Linux: Fully supported (USB/GPIB via VISA)
        - Windows: Fully supported (USB/GPIB via NI-VISA driver)
        - Connection: USB or GPIB ONLY (NOT Ethernet)

        **How it Works:**
        - Reads current profile from CSV (columns: time_s, current_a)
        - Automatically switches between Power Supply mode (charge) and Battery Test mode (discharge)
        - Positive currents: Power Supply mode at specified voltage
        - Negative currents: Battery Test mode at specified discharge current
        - Takes measurements at regular intervals (sample_period) during execution
        - Logs all measurements to CSV file

        Args:
            profile_path: Path to CSV profile file with 'time_s' and 'current_a' columns
            discharge_current: Constant discharge current in amperes (for negative segments)
            charge_voltage: Charging voltage limit in volts
            protection_voltage: Over-voltage protection limit in volts
            sample_period: Measurement interval in seconds (default: 1.0s)

        Returns:
            Path to log file if successful, None if failed

        Raises:
            Exception: If device not connected, busy, or using Ethernet connection
            Exception: If profile file cannot be loaded

        Note:
            During execution, the device is marked as BUSY and monitoring is disabled.
            Log file is saved to ./logs/keithley_log_YYYYMMDD_HHMMSS.csv
        """
        # Delegate to modular test runner
        return self._profile_runner.run(
            profile_path=profile_path,
            discharge_current=discharge_current,
            charge_voltage=charge_voltage,
            protection_voltage=protection_voltage,
            sample_period=sample_period,
            output_format=output_format
        )
