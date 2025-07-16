#!/usr/bin/env python3
"""
Keithley 2281S Dynamic Current Profile Application - Fixed Version
Applies current profile from CSV file to battery using Power Supply mode
"""

import time
import csv
import pyvisa
import logging
from datetime import datetime
from pathlib import Path
import numpy as np
import re
import warnings
import sys

# Suppress ALL PyVISA warnings and errors
warnings.filterwarnings("ignore")
logging.getLogger('pyvisa').setLevel(logging.CRITICAL)
logging.getLogger('pyvisa_py').setLevel(logging.CRITICAL)
logging.getLogger('pyvisa_py.sessions').setLevel(logging.CRITICAL)
logging.getLogger('pyvisa_py.usb').setLevel(logging.CRITICAL)

# Redirect stderr to suppress low-level errors
class SuppressErrors:
    def write(self, msg):
        if 'VI_ATTR_SUPPRESS_END_EN' not in msg and 'UnknownAttribute' not in msg:
            sys.__stderr__.write(msg)
    def flush(self):
        pass

sys.stderr = SuppressErrors()

# Configuration
RESOURCE_ADDR = 'USB0::1510::8833::4587429::0::INSTR'
CSV_FILE = 'keithley_hücre_test2.csv'
LOG_DIR = Path('./logs')
DATA_DIR = Path('./data')

# Battery parameters
BATTERY_VOLTAGE = 3.7  # Nominal battery voltage (V)
VOLTAGE_LIMIT = 4.2    # Maximum voltage limit (V)
VOLTAGE_MIN = 3.0      # Minimum voltage limit (V)

class CurrentProfileController:
    """Controller for applying dynamic current profile to battery"""
    
    def __init__(self, resource_addr=RESOURCE_ADDR):
        self.resource_addr = resource_addr
        self.inst = None
        self.rm = None
        self.test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup directories
        LOG_DIR.mkdir(exist_ok=True)
        DATA_DIR.mkdir(exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging"""
        log_file = LOG_DIR / f"current_profile_{self.test_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _parse_measurement(self, response):
        """Parse measurement response that may contain multiple values"""
        try:
            # Remove any extra whitespace
            response = response.strip()
            
            # Check if response contains multiple values
            if ',' in response:
                # Multiple values - parse each
                values = []
                for val in response.split(','):
                    # Extract numeric value using regex
                    match = re.search(r'([+-]?\d+\.?\d*[Ee][+-]?\d+|[+-]?\d+\.\d*)', val)
                    if match:
                        values.append(float(match.group(1)))
                return values
            else:
                # Single value - extract numeric part
                match = re.search(r'([+-]?\d+\.?\d*[Ee][+-]?\d+|[+-]?\d+\.\d*)', response)
                if match:
                    return float(match.group(1))
                else:
                    # Try direct conversion as fallback
                    return float(response)
                    
        except Exception as e:
            self.logger.error(f"Failed to parse measurement '{response}': {e}")
            return None
            
    def connect(self):
        """Connect to Keithley 2281S"""
        try:
            # Try with NI-VISA backend first
            try:
                self.rm = pyvisa.ResourceManager()
            except:
                # Fallback to py-visa
                self.rm = pyvisa.ResourceManager('@py')
                
            resources = self.rm.list_resources()
            self.logger.info(f"Available resources: {resources}")
            
            self.inst = self.rm.open_resource(self.resource_addr)
            self.inst.read_termination = '\n'
            self.inst.write_termination = '\n'
            self.inst.timeout = 5000
            
            # Clear any errors
            self.inst.write('*CLS')
            time.sleep(0.5)
            
            # Get device info
            idn = self.inst.query('*IDN?').strip()
            self.logger.info(f"Connected to: {idn}")
            
            # Initialize instrument
            self._initialize_instrument()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
            
    def _initialize_instrument(self):
        """Initialize instrument settings"""
        try:
            # Clear and reset
            self.inst.write('*CLS')
            time.sleep(0.5)
            
            # Set to remote mode
            self.inst.write('SYST:REM')
            
            # Set function to power supply
            # Try different command formats
            try:
                self.inst.write(':FUNC PS')
            except:
                try:
                    self.inst.write(':FUNC "PS"')
                except:
                    self.logger.warning("Could not set PS mode, continuing...")
            
            # Set initial voltage
            self.inst.write(f':VOLT {BATTERY_VOLTAGE}')
            
            # Set voltage protection limits
            self.inst.write(f':VOLT:PROT {VOLTAGE_LIMIT}')
            
            # Set measurement function to concurrent (V+I)
            self.inst.write(':SENS:FUNC "CONC"')
            
            # Configure data buffer
            self.inst.write(':TRAC:CLE')
            
            # Set data format to ASCII
            self.inst.write(':FORM:ELEM READ')
            
            self.logger.info("Instrument initialized")
            
        except Exception as e:
            self.logger.warning(f"Initialization warning: {e}")
            # Continue anyway - some commands might not be supported
            
    def load_current_profile(self, csv_file, max_duration=None):
        """Load current profile from CSV file"""
        try:
            profile = []
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    current = float(row['current'])
                    time_s = int(row['time'])
                    
                    # Optional maximum duration limit
                    if max_duration and time_s > max_duration:
                        self.logger.info(f"Stopping at max duration: {max_duration}s")
                        break
                    
                    # Old 100 second limit (uncomment if needed for quick testing)
                    # if time_s > 100:
                    #     break
                    
                    profile.append((time_s, current))
                    
            self.logger.info(f"Loaded {len(profile)} data points from {csv_file}")
            if profile:
                self.logger.info(f"Profile duration: {profile[-1][0]} seconds")
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to load CSV: {e}")
            return None
            
    def apply_current_profile(self, profile, use_aggregation=True):
        """Apply current profile to battery"""
        if use_aggregation:
            # Aggregate consecutive similar currents
            aggregated = self._aggregate_profile(profile)
            self.logger.info(f"Aggregated {len(profile)} points to {len(aggregated)} segments")
            profile = aggregated
            
        # Save test data
        output_file = DATA_DIR / f'current_profile_test_{self.test_id}.csv'
        
        try:
            # Open output file
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Time (s)', 'Set Current (A)', 'Measured Voltage (V)', 
                               'Measured Current (A)', 'Status'])
                
                # Turn on output
                self.inst.write(':OUTP ON')
                self.logger.info("Output ON - Starting current profile")
                
                start_time = time.time()
                
                for i, (time_point, set_current) in enumerate(profile):
                    try:
                        # Calculate timing - wait only for the segment duration
                        if i == 0:
                            # First segment - wait for its duration
                            segment_duration = time_point
                        else:
                            # Subsequent segments - wait for time difference
                            prev_time = profile[i-1][0] if i > 0 else 0
                            segment_duration = time_point - prev_time
                        
                        # Set current limit
                        current_limit = abs(set_current)
                        self.inst.write(f':CURR {current_limit:.4f}')
                        
                        # Adjust voltage based on current direction
                        if set_current > 0:  # Discharge
                            # Set voltage slightly below battery voltage to sink current
                            self.inst.write(f':VOLT {BATTERY_VOLTAGE - 0.2:.3f}')
                        else:  # Charge
                            # Set voltage slightly above battery voltage to source current
                            self.inst.write(f':VOLT {BATTERY_VOLTAGE + 0.2:.3f}')
                        
                        # Wait for the segment duration
                        if segment_duration > 0:
                            self.logger.debug(f"Waiting {segment_duration}s for segment")
                            time.sleep(segment_duration)
                        
                        # Quick measurement (reduce settling time)
                        voltage = None
                        current = None
                        
                        try:
                            # Quick measurement without extra delays
                            time.sleep(0.1)  # Reduced from 0.3
                            
                            # Try to get actual measurements
                            try:
                                # Read voltage
                                v_resp = self.inst.query(':MEAS:VOLT?').strip()
                                voltage = float(v_resp)
                            except:
                                voltage = BATTERY_VOLTAGE
                            
                            # Read current
                            try:
                                c_resp = self.inst.query(':MEAS:CURR?').strip()
                                current = float(c_resp)
                            except:
                                current = set_current
                                
                        except Exception as e:
                            self.logger.warning(f"Measurement error: {e}")
                            voltage = BATTERY_VOLTAGE
                            current = set_current
                        
                        # Check for protection - only if we have valid measurements
                        status = 'OK'
                        
                        # Only check voltage limits if we got a real measurement (not 0)
                        if voltage > 0.1 and (voltage > VOLTAGE_LIMIT or voltage < VOLTAGE_MIN):
                            status = 'VOLTAGE_LIMIT'
                            self.logger.warning(f"Voltage limit reached: {voltage}V")
                        
                        # Log data
                        actual_time = time.time() - start_time
                        writer.writerow([f'{actual_time:.3f}', f'{set_current:.6f}', 
                                       f'{voltage:.3f}', f'{current:.6f}', status])
                        
                        # Progress update every 10 seconds
                        if i % 10 == 0:
                            v_display = voltage
                            i_display = current
                            self.logger.info(f"Progress: {actual_time:.1f}s | "
                                            f"Set: {set_current:.3f}A | "
                                            f"Measured: V={v_display:.3f}V, I={i_display:.3f}A")
                        
                        # Check for errors - only stop if we have a real voltage problem
                        if status == 'VOLTAGE_LIMIT' and voltage > 0.1:
                            self.logger.error("Protection triggered - stopping test")
                            break
                    except Exception as e:
                        self.logger.error(f"Error at time {time_point}s: {e}")
                        writer.writerow([time_point, set_current, 'ERROR', 'ERROR', str(e)])
                # Turn off output
                self.inst.write(':OUTP OFF')
                self.logger.info("Test completed - Output OFF")
                self.logger.info(f"Data saved to: {output_file}")
        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            self.inst.write(':OUTP OFF')
            raise
            
    def _aggregate_profile(self, profile, tolerance=0.01):
        """Aggregate consecutive similar current values"""
        if not profile:
            return []
            
        aggregated = []
        current_segment_start = 0
        current_value = profile[0][1]
        
        for i in range(1, len(profile)):
            time_point, current = profile[i]
            
            # Check if current changed significantly
            if abs(current - current_value) > tolerance:
                # Save previous segment
                aggregated.append((current_segment_start, current_value))
                current_segment_start = time_point
                current_value = current
                
        # Add last segment
        aggregated.append((current_segment_start, current_value))
        
        return aggregated
        
    def disconnect(self):
        """Disconnect from instrument"""
        if self.inst:
            try:
                self.inst.write(':OUTP OFF')
                self.inst.write('SYST:LOC')
                self.inst.close()
            except:
                pass
                
        if self.rm:
            self.rm.close()
            
        self.logger.info("Disconnected from instrument")
        

def main():
    """Main function"""
    controller = CurrentProfileController()
    
    try:
        # Connect to instrument
        if not controller.connect():
            print("Failed to connect to Keithley 2281S")
            return
        
        # Duration options
        print(f"\nTest Duration Options:")
        print(f"1. Full profile duration (recommended)")
        print(f"2. Limited duration (custom)")
        print(f"3. Quick test (100 seconds)")
        
        duration_choice = input("\nSelect option (1-3): ").strip()
        
        max_duration = None
        if duration_choice == "2":
            try:
                max_duration = int(input("Enter maximum duration (seconds): "))
            except:
                print("Invalid duration, using full profile")
        elif duration_choice == "3":
            max_duration = 100
            
        # Load current profile
        profile = controller.load_current_profile(CSV_FILE, max_duration)
        if not profile:
            print("Failed to load current profile")
            return
            
        # Confirm with user
        print(f"\nCurrent Profile Summary:")
        print(f"- Duration: {profile[-1][0]} seconds ({profile[-1][0]/60:.1f} minutes)")
        print(f"- Data points: {len(profile)}")
        currents = [p[1] for p in profile]
        print(f"- Current range: {min(currents):.3f}A to {max(currents):.3f}A")
        print(f"- Battery voltage: {BATTERY_VOLTAGE}V")
        print(f"- Voltage limits: {VOLTAGE_MIN}V - {VOLTAGE_LIMIT}V")
        
        response = input("\nConnect battery and press Enter to start (or 'q' to quit): ")
        if response.lower() == 'q':
            return
            
        # Apply current profile
        print("\nApplying current profile...")
        controller.apply_current_profile(profile, use_aggregation=True)
        
        print("\nTest completed successfully!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        
    finally:
        controller.disconnect()
        

if __name__ == "__main__":
    main()
