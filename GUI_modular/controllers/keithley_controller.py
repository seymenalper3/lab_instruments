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
        
    def run_pulse_test(self, 
                      pulses: int = 2, 
                      pulse_time: float = 30.0, 
                      rest_time: float = 30.0,
                      i_pulse: float = 1.0,
                      i_rest: float = 0.0001,
                      sample_interval: float = 0.5) -> tuple:
        """
        Run battery pulse test
        Returns tuple of (pulse_file_path, rest_file_path)
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
        
            def last_vi():
                """Get last voltage, current and relative time from device buffer"""
                try:
                    # First try the data buffer method
                    original_timeout = self.interface.connection.timeout
                    self.interface.connection.timeout = 2000  # 2 second timeout
                    buf = self.query_command(':BATT:DATA:DATA? "VOLT,CURR,REL"')
                    
                    if buf and len(buf.split(',')) >= 3:
                        vals = list(map(float, buf.split(',')[-3:]))
                        self.interface.connection.timeout = original_timeout
                        return vals[0], vals[1], vals[2]
                    
                    # If buffer method fails, try direct measurement
                    debug_msg = f'DEBUG: Buffer method failed, trying direct measurement'
                    print(debug_msg)
                    try:
                        with open('pulse_debug.log', 'a') as debug_log:
                            debug_log.write(debug_msg + '\n')
                    except:
                        pass
                    
                    # Try direct voltage and current measurement
                    try:
                        volt_cmd = ':MEAS:VOLT?'
                        curr_cmd = ':MEAS:CURR?'
                        
                        volt_response = self.query_command(volt_cmd)
                        curr_response = self.query_command(curr_cmd)
                        
                        if volt_response and curr_response:
                            voltage = float(volt_response.strip())
                            current = float(curr_response.strip())
                            rel_time = time.time() - t0
                            
                            self.interface.connection.timeout = original_timeout
                            debug_msg = f'DEBUG: Direct measurement successful: V={voltage:.3f}V I={current:.3f}A'
                            print(debug_msg)
                            try:
                                with open('pulse_debug.log', 'a') as debug_log:
                                    debug_log.write(debug_msg + '\n')
                            except:
                                pass
                            return voltage, current, rel_time
                            
                    except Exception as direct_e:
                        print(f'DEBUG: Direct measurement also failed: {direct_e}')
                    
                    self.interface.connection.timeout = original_timeout
                    return None, None, None
                    
                except Exception as e:
                    print(f'DEBUG: Exception in last_vi(): {e}')
                    # Restore original timeout
                    try:
                        self.interface.connection.timeout = original_timeout
                    except:
                        pass
                    return None, None, None
        
                # Initialize device for battery testing
            try:
                print("Initializing Keithley for pulse test...")
                # Reset device to clear any stuck states
                try:
                    self.send_command('*RST')
                    time.sleep(1)
                except:
                    pass
                
                self.send_command('*CLS')
                self.send_command('SYST:REM')
                self.send_command(':FUNC TEST')
                self.send_command(':BATT:TEST:MODE DIS')
                self.send_command(f':BATT:TEST:SENS:SAMP:INT {sample_interval}')
                self.send_command(f':BATT:TEST:SENS:EVOC:DELA {EVOC_DLY}')
                self.send_command(':FORM:UNITS OFF')
                self.send_command(':SYST:AZER OFF')
                self.send_command(':BATT:DATA:CLE')
                self.send_command(':BATT:DATA:STAT ON')
                self.send_command(':BATT:TEST:EXEC STAR')
                
                # Wait a moment for data collection to start
                time.sleep(0.5)
                
                # Check if data collection is working
                try:
                    test_data = self.query_command(':BATT:DATA:DATA? "VOLT,CURR,REL"')
                    if test_data:
                        print(f"DEBUG: Data collection active, sample: {test_data[:50]}...")
                    else:
                        print("DEBUG: WARNING - No data in buffer after initialization")
                except Exception as e:
                    print(f"DEBUG: WARNING - Failed to read test data: {e}")
                
                # Test if device is responding
                try:
                    self.query_command('*IDN?')
                    print("Device initialization complete")
                except:
                    raise Exception("Device not responding after initialization")
            except Exception as e:
                raise Exception(f"Failed to initialize device for pulse test: {e}")
        
            # Create output files with timestamp
            try:
                import os
                stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                pulse_file = f'pulse_bt_{stamp}.csv'
                rest_file = f'rest_evoc_{stamp}.csv'
                
                # Ensure we can write files
                print(f"Creating output files: {pulse_file}, {rest_file}")
                
            except Exception as e:
                raise Exception(f"Failed to prepare output files: {e}")
        
            try:
                with open(pulse_file, 'w', newline='') as fpulse, \
                     open(rest_file, 'w', newline='') as frest:
                    
                    wp = csv.writer(fpulse)
                    wr = csv.writer(frest)
                    wp.writerow(['t_rel_s', 'volt_v', 'curr_a'])
                    wr.writerow(['t_rel_s', 'voc_v', 'esr_ohm'])
                    fpulse.flush()
                    frest.flush()
                    
                    print(f"DEBUG: CSV files created successfully:")
                    print(f"DEBUG: Pulse file: {pulse_file}")
                    print(f"DEBUG: Rest file: {rest_file}")
                    
                    # Also write debug info to a log file
                    with open('pulse_debug.log', 'w') as debug_log:
                        debug_log.write(f"Pulse test started at {datetime.datetime.now()}\n")
                        debug_log.write(f"Pulse file: {pulse_file}\n") 
                        debug_log.write(f"Rest file: {rest_file}\n")
                        debug_log.write(f"Parameters: pulses={pulses}, pulse_time={pulse_time}, rest_time={rest_time}, i_pulse={i_pulse}\n\n")
                    
                    t0 = time.time()
                    print(f"Starting pulse test: {pulses} pulses...")
                    
                    for cyc in range(1, pulses + 1):
                        print(f"Executing pulse {cyc}/{pulses}...")
                        
                        # Ramp up phase
                        for lim in RAMP_UP:
                            self.send_command(f':BATT:TEST:CURR:LIM:SOUR {lim}')
                            self.send_command(':BATT:OUTP ON')
                            end = time.time() + 2
                            ramp_up_count = 0
                            while time.time() < end:
                                v, i, rel = last_vi()
                                if v is not None:
                                    wp.writerow([f'{rel:.3f}', f'{v:.6f}', f'{i:.6f}'])
                                    fpulse.flush()
                                    ramp_up_count += 1
                                else:
                                    print(f'DEBUG: Ramp-up data read failed at limit {lim}A')
                                time.sleep(STEP)
                            print(f'DEBUG: Ramp-up at {lim}A saved {ramp_up_count} points')
                    
                        # Pulse phase
                        self.send_command(f':BATT:TEST:CURR:LIM:SOUR {i_pulse}')
                        print(f'>>> {cyc}. PULSE — {pulse_time}s')
                        end = time.time() + pulse_time
                        pulse_data_count = 0
                        while time.time() < end:
                            v, i, rel = last_vi()
                            if v is not None:
                                wp.writerow([f'{rel:.3f}', f'{v:.6f}', f'{i:.6f}'])
                                fpulse.flush()
                                pulse_data_count += 1
                                print(f'PULSE: V={v:.3f}V I={i:.3f}A t={rel:.1f}s')
                            else:
                                print(f'DEBUG: Pulse data read failed at t={time.time()-t0:.1f}s')
                            time.sleep(STEP)
                        debug_msg = f'DEBUG: Pulse {cyc} saved {pulse_data_count} data points'
                        print(debug_msg)
                        try:
                            with open('pulse_debug.log', 'a') as debug_log:
                                debug_log.write(debug_msg + '\n')
                        except:
                            pass
                        
                        # Ramp down phase
                        for lim in RAMP_DN:
                            self.send_command(f':BATT:TEST:CURR:LIM:SOUR {lim}')
                            end = time.time() + 2
                            ramp_down_count = 0
                            while time.time() < end:
                                v, i, rel = last_vi()
                                if v is not None:
                                    wp.writerow([f'{rel:.3f}', f'{v:.6f}', f'{i:.6f}'])
                                    fpulse.flush()
                                    ramp_down_count += 1
                                else:
                                    print(f'DEBUG: Ramp-down data read failed at limit {lim}A')
                                time.sleep(STEP)
                            print(f'DEBUG: Ramp-down at {lim}A saved {ramp_down_count} points')
                        
                        # Rest phase
                        self.send_command(':BATT:OUTP OFF')
                        self.send_command(f':BATT:TEST:CURR:LIM:SOUR {i_rest}')
                        print(f'>>> Rest — {rest_time}s')
                        end = time.time() + rest_time
                        while time.time() < end:
                            try:
                                evoc_response = self.query_command(':BATT:TEST:MEAS:EVOC?')
                                esr, voc = map(float, evoc_response.split(','))
                                wr.writerow([f'{time.time()-t0:.3f}', f'{voc:.6f}', f'{esr:.6f}'])
                                frest.flush()
                                print(f'REST: VOC={voc:.3f}V ESR={esr:.6f}Ω')
                            except:
                                pass
                            time.sleep(STEP)
                    
                    print("Pulse test completed successfully")
                    
                    # Log final file status
                    try:
                        with open('pulse_debug.log', 'a') as debug_log:
                            debug_log.write(f"\nPulse test completed at {datetime.datetime.now()}\n")
                            
                            # Check file sizes
                            import os
                            pulse_size = os.path.getsize(pulse_file) if os.path.exists(pulse_file) else 0
                            rest_size = os.path.getsize(rest_file) if os.path.exists(rest_file) else 0
                            
                            debug_log.write(f"Pulse file size: {pulse_size} bytes\n")
                            debug_log.write(f"Rest file size: {rest_size} bytes\n")
                            
                            if pulse_size <= 50:  # Only headers
                                debug_log.write("WARNING: Pulse file appears to be empty (only headers)\n")
                            if rest_size <= 50:   # Only headers  
                                debug_log.write("WARNING: Rest file appears to be empty (only headers)\n")
                    except Exception as log_e:
                        print(f"Failed to write final log: {log_e}")
                    
            except Exception as e:
                # Ensure device is cleaned up on error
                try:
                    self.send_command(':BATT:OUTP OFF')
                    self.local_mode()
                except:
                    pass
                # Clear busy state on error
                self.set_busy(False)
                raise Exception(f"Pulse test execution failed: {e}")
        
        finally:
            # Always ensure cleanup and clear busy state
            try:
                # Quick cleanup with reduced timeout
                original_timeout = self.interface.connection.timeout
                self.interface.connection.timeout = 1000  # 1 second timeout for cleanup
                
                self.send_command(':BATT:OUTP OFF')
                self.send_command('SYST:LOC')
                
                self.interface.connection.timeout = original_timeout
                print("Device cleanup completed")
            except Exception as e:
                print(f"Warning: Cleanup failed: {e}")
                # Restore timeout even if cleanup fails
                try:
                    self.interface.connection.timeout = original_timeout
                except:
                    pass
            finally:
                # Always clear busy state
                self.set_busy(False)
                print("Device marked as available for monitoring")
        
        return pulse_file, rest_file