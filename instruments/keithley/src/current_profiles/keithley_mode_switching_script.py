#!/usr/bin/env python3
"""
Keithley 2281S Mode-Switching Current Profile Script
Applies a profile with distinct charge (Power Supply mode) and discharge (Battery Test mode) segments.
Example Profile: 0-10s charge, 10-20s discharge, 20-30s charge, 30-40s discharge
"""

import time
import pyvisa
import logging
import pandas as pd
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Keithley2281S:
    def __init__(self, resource_name='USB0::1510::8833::4587429::0::INSTR'):
        """Initializes the Keithley2281S driver."""
        self.resource_name = resource_name
        self.rm = pyvisa.ResourceManager('@py')
        self.instr = None
        
    def connect(self):
        """Establishes connection with the instrument."""
        try:
            logging.info(f"Connecting to {self.resource_name}...")
            self.instr = self.rm.open_resource(self.resource_name)
            self.instr.read_termination = '\n'
            self.instr.write_termination = '\n'
            self.instr.timeout = 10000  # 10 second timeout
            logging.info("Connection successful.")
            return True
        except pyvisa.errors.VisaIOError as e:
            logging.error(f"Connection failed: {e}")
            return False

    def write(self, command):
        """Sends a SCPI command to the instrument."""
        logging.debug(f"Sending: {command}")
        self.instr.write(command)
        time.sleep(0.1)

    def query(self, command):
        """Sends a SCPI query to the instrument."""
        logging.debug(f"Querying: {command}")
        response = self.instr.query(command).strip()
        logging.debug(f"Response: {response}")
        return response

    def check_errors(self):
        """Queries for system errors and logs them."""
        err = self.query('SYST:ERR?')
        code = err.split(',')[0]
        try:
            if int(code) != 0:
                logging.warning(f"Instrument error reported: {err}")
        except ValueError:
            logging.error(f"Could not parse error code from response: {err}")

    def initialize(self):
        """Initializes the instrument to a known state."""
        logging.info("Initializing instrument...")
        self.write("*RST")
        time.sleep(2)
        self.write("*CLS")
        
        idn = self.query("*IDN?")
        logging.info(f"Connected to: {idn}")
        self.check_errors()

    def run_profile(self, profile_data):
        """Runs the entire charge/discharge profile."""
        logging.info("\n=== Starting Current Profile Execution ===")
        
        for i, segment in enumerate(profile_data):
            time_s = segment['time_s']
            current_a = float(segment['current_a']) # Ensure float
            
            duration = time_s - (float(profile_data[i-1]['time_s']) if i > 0 else 0)
            if duration <= 0:
                logging.warning(f"Skipping segment {i+1} with zero or negative duration.")
                continue

            logging.info(f"\nSegment {i+1}: t={time_s}s, I={current_a}A, duration={duration:.2f}s")

            if current_a > 0:
                # Charge segment - use power supply mode
                voltage = 4.2  # Set a safe charging voltage
                logging.info(f"Executing CHARGE: {current_a:.3f}A for {duration:.2f}s...")
                
                # Make sure we're in power supply mode
                self.write(":OUTP OFF")
                time.sleep(0.1)
                
                # Set up power supply mode for charging
                self.write(f":VOLT {voltage}")
                self.write(f":VOLT:PROT {voltage}")
                self.write(f":CURR {current_a}")
                self.write(":OUTP ON")
                
                # Wait a bit then measure
                time.sleep(1)
                try:
                    measurement = self.query(":MEAS:VOLT?").strip()
                    logging.info(f"Measurement: {measurement}")
                except Exception as e:
                    logging.warning(f"Measurement failed: {e}")
                
                time.sleep(duration - 1)
                self.write(":OUTP OFF")
                
            else:
                # Discharge segment - use power supply mode with sink behavior
                discharge_current = abs(current_a)
                if discharge_current == 0:
                    logging.info("Skipping zero-current discharge (rest) segment.")
                    time.sleep(duration)
                    continue
                
                logging.info(f"Executing DISCHARGE: {discharge_current:.3f}A for {duration:.2f}s...")
                
                # Make sure we're in power supply mode
                self.write(":OUTP OFF")
                time.sleep(0.1)
                
                # Set up power supply mode for discharge (lower voltage to create sink)
                sink_voltage = 3.0  # Lower voltage to pull current from battery
                self.write(f":VOLT {sink_voltage}")
                self.write(f":VOLT:PROT 4.2")  # Keep protection high
                self.write(f":CURR {discharge_current}")
                self.write(":OUTP ON")
                
                # Wait a bit then measure
                time.sleep(1)
                try:
                    measurement = self.query(":MEAS:VOLT?").strip()
                    logging.info(f"Measurement: {measurement}")
                except Exception as e:
                    logging.warning(f"Measurement failed: {e}")
                
                time.sleep(duration - 1)
                self.write(":OUTP OFF")

        logging.info("\n=== Profile Execution Completed ===")

    def safety_shutdown(self):
        """Turns off all outputs for safety."""
        logging.info("\nSafety shutdown...")
        try:
            if self.instr:
                # Try to turn off both outputs, ignore errors
                try:
                    self.write(":OUTP OFF")
                except:
                    pass
                try:
                    self.write(":BATT:OUTP OFF")
                except:
                    pass
        except Exception as e:
            logging.error(f"An error occurred during safety shutdown: {e}")

    def close(self):
        """Closes the connection to the instrument."""
        if self.instr:
            self.instr.close()
        self.rm.close()
        logging.info("Connection closed.")

def load_profile_from_csv(file_path):
    """Loads a profile from a CSV and converts it to the required segment format."""
    logging.info(f"Loading profile from {file_path}...")
    try:
        # The CSV may have extra comment columns, so we only read time and current.
        # It also has a header row that we can skip or use. Let's use it.
        df = pd.read_csv(file_path, usecols=[0, 1])
        df.columns = ['time_s', 'current_a']  # Ensure correct column names

        if df.empty:
            logging.error("Profile CSV is empty.")
            return None

        profile_data = []
        # The CSV contains start times. The script needs segments with end times.
        for i in range(len(df)):
            current = df['current_a'].iloc[i]
            
            # The segment's end time is the start time of the next segment.
            if i + 1 < len(df):
                end_time = df['time_s'].iloc[i+1]
            else:
                # For the last segment, extrapolate duration from the previous one.
                if len(df) > 1:
                    last_duration = df['time_s'].iloc[i] - df['time_s'].iloc[i-1]
                else:
                    last_duration = 10.0  # Default duration for a single-point profile
                end_time = df['time_s'].iloc[i] + last_duration

            # The first row in the CSV is the start of the first segment.
            # Its 'time_s' is the end time for that segment.
            if i == 0:
                 # The first segment starts at t=0 and its current is defined at t=0 in the csv
                 # The end time of this first segment is the time of the second entry.
                 profile_data.append({'time_s': end_time, 'current_a': current})
            else:
                 # subsequent segments
                 profile_data.append({'time_s': end_time, 'current_a': current})


        # The logic in run_profile calculates durations based on end_times.
        # Let's adjust the generated profile to be a clean list of segments
        # with start_time, end_time, and current. No, the current logic is fine.
        
        # Re-adjust the profile to match the format expected by run_profile
        # The `time_s` should be the END of the segment.
        final_profile = []
        for i in range(len(df)):
            current = df['current_a'].iloc[i]
            if i + 1 < len(df):
                end_time = df['time_s'].iloc[i+1]
                final_profile.append({'time_s': end_time, 'current_a': current})
        
        # Handle the last segment separately.
        if len(df) > 1:
            last_start_time = df['time_s'].iloc[-1]
            last_current = df['current_a'].iloc[-1]
            prev_start_time = df['time_s'].iloc[-2]
            duration = last_start_time - prev_start_time
            last_end_time = last_start_time + duration
            final_profile.append({'time_s': last_end_time, 'current_a': last_current})
        elif len(df) == 1:
            # Single point profile, assume 10s duration
            final_profile.append({'time_s': df['time_s'].iloc[0] + 10.0, 'current_a': df['current_a'].iloc[0]})


        logging.info(f"Profile loaded: {final_profile}")
        return final_profile

    except FileNotFoundError:
        logging.error(f"Profile file not found: {file_path}")
        return None
    except Exception as e:
        logging.error(f"Failed to load or parse profile CSV: {e}", exc_info=True)
        return None

def main():
    """Main program execution."""
    # Load profile from CSV file
    profile_csv_path = Path(__file__).parent.parent.parent / 'profile_simple.csv'
    profile_data = load_profile_from_csv(profile_csv_path)
    
    if not profile_data:
        logging.error("Exiting due to profile loading failure.")
        return

    keithley = Keithley2281S()
    
    if not keithley.connect():
        return

    try:
        keithley.initialize()
        keithley.run_profile(profile_data)
    except Exception as e:
        logging.error(f"A critical error occurred: {e}", exc_info=True)
    finally:
        keithley.safety_shutdown()
        keithley.close()

if __name__ == "__main__":
    main()
