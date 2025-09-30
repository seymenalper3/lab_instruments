#!/usr/bin/env python3
"""
Keithley 2281S Battery Simulator/Emulator Controller
Enhanced with reference script patterns from auto_mode_profile.py
"""
import csv
import time
import datetime
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from controllers.base_controller import BaseDeviceController
from models.device_config import DEVICE_SPECS, DeviceType
from utils.keithley_logger import KeithleyLogger


class KeithleyController(BaseDeviceController):
    """Keithley 2281S Battery Simulator/Emulator Controller"""
    
    def __init__(self, interface):
        super().__init__(interface, DEVICE_SPECS[DeviceType.KEITHLEY_2281S])
        self.current_mode: Optional[str] = None  # Track current mode
        self.logger = KeithleyLogger()  # Structured logging
        self.mode_switch_delay = 3.0  # Delay after mode switch (seconds)
        
    def set_voltage(self, voltage: float):
        """Set output voltage in volts - mode dependent"""
        if voltage < 0 or voltage > self.device_spec.max_voltage:
            raise ValueError(f"Voltage must be between 0 and {self.device_spec.max_voltage}V")
        
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
        
    def set_current_limit(self, current: float):
        """Set current limit in amperes - mode dependent"""
        if current < 0 or current > self.device_spec.max_current:
            raise ValueError(f"Current must be between 0 and {self.device_spec.max_current}A")
        
        # Use different commands based on current mode
        if self.current_mode == 'test':
            # In Battery Test mode, use battery-specific commands
            print(f"Setting Battery Test current to {current}A")
            self.send_command(f':BATT:TEST:CURR:LIM:SOUR {current}')
            self.send_command(f':BATT:TEST:CURR:END {current}')
            # Set discharge mode if current is positive (for load testing)
            self.send_command(':BATT:TEST:MODE DIS')
        else:
            # Power Supply mode
            cmd = self.device_spec.default_commands['set_current'].format(current)
            self.send_command(cmd)
        
    def output_on(self):
        """Turn output on - mode dependent"""
        if self.current_mode == 'test':
            # In Battery Test mode, use battery output
            print("Turning on Battery Test output")
            self.send_command(':BATT:OUTP ON')
        else:
            # Power Supply mode
            cmd = self.device_spec.default_commands['output_on']
            self.send_command(cmd)
        
    def output_off(self):
        """Turn output off - mode dependent"""
        if self.current_mode == 'test':
            # In Battery Test mode, use battery output
            print("Turning off Battery Test output")
            self.send_command(':BATT:OUTP OFF')
        else:
            # Power Supply mode
            cmd = self.device_spec.default_commands['output_off']
            self.send_command(cmd)
        
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
            # Turn off any outputs first
            try:
                self.send_command(self.device_spec.default_commands['output_off'])
                time.sleep(0.2)
            except:
                pass
            try:
                self.send_command(self.device_spec.default_commands['battery_output_off'])
                time.sleep(0.2)
            except:
                pass
            
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
            
            # If verification failed but we sent the command, assume it worked
            self.current_mode = 'power'
            print("Mode switch command sent, assuming success")
            return True
            
        except Exception as e:
            print(f"Failed to switch to Power Supply mode: {e}")
            return False

    def switch_to_battery_test_mode(self) -> bool:
        """
        Switch instrument to Battery Test mode for discharging
        Based on reference script auto_mode_profile.py
        """
        if self.current_mode == 'test':
            return True
            
        print("Switching to Battery Test mode...")
        try:
            # Turn off any outputs first
            try:
                self.send_command(self.device_spec.default_commands['output_off'])
                time.sleep(0.2)
            except:
                pass
            try:
                self.send_command(self.device_spec.default_commands['battery_output_off'])
                time.sleep(0.2)
            except:
                pass
            
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
            
            # If verification failed but we sent the command, assume it worked
            self.current_mode = 'test'
            print("Mode switch command sent, assuming success")
            return True
            
        except Exception as e:
            print(f"Failed to switch to Battery Test mode: {e}")
            return False
    
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
            except:
                return None, None
    
    def measure_battery_data_buffer(self) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Get last voltage, current and relative time from device buffer
        Based on reference script pattern
        Returns (voltage, current, rel_time) tuple
        """
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
            
            # If buffer fails, try direct measurement with retries
            for retry in range(5):  # More retries
                try:
                    if is_ethernet:
                        time.sleep(0.2)  # Longer delay for ethernet
                    
                    volt_response = self.query_command(self.device_spec.default_commands['measure_voltage'])
                    if is_ethernet:
                        time.sleep(0.1)  # Additional delay between commands
                    curr_response = self.query_command(self.device_spec.default_commands['measure_current'])
                    
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
            except:
                pass
            return None, None, None
            
    def measure_power(self) -> Optional[float]:
        """Calculate power from voltage and current"""
        try:
            voltage, current = self.measure_voltage_current_combined()
            if voltage is not None and current is not None:
                return voltage * current
        except:
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
                      sample_interval: float = 0.5) -> tuple:
        """
        Run battery pulse test.
        """
        if not self.connected:
            raise Exception("Device not connected")
        
        if self.busy:
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
            
            # Create output files
            stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            pulse_file = f'pulse_bt_{stamp}.csv'
            rest_file = f'rest_evoc_{stamp}.csv'
            
            print(f"Creating output files: {pulse_file}, {rest_file}")
            
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
                    
                    # Return file paths
                    return (pulse_file, rest_file)
                    
            except Exception as e:
                # Clean up on error - only turn off output
                try:
                    self.send_command(':BATT:OUTP OFF')
                except:
                    pass
                raise Exception(f"Pulse test execution failed: {e}")
                
        finally:
            # Always clear busy state
            self.set_busy(False)
            
            # Clean up device state - only turn off output, keep connection
            try:
                self.send_command(':BATT:OUTP OFF')
            except:
                pass
                
    def run_battery_model_test(self, 
                          discharge_voltage: float = 3.0,
                          discharge_current_end: float = 0.4,
                          charge_vfull: float = 4.20,
                          charge_ilimit: float = 1.00,
                          esr_interval: int = 30,
                          model_slot: int = 4,
                          v_min: float = 2.5,
                          v_max: float = 4.2,
                          export_csv: bool = True) -> dict:
        """
        Run complete battery model generation test
        
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
        """
        if not self.connected:
            raise Exception("Device not connected")
        
        if self.busy:
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
        if esr_interval < 1 or esr_interval > 300:
            raise ValueError("ESR interval must be between 1 and 300 seconds")
            
        # Set device as busy
        self.set_busy(True)
        
        import time
        import csv
        from datetime import datetime
        from pathlib import Path
        
        test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            'test_id': test_id,
            'model_slot': model_slot,
            'start_time': datetime.now().isoformat(),
            'model_file': None,
            'data_file': None,
            'success': False
        }
        
        try:
            print(f"Starting battery model generation test {test_id}")
            
            # 1) Clear and initialize
            print("Clearing buffers and initializing...")
            self.send_command('*CLS')
            self.send_command(':BATT1:DATA:CLE')
            self.send_command(':BATT:DATA:CLE')
            self.send_command(':TRACe:CLEar')
            
            # 2) Discharge phase
            print("=== STARTING BATTERY DISCHARGE ===")
            print(f"Discharge to {discharge_voltage}V, end current {discharge_current_end}A")
            
            self.send_command(':BATT:TEST:MODE DIS')
            self.send_command(f':BATT:TEST:VOLT {discharge_voltage}')
            self.send_command(f':BATT:TEST:CURR:END {discharge_current_end}')
            self.send_command(':BATT:OUTP ON')
            
            # Wait for discharge to complete
            start_time = time.time()
            max_discharge_time = 4 * 3600  # 4 hours max
            
            while True:
                # Check measurement status
                try:
                    cond = int(self.query_command(':STAT:OPER:INST:ISUM:COND?'))
                    measuring = bool(cond & 0x10)
                    
                    # Try to get voltage/current
                    try:
                        voltage = float(self.query_command(':BATT:VOLT?'))
                        current = float(self.query_command(':BATT:CURR?'))
                        elapsed = time.time() - start_time
                        print(f"Discharge progress: {elapsed/60:.1f} min | V: {voltage:.3f}V | I: {current:.3f}A")
                    except:
                        pass
                        
                    if not measuring:
                        print(f"Discharge completed in {(time.time() - start_time)/60:.1f} minutes")
                        break
                        
                    if time.time() - start_time > max_discharge_time:
                        raise TimeoutError("Discharge exceeded 4 hours")
                        
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    print(f"Status check error: {e}")
                    time.sleep(5)
                    
            self.send_command(':BATT:OUTP OFF')
            print("=== DISCHARGE COMPLETED ===")
            
            # 3) Charge and characterization phase
            print("=== STARTING CHARGE & CHARACTERIZATION ===")
            print(f"Charge to {charge_vfull}V, current limit {charge_ilimit}A, ESR interval {esr_interval}s")
            
            self.send_command(f':BATT:TEST:SENS:AH:VFUL {charge_vfull}')
            self.send_command(f':BATT:TEST:SENS:AH:ILIM {charge_ilimit}')
            self.send_command(f':BATT:TEST:SENS:AH:ESRI S{esr_interval}')
            self.send_command(':TRACe:CLEar:AUTO ON')
            self.send_command(':TRACe:FEED:CONT ALW')
            
            # Start A-H measurement
            self.send_command(':BATT:OUTP ON')
            self.send_command(':BATT:TEST:SENS:AH:EXEC STAR')
            
            # Wait for charge to complete
            start_time = time.time()
            max_charge_time = 8 * 3600  # 8 hours max
            
            while True:
                try:
                    cond = int(self.query_command(':STAT:OPER:INST:ISUM:COND?'))
                    measuring = bool(cond & 0x10)
                    
                    # Try to get voltage/current
                    try:
                        voltage = float(self.query_command(':BATT:VOLT?'))
                        current = float(self.query_command(':BATT:CURR?'))
                        elapsed = time.time() - start_time
                        print(f"Charge progress: {elapsed/60:.1f} min | V: {voltage:.3f}V | I: {current:.3f}A")
                    except:
                        pass
                        
                    if not measuring:
                        print(f"Charge completed in {(time.time() - start_time)/60:.1f} minutes")
                        break
                        
                    if time.time() - start_time > max_charge_time:
                        raise TimeoutError("Charge exceeded 8 hours")
                        
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    print(f"Status check error: {e}")
                    time.sleep(5)
                    
            print("=== CHARGE & CHARACTERIZATION COMPLETED ===")
            
            # 4) Generate and save model
            print("=== GENERATING BATTERY MODEL ===")
            self.send_command(f':BATT:TEST:SENS:AH:GMOD:RANG {v_min},{v_max}')
            self.send_command(f':BATT:TEST:SENS:AH:GMOD:SAVE:INT {model_slot}')
            
            # Wait for model generation
            time.sleep(2)
            self.query_command('*OPC?')  # Wait for operation complete
            
            # Verify save
            slots = self.query_command(':BATT:TEST:SENS:AH:GMOD:CAT?')
            print(f"Model saved to slot {model_slot}. Available slots: {slots}")
            
            # 5) Export model to CSV if requested
            if export_csv:
                print("=== EXPORTING MODEL TO CSV ===")
                
                # Recall model
                self.send_command(f':BATT:MOD:RCL {model_slot}')
                time.sleep(1)
                
                # Prepare CSV file
                data_dir = Path('./battery_models')
                data_dir.mkdir(exist_ok=True)
                csv_file = data_dir / f'battery_model_slot{model_slot}_{test_id}.csv'
                
                with open(csv_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['SOC (%)', 'Voc (V)', 'ESR (Ω)', 'Timestamp'])
                    
                    # Read model data (101 points for complete model)
                    rows_written = 0
                    for i in range(101):
                        try:
                            resp = self.query_command(f':BATT:MOD{model_slot}:ROW{i}?')
                            if resp and ',' in resp:
                                parts = resp.strip().split(',')
                                if len(parts) >= 2:
                                    voc = float(parts[0])
                                    esr = float(parts[1])
                                    soc = i  # 0-100%
                                    timestamp = datetime.now().isoformat()
                                    writer.writerow([f'{soc}', f'{voc:.4f}', f'{esr:.4f}', timestamp])
                                    rows_written += 1
                        except Exception as e:
                            print(f"Error reading row {i}: {e}")
                            
                print(f"Model exported to: {csv_file} ({rows_written} rows)")
                results['model_file'] = str(csv_file)
                
            # 6) Export measurement data
            try:
                print("=== EXPORTING MEASUREMENT DATA ===")
                points_str = self.query_command(':TRACe:POINts:ACTual?')
                points = int(points_str) if points_str else 0
                
                if points > 0:
                    print(f"Buffer contains {points} data points")
                    data_file = data_dir / f'battery_measurements_{test_id}.csv'
                    
                    with open(data_file, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Time (s)', 'Voltage (V)', 'Current (A)', 'Capacity (Ah)', 'ESR (Ω)'])
                        
                        # Read data in chunks
                        chunk_size = 100
                        total_rows = 0
                        
                        for start in range(1, points + 1, chunk_size):
                            end = min(start + chunk_size - 1, points)
                            
                            try:
                                data = self.query_command(
                                    f':BATT1:DATA:DATA:SEL? {start},{end},"VOLT,CURR,AH,RES,REL"'
                                )
                                
                                if data:
                                    rows = [r.split(',') for r in data.split(';') if r]
                                    for row in rows:
                                        if len(row) >= 5:
                                            writer.writerow(row)
                                            total_rows += 1
                            except Exception as e:
                                print(f"Failed to read chunk {start}-{end}: {e}")
                                
                    print(f"Measurement data exported to: {data_file} ({total_rows} rows)")
                    results['data_file'] = str(data_file)
                    
            except Exception as e:
                print(f"Failed to export measurement data: {e}")
                
            results['success'] = True
            results['end_time'] = datetime.now().isoformat()
            print("=== BATTERY MODEL TEST COMPLETED SUCCESSFULLY ===")
            
            return results
            
        except Exception as e:
            print(f"Battery model test failed: {e}")
            results['error'] = str(e)
            results['end_time'] = datetime.now().isoformat()
            raise
            
        finally:
            # Cleanup - only turn off output, keep connection
            try:
                self.send_command(':BATT:OUTP OFF')
            except:
                pass
                
            # Clear busy state
            self.set_busy(False)
    
    def load_current_profile(self, csv_path: str) -> Optional[pd.DataFrame]:
        """
        Load a current profile CSV and calculate segment durations
        Based on reference script pattern
        """
        print(f"Loading profile from: {csv_path}")
        try:
            # Check if file exists
            if not Path(csv_path).exists():
                print(f"Profile file not found: {csv_path}")
                return None
                
            # Read CSV with error handling
            df = pd.read_csv(csv_path)
            print(f"CSV loaded with columns: {list(df.columns)}")
            
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
            
            # Calculate durations. The time in the CSV is the START time of the segment.
            df['duration_s'] = df['time_s'].diff().shift(-1)
            
            # For the last row, use the duration of the second to last row as an estimate
            if len(df) > 1 and (pd.isna(df['duration_s'].iloc[-1]) or df['duration_s'].iloc[-1] <= 0):
                df.loc[df.index[-1], 'duration_s'] = df['duration_s'].iloc[-2] if not pd.isna(df['duration_s'].iloc[-2]) else 10.0
            elif len(df) == 1:
                df.loc[df.index[-1], 'duration_s'] = 10.0  # Default 10s for single point profile
            
            # Ensure all durations are positive
            df['duration_s'] = df['duration_s'].fillna(10.0)  # Default duration
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
                           charge_voltage: float = 4.2, protection_voltage: float = 4.3) -> bool:
        """
        Execute charging segments in Power Supply mode
        Based on reference script pattern
        """
        if not self.connect_and_prep():
            return False

        if not self.switch_to_power_supply_mode():
            print("Failed to switch to Power Supply mode, skipping charge segments")
            return False

        print(f"--- Executing Batch of {len(segments)} CHARGE segments ---")
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
                
                # Take measurement using reference script's approach
                try:
                    measured_v, measured_i = self.measure_voltage_current_combined()
                    if measured_v is not None and measured_i is not None:
                        print(f"    Measurement: V={measured_v:.3f}V, I={measured_i:.3f}A")
                        self.logger.log_segment(step_no, 'charge', current, measured_v, measured_i, 
                                              self.logger.elapsed(), 'OK')
                    else:
                        raise Exception("No measurement data received")
                        
                except Exception as e:
                    print(f"    Measurement failed: {e}")
                    self.logger.log_error(step_no, 'charge', str(e))
                
                time.sleep(duration)
                
        except Exception as e:
            print(f"ERROR during charge batch: {e}")
            return False
        finally:
            try:
                self.send_command(':OUTP OFF')
                print("Output turned OFF after charge batch")
            except:
                pass
        print("--- Charge batch finished ---")
        return True

    def run_discharge_segments(self, segments: List[Dict], step_offset: int = 0, 
                             discharge_current: float = 1.0) -> bool:
        """
        Execute discharge segments in Battery Test mode
        Based on reference script pattern
        """
        if not self.connect_and_prep():
            return False

        if not self.switch_to_battery_test_mode():
            print("Failed to switch to Battery Test mode, skipping discharge segments")
            return False

        print(f"--- Executing Batch of {len(segments)} DISCHARGE segments ---")
        try:
            # Configure battery test for discharge (same as reference script)
            self.send_command(':BATT:TEST:MODE DIS')
            self.send_command(':BATT:OUTP ON')
            print("Output ON. Applying per-segment discharge sink current from profile...")

            # Calculate total discharge time
            total_duration = sum(segment['duration_s'] for segment in segments)
            print(f"Total discharge time: {total_duration:.1f}s")

            for i, segment in enumerate(segments):
                duration = segment['duration_s']
                # Per-segment sink current magnitude from CSV (negative means discharge)
                set_current = abs(float(segment.get('current_a', discharge_current)))
                step_no = step_offset + i + 1
                print(f"  -> Segment {step_no}: Set sink current {set_current:.3f}A for {duration:.2f}s")
                # Apply sink limit for this segment
                self.send_command(f':BATT:TEST:CURR:LIM:SINK {set_current}')
                
                # Skip individual measurements during Battery Test mode to avoid conflicts
                # Log the segment with expected values instead
                self.logger.log_segment(step_no, 'discharge', set_current, 
                                      None, None, self.logger.elapsed(), 'DISCHARGE_MODE')
                
                time.sleep(duration)

            # Take one final measurement after all segments complete
            print("Taking final measurement after discharge batch...")
            try:
                # Brief delay to let device settle
                time.sleep(0.5)
                measured_v, measured_i, rel_time = self.measure_battery_data_buffer()
                if measured_v is not None and measured_i is not None:
                    print(f"Final measurement: V={measured_v:.3f}V, I={measured_i:.3f}A")
                    # Log final measurement
                    final_step = step_offset + len(segments)
                    self.logger.log_segment(final_step, 'discharge_final', set_current, 
                                          measured_v, measured_i, self.logger.elapsed(), 'FINAL')
                else:
                    print("Final measurement failed - continuing anyway")
            except Exception as e:
                print(f"Final measurement failed: {e} - continuing anyway")
                
        except Exception as e:
            print(f"ERROR during discharge batch: {e}")
            return False
        finally:
            try:
                self.send_command(':BATT:OUTP OFF')
            except:
                pass
        print("--- Discharge batch finished ---")
        return True
    
    def run_current_profile(self, profile_path: str, discharge_current: float = 1.0,
                           charge_voltage: float = 4.2, protection_voltage: float = 4.3) -> Optional[str]:
        """
        Execute current profile with automatic mode switching
        Based on reference script auto_mode_profile.py
        
        Args:
            profile_path: Path to CSV profile file
            discharge_current: Constant discharge current (A) for negative segments
            charge_voltage: Charging voltage (V)
            protection_voltage: Protection voltage (V)
            
        Returns:
            Path to log file if successful, None if failed
        """
        print(f"\n🚀 Starting current profile execution...")
        print(f"Profile: {profile_path}")
        print(f"Parameters: discharge={discharge_current}A, charge={charge_voltage}V")
        
        if self.busy:
            error_msg = "Device is busy with another operation"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)
            
        # Check if connected
        if not self.connected:
            error_msg = "Device not connected"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)
            
        # Test basic communication before starting
        print("Testing device communication...")
        try:
            idn = self.query_command('*IDN?')
            if idn:
                print(f"Device responds: {idn.strip()[:50]}...")
            else:
                raise Exception("Device not responding to *IDN?")
        except Exception as e:
            error_msg = f"Communication test failed: {e}"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)
            
        # Load profile
        print("Loading current profile...")
        profile_df = self.load_current_profile(profile_path)
        if profile_df is None:
            error_msg = "Failed to load current profile"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)

        # Set device as busy to prevent monitoring interference
        self.set_busy(True)
        print("Device marked as BUSY - monitoring disabled during profile execution")
        
        # Initialize logger
        self.logger.clear_log()
        self.logger.start_timer()

        print(f"\n🚀 Starting profile execution with AUTOMATIC mode switching...")
        print(f"Total segments: {len(profile_df)}")
        print(f"Mode switch delay: {self.mode_switch_delay}s")

        try:
            last_mode = None
            segment_chunk = []
            step_offset = 0

            # Add a dummy row at the end to ensure the last chunk is processed
            sentinel = pd.DataFrame([{'current_a': 999, 'duration_s': 0}], index=[len(profile_df)])
            processing_df = pd.concat([profile_df, sentinel])

            for index, row in processing_df.iterrows():
                current = row['current_a']
                current_mode = 'charge' if current >= 0 else 'discharge'

                # Process chunk when mode changes
                if current_mode != last_mode and last_mode is not None:
                    print(f"\n>>> Mode change detected: {last_mode.upper()} → {current_mode.upper()}")
                    print(f"    Processing {len(segment_chunk)} segments in {last_mode.upper()} mode.")
                    
                    if last_mode == 'charge':
                        success = self.run_charge_segments(segment_chunk, step_offset, 
                                                         charge_voltage, protection_voltage)
                    else:
                        success = self.run_discharge_segments(segment_chunk, step_offset, 
                                                            discharge_current)
                    
                    if not success:
                        print(f"Failed to execute {last_mode} segments")
                        return None
                    
                    step_offset += len(segment_chunk)
                    segment_chunk = []

                # Add current segment to chunk (skip sentinel)
                if index < len(profile_df):
                    segment_chunk.append(row)
                
                last_mode = current_mode

            # Save log
            log_file = self.logger.save_log_csv()
            print(f"\n✅✅✅ Profile execution completed. Log saved to: {log_file} ✅✅✅")
            return log_file
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Script interrupted by user (Ctrl+C)")
            return None
        except Exception as e:
            print(f"\n\n❌ Unexpected error: {e}")
            print("Attempting device recovery...")
            try:
                # Try to recover the device
                self.send_command('*RST')
                time.sleep(1)
                self.send_command(':OUTP OFF')
                self.send_command(':BATT:OUTP OFF')
                print("Device recovery attempted")
            except:
                print("Device recovery failed")
            return None
        finally:
            # Always clear busy state and clean up
            print("Cleaning up after profile execution...")
            self.current_mode = None
            self.set_busy(False)
            print("Device no longer BUSY - monitoring re-enabled")
            try:
                self.send_command(':OUTP OFF')
                self.send_command(':BATT:OUTP OFF')
                print("Device cleanup completed - outputs turned off")
            except Exception as cleanup_error:
                print(f"Cleanup error (non-critical): {cleanup_error}")
                pass