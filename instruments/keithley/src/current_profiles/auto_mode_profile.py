#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keithley 2281S Automatic Mode-Switching Profile Script

This script applies a current profile from a CSV file with automatic
mode switching between Power Supply (charge) and Battery Test (discharge) modes.
"""

import pyvisa
import pandas as pd
import time
from pathlib import Path
import csv
from datetime import datetime

# --- Configuration ---
RESOURCE_ADDR = 'USB0::1510::8833::4587429::0::INSTR'
PROFILE_CSV = Path(__file__).parent.parent.parent / 'current_profile_10s.csv'
DISCHARGE_CURRENT = 1.0  # Constant discharge current (Amps) for all negative segments
VOLTAGE_CHARGE = 4.2     # Charging voltage (V)
VOLTAGE_PROTECTION = 4.3 # Protection voltage (V)
MODE_SWITCH_DELAY = 3.0  # Delay after mode switch (seconds)


class AutoKeithleySwitcher:
    """Manages the connection and execution with automatic mode switching."""

    def __init__(self, resource_addr):
        self.resource_addr = resource_addr
        self.rm = pyvisa.ResourceManager('@py')
        self.inst = None
        self.log = []  # Log listesi
        self.start_time = None
        self.current_mode = None

    def start_timer(self):
        self.start_time = time.time()

    def elapsed(self):
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def log_segment(self, step, mode, set_current, measured_v, measured_i, elapsed, status):
        self.log.append({
            'step': step,
            'mode': mode,
            'set_current_a': set_current,
            'measured_voltage_v': measured_v,
            'measured_current_a': measured_i,
            'elapsed_time_s': elapsed,
            'status': status
        })

    def save_log_csv(self):
        if not self.log:
            print("No log data to save.")
            return
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f'auto_profile_log_{ts}.csv'
        with open(fname, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(self.log[0].keys()))
            writer.writeheader()
            for row in self.log:
                writer.writerow(row)
        print(f"\nLog saved to: {fname}")

    def connect_and_prep(self):
        """Connects to the instrument and prepares it for commands."""
        try:
            if self.inst is None:
                print("Connecting to instrument...")
                self.inst = self.rm.open_resource(self.resource_addr)
                self.inst.read_termination = '\n'
                self.inst.write_termination = '\n'
                self.inst.timeout = 30000
                self.inst.write('*CLS')
                print(f"Connected: {self.inst.query('*IDN?').strip()}")
            return True
        except pyvisa.errors.VisaIOError as e:
            print(f"!!! Connection Failed: {e}")
            return False

    def close_connection(self):
        """Closes the instrument connection."""
        if self.inst:
            try:
                self.inst.write(':OUTP OFF')  # Turn off output before closing
                self.inst.write(':BATT:OUTP OFF')  # Turn off battery output too
                self.inst.close()
                print("Connection closed.")
            except Exception as e:
                print(f"Could not close connection properly: {e}")
        self.inst = None
        self.current_mode = None

    def switch_to_power_supply_mode(self):
        """Switches instrument to Power Supply mode for charging."""
        if self.current_mode == 'power':
            return True
            
        print("Switching to Power Supply mode...")
        try:
            # Turn off any outputs first
            self.inst.write(':OUTP OFF')
            self.inst.write(':BATT:OUTP OFF')
            time.sleep(0.5)
            
            # Switch to Power Supply mode
            self.inst.write(':ENTRy:FUNC POWer')
            time.sleep(MODE_SWITCH_DELAY)
            
            # Verify mode switch
            current_func = self.inst.query(':ENTRy:FUNC?').strip()
            if current_func.upper() != 'POWER':
                print(f"Warning: Expected POWER mode, got {current_func}")
            
            self.current_mode = 'power'
            print("Successfully switched to Power Supply mode")
            return True
        except Exception as e:
            print(f"!!! Failed to switch to Power Supply mode: {e}")
            return False

    def switch_to_battery_test_mode(self):
        """Switches instrument to Battery Test mode for discharging."""
        if self.current_mode == 'test':
            return True
            
        print("Switching to Battery Test mode...")
        try:
            # Turn off any outputs first
            self.inst.write(':OUTP OFF')
            self.inst.write(':BATT:OUTP OFF')
            time.sleep(0.5)
            
            # Switch to Battery Test mode
            self.inst.write(':ENTRy:FUNC TEST')
            time.sleep(MODE_SWITCH_DELAY)
            
            # Verify mode switch
            current_func = self.inst.query(':ENTRy:FUNC?').strip()
            if current_func.upper() != 'TEST':
                print(f"Warning: Expected TEST mode, got {current_func}")
            
            self.current_mode = 'test'
            print("Successfully switched to Battery Test mode")
            return True
        except Exception as e:
            print(f"!!! Failed to switch to Battery Test mode: {e}")
            return False

    def run_charge_segments(self, segments, step_offset=0):
        """Executes charging segments in Power Supply mode."""
        if not self.connect_and_prep():
            return

        if not self.switch_to_power_supply_mode():
            print("Failed to switch to Power Supply mode, skipping charge segments")
            return

        print(f"--- Executing Batch of {len(segments)} CHARGE segments ---")
        try:
            # Configure voltage settings
            self.inst.write(f':VOLT {VOLTAGE_CHARGE}')
            self.inst.write(f':VOLT:PROT {VOLTAGE_PROTECTION}')
            self.inst.write(':OUTP ON')
            print(f"Output ON. Charge voltage: {VOLTAGE_CHARGE}V, Protection: {VOLTAGE_PROTECTION}V")

            for i, segment in enumerate(segments):
                current = segment['current_a']
                duration = segment['duration_s']
                step_no = step_offset + i + 1
                print(f"  -> Segment {step_no}: Applying {current:.3f}A for {duration:.2f}s")
                
                # Set current
                self.inst.write(f':CURR {current}')  # Use exact current value
                if i == 0:
                    self.inst.write(':SYST:KEY 2')  # Only first segment
                
                # Take measurement using manual script's approach
                try:
                    meas = self.inst.query(':MEAS:VOLT?').strip()
                    parts = [x.strip() for x in meas.split(',')]
                    if len(parts) >= 2:
                        measured_i = float(parts[0].replace('A','').replace('V','').strip())
                        measured_v = float(parts[1].replace('A','').replace('V','').strip())
                    else:
                        # Single value response - determine if it's voltage or current
                        if 'A' in meas:
                            measured_i = float(meas.replace('A','').replace('V','').strip())
                            v_resp = self.inst.query(':MEAS:VOLT?').strip()
                            measured_v = float(v_resp.replace('A','').replace('V','').strip())
                        else:
                            measured_v = float(meas.replace('A','').replace('V','').strip())
                            i_resp = self.inst.query(':MEAS:CURR?').strip()
                            measured_i = float(i_resp.replace('A','').replace('V','').strip())
                    print(f"    Measurement: {meas}")
                    self.log_segment(step_no, 'charge', current, measured_v, measured_i, self.elapsed(), 'OK')
                except Exception as e:
                    print(f"    Measurement failed: {e}")
                    self.log_segment(step_no, 'charge', current, 'ERROR', 'ERROR', self.elapsed(), f'ERROR: {e}')
                
                time.sleep(duration)
                
        except Exception as e:
            print(f"!!! ERROR during charge batch: {e}")
        finally:
            try:
                self.inst.write(':OUTP OFF')
            except:
                pass
        print("--- Charge batch finished ---")

    def run_discharge_segments(self, segments, step_offset=0):
        """Executes discharge segments in Battery Test mode."""
        if not self.connect_and_prep():
            return

        if not self.switch_to_battery_test_mode():
            print("Failed to switch to Battery Test mode, skipping discharge segments")
            return

        print(f"--- Executing Batch of {len(segments)} DISCHARGE segments ---")
        try:
            # Configure battery test for discharge (same as manual script)
            self.inst.write(':BATT:TEST:MODE DIS')
            self.inst.write(f':BATT:TEST:CURR:LIM:SOUR {DISCHARGE_CURRENT}')
            self.inst.write(':BATT:OUTP ON')
            print(f"Output ON. Applying constant {DISCHARGE_CURRENT}A discharge...")

            for i, segment in enumerate(segments):
                duration = segment['duration_s']
                step_no = step_offset + i + 1
                print(f"  -> Segment {step_no}: Waiting for {duration:.2f}s")
                
                # Take measurement using manual script's buffer approach
                retry_count = 0
                max_retries = 3
                measured_v = measured_i = rel = None
                
                while retry_count < max_retries:
                    try:
                        buf = self.inst.query(':BATT:DATA:DATA? "VOLT,CURR,REL"').strip()
                        vals = [float(x) for x in buf.split(',')[-3:]] if buf else [None, None, None]
                        if len(vals) == 3 and all(v is not None for v in vals):
                            measured_v, measured_i, rel = vals
                            print(f"    Measurement: V={measured_v}, I={measured_i}, REL={rel}")
                            self.log_segment(step_no, 'discharge', DISCHARGE_CURRENT, measured_v, measured_i, self.elapsed(), 'OK')
                            break
                        else:
                            raise ValueError("No valid data from buffer")
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"    Measurement failed (attempt {retry_count}), retrying in 1s...")
                            time.sleep(1)
                        else:
                            print(f"    Measurement failed after {max_retries} attempts: {e}")
                            self.log_segment(step_no, 'discharge', DISCHARGE_CURRENT, 'ERROR', 'ERROR', self.elapsed(), f'ERROR: {e}')
                
                time.sleep(duration)
                
        except Exception as e:
            print(f"!!! ERROR during discharge batch: {e}")
        finally:
            try:
                self.inst.write(':BATT:OUTP OFF')
            except:
                pass
        print("--- Discharge batch finished ---")


def load_profile(csv_path):
    """Loads a profile CSV and calculates segment durations."""
    print(f"Loading profile from: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        # Calculate durations. The time in the CSV is the START time of the segment.
        df['duration_s'] = df['time_s'].diff().shift(-1)
        # For the last row, use the duration of the second to last row as an estimate
        if pd.isna(df['duration_s'].iloc[-1]):
             if len(df) > 1:
                 df.loc[df.index[-1], 'duration_s'] = df['duration_s'].iloc[-2]
             else:
                 df.loc[df.index[-1], 'duration_s'] = 1.0 # Default 1s for single point profile
        print(f"Profile loaded successfully: {len(df)} segments")
        return df
    except FileNotFoundError:
        print(f"!!! Profile file not found: {csv_path}")
        return None
    except Exception as e:
        print(f"!!! Failed to load profile: {e}")
        return None


def main():
    """Main execution function."""
    profile_df = load_profile(PROFILE_CSV)
    if profile_df is None:
        print("Exiting due to profile loading error.")
        return

    controller = AutoKeithleySwitcher(RESOURCE_ADDR)
    controller.start_timer()

    print("\n🚀 Starting profile execution with AUTOMATIC mode switching...")
    print(f"Total segments: {len(profile_df)}")
    print(f"Mode switch delay: {MODE_SWITCH_DELAY}s")

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
                    controller.run_charge_segments(segment_chunk, step_offset)
                else:
                    controller.run_discharge_segments(segment_chunk, step_offset)
                
                step_offset += len(segment_chunk)
                segment_chunk = []

            # Add current segment to chunk (skip sentinel)
            if index < len(profile_df):
                segment_chunk.append(row)
            
            last_mode = current_mode

    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
    finally:
        controller.close_connection()
        controller.save_log_csv()

    print("\n\n✅✅✅ Profile execution completed. ✅✅✅")


if __name__ == '__main__':
    main()