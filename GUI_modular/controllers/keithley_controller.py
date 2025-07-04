#!/usr/bin/env python3
"""
Keithley 2281S Battery Simulator/Emulator Controller
"""
import csv
import time
import datetime
from typing import Optional
from controllers.base_controller import BaseDeviceController
from models.device_config import DEVICE_SPECS, DeviceType


class KeithleyController(BaseDeviceController):
    """Keithley 2281S Battery Simulator/Emulator Controller"""
    
    def __init__(self, interface):
        super().__init__(interface, DEVICE_SPECS[DeviceType.KEITHLEY_2281S])
        
    def set_voltage(self, voltage: float):
        """Set output voltage in volts"""
        if voltage < 0 or voltage > self.device_spec.max_voltage:
            raise ValueError(f"Voltage must be between 0 and {self.device_spec.max_voltage}V")
            
        cmd = self.device_spec.default_commands['set_voltage'].format(voltage)
        self.send_command(cmd)
        
    def set_current_limit(self, current: float):
        """Set current limit in amperes"""
        if current < 0 or current > self.device_spec.max_current:
            raise ValueError(f"Current must be between 0 and {self.device_spec.max_current}A")
            
        cmd = self.device_spec.default_commands['set_current'].format(current)
        self.send_command(cmd)
        
    def output_on(self):
        """Turn output on"""
        cmd = self.device_spec.default_commands['output_on']
        self.send_command(cmd)
        
    def output_off(self):
        """Turn output off"""
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
        
    def run_pulse_test(self, pulses: int = 5, 
                      pulse_time: float = 60.0, 
                      rest_time: float = 60.0,
                      i_pulse: float = 1.0,
                      i_rest: float = 0.0001,
                      sample_interval: float = 0.5) -> tuple:
        """
        Run battery pulse test with fixes for ethernet and current setting
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
            
            # Test parameters
            RAMP_UP = [0.05, 0.20]
            RAMP_DN = [0.20, 0.05]
            STEP = 0.5
            EVOC_DLY = 0.05
            
            # Determine if ethernet connection
            is_ethernet = self.is_ethernet_connection()
            
            def last_vi():
                """Get last voltage, current and relative time from device buffer"""
                try:
                    # Store original timeout - handle both socket and VISA connections
                    if is_ethernet:
                        original_timeout = self.interface.connection.gettimeout()
                        self.interface.connection.settimeout(15.0)  # 15 second timeout for Ethernet
                        time.sleep(0.1)  # Delay for ethernet
                    else:
                        original_timeout = getattr(self.interface.connection, 'timeout', 5000)
                        if hasattr(self.interface.connection, 'timeout'):
                            self.interface.connection.timeout = 5000  # 5 second timeout for USB
                    
                    # Try buffer method first
                    buf = self.query_command(':BATT:DATA:DATA? "VOLT,CURR,REL"')
                    
                    if buf and len(buf.split(',')) >= 3:
                        vals = list(map(float, buf.split(',')[-3:]))
                        # Restore original timeout
                        if is_ethernet:
                            self.interface.connection.settimeout(original_timeout)
                        else:
                            if hasattr(self.interface.connection, 'timeout'):
                                self.interface.connection.timeout = original_timeout
                        return vals[0], vals[1], vals[2]
                    
                    # If buffer fails, try direct measurement with retries
                    for retry in range(5):  # More retries
                        try:
                            if is_ethernet:
                                time.sleep(0.2)  # Longer delay for ethernet
                            
                            volt_response = self.query_command(':MEAS:VOLT?')
                            if is_ethernet:
                                time.sleep(0.1)  # Additional delay between commands
                            curr_response = self.query_command(':MEAS:CURR?')
                            
                            if volt_response and curr_response:
                                try:
                                    voltage = float(volt_response.strip())
                                    current = float(curr_response.strip())
                                    rel_time = time.time() - t0
                                    # Restore original timeout
                                    if is_ethernet:
                                        self.interface.connection.settimeout(original_timeout)
                                    else:
                                        if hasattr(self.interface.connection, 'timeout'):
                                            self.interface.connection.timeout = original_timeout
                                    return voltage, current, rel_time
                                except ValueError as ve:
                                    print(f'DEBUG: Could not parse measurement data: V="{volt_response}" I="{curr_response}"')
                        except Exception as e:
                            if retry < 4:
                                wait_time = 0.5 * (retry + 1)  # Progressive backoff
                                print(f'DEBUG: Measurement retry {retry + 1}/5 failed: {e}, waiting {wait_time}s')
                                time.sleep(wait_time)
                                continue
                            else:
                                print(f'DEBUG: Direct measurement failed after 5 retries: {e}')
                    
                    # Restore original timeout
                    if is_ethernet:
                        self.interface.connection.settimeout(original_timeout)
                    else:
                        if hasattr(self.interface.connection, 'timeout'):
                            self.interface.connection.timeout = original_timeout
                    return None, None, None
                    
                except Exception as e:
                    print(f'DEBUG: Exception in last_vi(): {e}')
                    try:
                        if is_ethernet:
                            self.interface.connection.settimeout(original_timeout)
                        else:
                            if hasattr(self.interface.connection, 'timeout'):
                                self.interface.connection.timeout = original_timeout
                    except:
                        pass
                    return None, None, None
            
            # Initialize device for battery testing
            try:
                print("Initializing Keithley for pulse test...")
                print(f"Connection type: {'Ethernet' if is_ethernet else 'USB/GPIB'}")
                
                # Reset device
                self.send_command('*RST')
                time.sleep(3 if is_ethernet else 1)
                
                # Test basic communication
                try:
                    idn_response = self.query_command('*IDN?')
                    print(f"DEBUG: Device identified as: {idn_response[:50]}...")
                except Exception as e:
                    print(f"WARNING: Device identification failed: {e}")
                    raise Exception("Device not responding to basic commands")
                
                # Clear and setup with delays for ethernet
                self.send_command_with_delay('*CLS')
                self.send_command_with_delay('SYST:REM')
                self.send_command_with_delay(':FUNC TEST')
                self.send_command_with_delay(':BATT:TEST:MODE DIS')
                
                # Pre-configure pulse current settings
                print(f'DEBUG: Configuring pulse current to {i_pulse}A')
                self.send_command_with_delay(f':BATT:TEST:CURR:END {i_pulse:.6f}')
                self.send_command_with_delay(f':BATT:TEST:CURR:LIM:SOUR {i_pulse:.6f}')
                
                # Verify current settings
                try:
                    curr_end = self.query_command(':BATT:TEST:CURR:END?')
                    curr_lim = self.query_command(':BATT:TEST:CURR:LIM:SOUR?')
                    print(f'DEBUG: Current settings confirmed - End: {curr_end}, Limit: {curr_lim}')
                except:
                    print('DEBUG: Could not verify current settings')
                
                # Continue initialization
                self.send_command_with_delay(f':BATT:TEST:SENS:SAMP:INT {sample_interval}')
                self.send_command_with_delay(f':BATT:TEST:SENS:EVOC:DELA {EVOC_DLY}')
                self.send_command_with_delay(':FORM:UNITS OFF')
                self.send_command_with_delay(':SYST:AZER OFF')
                
                # Clear buffer multiple times to ensure it's ready
                for _ in range(3):
                    self.send_command_with_delay(':BATT:DATA:CLE')
                    time.sleep(0.2 if is_ethernet else 0.1)
                
                self.send_command_with_delay(':BATT:DATA:STAT ON')
                time.sleep(0.5 if is_ethernet else 0.2)
                
                self.send_command_with_delay(':BATT:TEST:EXEC STAR')
                
                # Wait longer for data collection to start
                time.sleep(3.0 if is_ethernet else 1.0)
                
                # Verify data collection is working
                buffer_working = False
                try:
                    test_data = self.query_command(':BATT:DATA:DATA? "VOLT,CURR,REL"')
                    if test_data and ',' in test_data:
                        print(f"DEBUG: Data collection active, sample: {test_data[:50]}...")
                        buffer_working = True
                    else:
                        print("DEBUG: WARNING - No data in buffer after initialization")
                except Exception as e:
                    print(f"DEBUG: WARNING - Failed to read test data: {e}")
                
                # If buffer not working, test direct measurements
                if not buffer_working:
                    print("DEBUG: Testing direct measurement as fallback...")
                    try:
                        volt_test = self.query_command(':MEAS:VOLT?')
                        curr_test = self.query_command(':MEAS:CURR?')
                        if volt_test and curr_test:
                            print(f"DEBUG: Direct measurement working - V:{volt_test} I:{curr_test}")
                        else:
                            print("WARNING: Both buffer and direct measurements failing")
                    except Exception as e:
                        print(f"WARNING: Direct measurement test failed: {e}")
                
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
                    
                    for cyc in range(1, pulses + 1):
                        print(f"Executing pulse {cyc}/{pulses}...")
                        
                        # Ramp up phase
                        for lim in RAMP_UP:
                            # Format and send current command
                            current_cmd = f':BATT:TEST:CURR:LIM:SOUR {lim:.6f}'
                            self.send_command_with_delay(current_cmd)
                            
                            # Verify for debugging
                            if cyc == 1:  # Only verify on first cycle
                                try:
                                    actual = self.query_command(':BATT:TEST:CURR:LIM:SOUR?')
                                    print(f'DEBUG: Ramp current {lim}A, device reports: {actual}')
                                except:
                                    pass
                            
                            self.send_command(':BATT:OUTP ON')
                            end = time.time() + 2
                            
                            while time.time() < end:
                                v, i, rel = last_vi()
                                if v is not None:
                                    wp.writerow([f'{rel:.3f}', f'{v:.6f}', f'{i:.6f}'])
                                    fpulse.flush()
                                time.sleep(STEP)
                        
                        # Pulse phase - ensure current is set correctly
                        print(f'DEBUG: Setting pulse current to {i_pulse}A')
                        
                        # Set current with both methods for compatibility
                        self.send_command_with_delay(f':BATT:TEST:CURR:LIM:SOUR {i_pulse:.6f}')
                        self.send_command_with_delay(f':BATT:TEST:CURR:END {i_pulse:.6f}')
                        
                        # Verify on first pulse
                        if cyc == 1:
                            try:
                                actual = self.query_command(':BATT:TEST:CURR:LIM:SOUR?')
                                print(f'DEBUG: Pulse current set to {i_pulse}A, device reports: {actual}')
                            except:
                                pass
                        
                        print(f'>>> Pulse {cyc} — {pulse_time}s @ {i_pulse}A')
                        end = time.time() + pulse_time
                        pulse_count = 0
                        
                        while time.time() < end:
                            v, i, rel = last_vi()
                            if v is not None:
                                wp.writerow([f'{rel:.3f}', f'{v:.6f}', f'{i:.6f}'])
                                fpulse.flush()
                                pulse_count += 1
                            time.sleep(STEP)
                        
                        print(f'DEBUG: Pulse phase logged {pulse_count} data points')
                        
                        # Ramp down phase
                        for lim in RAMP_DN:
                            self.send_command_with_delay(f':BATT:TEST:CURR:LIM:SOUR {lim:.6f}')
                            end = time.time() + 2
                            
                            while time.time() < end:
                                v, i, rel = last_vi()
                                if v is not None:
                                    wp.writerow([f'{rel:.3f}', f'{v:.6f}', f'{i:.6f}'])
                                    fpulse.flush()
                                time.sleep(STEP)
                        
                        # Rest phase
                        self.send_command(':BATT:OUTP OFF')
                        print(f'>>> Rest {cyc} — {rest_time}s')
                        end = time.time() + rest_time
                        rest_count = 0
                        
                        while time.time() < end:
                            # Get EVOC measurement
                            try:
                                evoc_response = self.query_command(':BATT:TEST:MEAS:EVOC?')
                                if evoc_response:
                                    esr, voc = map(float, evoc_response.split(','))
                                    wr.writerow([f'{time.time()-t0:.3f}', f'{voc:.6f}', f'{esr:.6f}'])
                                    frest.flush()
                                    rest_count += 1
                                    print(f'REST: VOC={voc:.3f}V ESR={esr:.6f}Ω')
                            except Exception as e:
                                print(f'DEBUG: EVOC measurement failed: {e}')
                            
                            time.sleep(STEP)
                        
                        print(f'DEBUG: Rest phase logged {rest_count} data points')
                    
                    print("Pulse test completed successfully")
                    
                    # Return file paths
                    return (pulse_file, rest_file)
                    
            except Exception as e:
                # Ensure device is cleaned up on error
                try:
                    self.send_command(':BATT:OUTP OFF')
                    self.local_mode()
                except:
                    pass
                raise Exception(f"Pulse test execution failed: {e}")
                
        finally:
            # Always clear busy state
            self.set_busy(False)
            
            # Clean up device state
            try:
                self.send_command(':BATT:OUTP OFF')
                self.send_command(':BATT:TEST:EXEC STOP')
                self.send_command(':BATT:DATA:STAT OFF')
                self.local_mode()
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
            # Cleanup
            try:
                self.send_command(':BATT:OUTP OFF')
                self.send_command('SYST:LOC')
            except:
                pass
                
            # Clear busy state
            self.set_busy(False)