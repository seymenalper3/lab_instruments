#!/usr/bin/env python3
"""
Keithley Pulse Test - Extract from main controller
Measures EVOC and ESR characteristics using battery test mode
"""
import csv
import time
import datetime
from pathlib import Path
from typing import Tuple


class KeithleyPulseTest:
    """
    Keithley Pulse Test Runner
    
    Runs battery pulse test to measure EVOC and ESR characteristics.
    Requires USB or GPIB connection (NOT Ethernet).
    """
    
    def __init__(self, controller):
        """
        Initialize pulse test runner
        
        Args:
            controller: Parent KeithleyController instance
        """
        self.controller = controller
    
    def run(self, pulses: int = 5,
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
        # Pre-flight checks
        if not self.controller.connected:
            raise Exception("Device not connected")
        
        if self.controller.is_ethernet_connection():
            raise Exception(
                "Pulse test data logging is not supported over Ethernet due to instrument limitations. "
                "Please use a USB connection for this test."
            )
            
        if self.controller.busy:
            raise Exception("Device is busy with another operation")
        
        # Set device as busy
        self.controller.set_busy(True)
        
        try:
            # Validate parameters
            self._validate_parameters(pulses, pulse_time, rest_time, i_pulse)
            
            # Initialize device
            is_ethernet = self.controller.is_ethernet_connection()
            self._initialize_device(sample_interval, is_ethernet)
            
            # Create output files
            pulse_file, rest_file = self._create_output_files()
            
            # Run pulse test
            self._execute_pulse_cycles(
                pulse_file, rest_file,
                pulses, pulse_time, rest_time,
                i_pulse, i_rest, is_ethernet
            )
            
            print("Pulse test completed successfully")
            print(f"Data saved to: {pulse_file}")
            print(f"Data saved to: {rest_file}")
            
            return (str(pulse_file), str(rest_file))
            
        finally:
            # Always clear busy state and clean up
            self.controller.set_busy(False)
            try:
                self.controller.send_command(':BATT:OUTP OFF')
            except:
                pass
    
    def _validate_parameters(self, pulses, pulse_time, rest_time, i_pulse):
        """Validate test parameters"""
        if pulses < 1 or pulses > 100:
            raise ValueError("Pulses must be between 1 and 100")
        if pulse_time < 1 or pulse_time > 300:
            raise ValueError("Pulse time must be between 1 and 300 seconds")
        if rest_time < 1 or rest_time > 300:
            raise ValueError("Rest time must be between 1 and 300 seconds")
        if i_pulse < 0.001 or i_pulse > self.controller.device_spec.max_current:
            raise ValueError(f"Pulse current must be between 0.001 and {self.controller.device_spec.max_current}A")
    
    def _initialize_device(self, sample_interval, is_ethernet):
        """Initialize device for pulse test"""
        try:
            print("Initializing Keithley for pulse test...")
            print(f"Connection type: {'Ethernet' if is_ethernet else 'USB/GPIB'}")
            
            # Set timeout
            if is_ethernet and hasattr(self.controller.interface.connection, 'settimeout'):
                self.controller.interface.connection.settimeout(5.0)
                print("Set ethernet timeout to 5 seconds")
            elif hasattr(self.controller.interface.connection, 'timeout'):
                self.controller.interface.connection.timeout = 5000
                print("Set VISA timeout to 5000ms")
            
            # Exact initialization sequence
            self.controller.send_command('*CLS')
            self.controller.send_command('SYST:REM')
            self.controller.send_command(':FUNC TEST')
            self.controller.send_command(':BATT:TEST:MODE DIS')
            self.controller.send_command(f':BATT:TEST:SENS:SAMP:INT {sample_interval}')
            self.controller.send_command(f':BATT:TEST:SENS:EVOC:DELA 0.05')
            self.controller.send_command(':FORM:UNITS OFF')
            self.controller.send_command(':SYST:AZER OFF')
            
            # Data logger setup
            self.controller.send_command(':BATT:DATA:CLE')
            self.controller.send_command(':BATT:DATA:STAT ON')
            self.controller.send_command(':BATT:TEST:EXEC STAR')
            
            time.sleep(1.0)  # Allow data logger to initialize
            
            # Debug check
            if is_ethernet:
                try:
                    data_status = self.controller.query_command(':BATT:DATA:STAT?')
                    print(f'DEBUG: Data logging status: {data_status}')
                except Exception as e:
                    print(f'DEBUG: Could not query data status: {e}')
            
            print("Device initialization complete")
            
        except Exception as e:
            raise Exception(f"Failed to initialize device for pulse test: {e}")
    
    def _create_output_files(self):
        """Create output CSV files"""
        logs_dir = Path('./logs')
        logs_dir.mkdir(exist_ok=True)
        
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        pulse_file = logs_dir / f'pulse_bt_{stamp}.csv'
        rest_file = logs_dir / f'rest_evoc_{stamp}.csv'
        
        print(f"Creating output files: {pulse_file.name}, {rest_file.name}")
        
        return pulse_file, rest_file
    
    def _execute_pulse_cycles(self, pulse_file, rest_file, pulses, pulse_time, 
                              rest_time, i_pulse, i_rest, is_ethernet):
        """Execute the pulse test cycles"""
        STEP = 0.5
        
        try:
            with open(pulse_file, 'w', newline='') as fpulse, \
                 open(rest_file, 'w', newline='') as frest:
                
                # Write headers
                wp = csv.writer(fpulse)
                wr = csv.writer(frest)
                wp.writerow(['t_rel_s', 'volt_v', 'curr_a'])
                wr.writerow(['t_rel_s', 'voc_v', 'esr_ohm'])
                fpulse.flush()
                frest.flush()
                
                t0 = time.time()
                print(f"Starting pulse test: {pulses} pulses...")
                
                def last_vi(cyc):
                    """Read buffer data"""
                    try:
                        buf = self.controller.query_command(':BATT:DATA:DATA? "VOLT,CURR,REL"')
                        
                        if is_ethernet and (cyc <= 2):
                            print(f'[DEBUG] Buffer length: {len(buf) if buf else 0}')
                        
                        if not buf or buf.strip() == '':
                            return None, None, None
                        
                        parts = buf.split(',')
                        if len(parts) < 3:
                            return None, None, None
                        
                        vals = list(map(float, parts[-3:]))
                        return vals[0], vals[1], vals[2]  # v, i, rel
                        
                    except Exception as e:
                        if is_ethernet and (cyc <= 2):
                            print(f'[DEBUG] last_vi() exception: {e}')
                        return None, None, None
                
                # Pulse cycles
                for cyc in range(1, pulses + 1):
                    print(f"Executing pulse {cyc}/{pulses}...")
                    
                    # PULSE phase
                    self.controller.send_command(f':BATT:TEST:CURR:LIM:SOUR {i_pulse}')
                    self.controller.send_command(':BATT:OUTP ON')
                    time.sleep(0.5)
                    
                    print(f'>>> {cyc}. PULSE — {pulse_time}s @ ~1A (Battery Test mode)')
                    end = time.time() + pulse_time
                    while time.time() < end:
                        v, i, rel = last_vi(cyc)
                        if v is not None:
                            wp.writerow([f'{rel:.3f}', f'{v:.6f}', f'{i:.6f}'])
                            fpulse.flush()
                        time.sleep(STEP)
                    
                    # REST phase
                    self.controller.send_command(':BATT:OUTP OFF')
                    self.controller.send_command(f':BATT:TEST:CURR:LIM:SOUR {i_rest}')
                    print(f'>>> Rest — {rest_time}s')
                    end = time.time() + rest_time
                    while time.time() < end:
                        try:
                            evoc_response = self.controller.query_command(':BATT:TEST:MEAS:EVOC?')
                            esr, voc = map(float, evoc_response.split(','))
                            wr.writerow([f'{time.time()-t0:.3f}', f'{voc:.6f}', f'{esr:.6f}'])
                            frest.flush()
                        except Exception as e:
                            print(f'EVOC measurement failed: {e}')
                        time.sleep(STEP)
                        
        except Exception as e:
            # Clean up on error
            try:
                self.controller.send_command(':BATT:OUTP OFF')
            except:
                pass
            raise Exception(f"Pulse test execution failed: {e}")

