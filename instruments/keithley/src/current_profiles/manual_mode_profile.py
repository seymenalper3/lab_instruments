
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keithley 2281S Manual Mode-Switching Profile Script

This script applies a current profile from a CSV file, but requires the user
to manually switch the instrument's mode for charge and discharge segments.
"""

import pyvisa
import pandas as pd
import time
from pathlib import Path
import subprocess
import csv
from datetime import datetime

# --- Configuration ---
RESOURCE_ADDR = 'USB0::1510::8833::4587429::0::INSTR'
PROFILE_CSV = Path(__file__).parent.parent.parent / 'current_profile_for_sourcing.csv'
DISCHARGE_CURRENT = 1.0  # Constant discharge current (Amps) for all negative segments
VOLTAGE_CHARGE = 4.2     # Charging voltage (V)
VOLTAGE_PROTECTION = 4.3 # Protection voltage (V)


class ManualKeithleySwitcher:
    """Manages the connection and execution for manual mode switching."""

    def __init__(self, resource_addr):
        self.resource_addr = resource_addr
        self.rm = pyvisa.ResourceManager('@py')
        self.inst = None
        self.log = []  # Log listesi
        self.start_time = None

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
        fname = f'manual_profile_log_{ts}.csv'
        with open(fname, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(self.log[0].keys()))
            writer.writeheader()
            for row in self.log:
                writer.writerow(row)
        print(f"\nLog saved to: {fname}")

    def connect_and_prep(self):
        """Connects to the instrument and prepares it for a command."""
        try:
            print("\nConnecting to instrument...")
            self.inst = self.rm.open_resource(self.resource_addr)
            self.inst.read_termination = '\n'
            self.inst.write_termination = '\n'
            self.inst.timeout = 10000
            self.inst.write('*CLS')
            # self.inst.write('SYST:REM') # No remote command, user is in control
            print(f"Connected: {self.inst.query('*IDN?').strip()}")
            return True
        except pyvisa.errors.VisaIOError as e:
            print(f"!!! Connection Failed: {e}")
            return False

    def release_control(self):
        """Releases the instrument to local mode and closes the connection."""
        if self.inst:
            try:
                self.inst.write('SYST:LOC') # Release to local control
                self.inst.close()
                print("Connection closed, instrument released to local control.")
            except Exception as e:
                print(f"Could not release control properly: {e}")
        self.inst = None

    def force_local_mode(self):
        """Tries to set the instrument to local mode in a safe, isolated way (subprocess)."""
        try:
            subprocess.run([
                'python3', '-c',
                f"""import pyvisa; rm=pyvisa.ResourceManager('@py'); inst=rm.open_resource('{self.resource_addr}'); inst.write('SYST:LOC'); inst.close(); rm.close()"""
            ], timeout=5)
            print("(Cihaz local moda alındı, ön panelden mod seçebilirsiniz.)")
        except Exception as e:
            print(f"(Local moda alma denemesi başarısız: {e})")

    def prompt_for_charge(self):
        self.force_local_mode()
        print("\n" + "="*50)
        print("ACTION REQUIRED: Please set the instrument to CHARGE mode.")
        print("1. Manually switch to POWER SUPPLY mode on the front panel.")
        print("2. Verify battery connections.")
        input("   Press Enter when ready to continue...")
        print("="*50)

    def prompt_for_discharge(self):
        self.force_local_mode()
        print("\n" + "="*50)
        print("ACTION REQUIRED: Please set the instrument to BATTERY TEST mode.")
        print("1. Manually switch to BATTERY TEST mode on the front panel.")
        print("   (The script will set it to DISCHARGE automatically).")
        print("2. Verify battery connections.")
        input("   Press Enter when ready to continue...")
        print("="*50)

    def run_charge_segments(self, segments, step_offset=0):
        self.prompt_for_charge()
        print("(Mod değişimi: 5 sn bekleniyor...)")
        time.sleep(5)
        if not self.connect_and_prep():
            return

        print(f"--- Executing Batch of {len(segments)} CHARGE segments ---")
        try:
            self.inst.write(f':VOLT {VOLTAGE_CHARGE}')
            self.inst.write(f':VOLT:PROT {VOLTAGE_PROTECTION}')
            self.inst.write(':OUTP ON')
            print("Output is ON. Starting segments...")

            for i, segment in enumerate(segments):
                current = segment['current_a']
                duration = segment['duration_s']
                step_no = step_offset + i + 1
                print(f"  -> Segment {step_no}: Applying {current:.3f}A for {duration:.2f}s")
                self.inst.write(f':CURR {current}')
                if i == 0:
                    self.inst.write(':SYST:KEY 2') # Only first segment
                try:
                    # @example_profile_application.py mantığıyla ölçüm
                    meas = self.inst.query(':MEAS:VOLT?').strip()
                    parts = [x.strip() for x in meas.split(',')]
                    if len(parts) >= 2:
                        measured_i = float(parts[0].replace('A','').replace('V','').strip())
                        measured_v = float(parts[1].replace('A','').replace('V','').strip())
                    else:
                        # Tek değer varsa ayrı ayrı sorgula
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
            if self.inst:
                self.inst.write(':OUTP OFF')
            self.release_control()
        print("--- Charge batch finished ---")

    def run_discharge_segments(self, segments, step_offset=0):
        self.prompt_for_discharge()
        print("(Mod değişimi: 5 sn bekleniyor...)")
        time.sleep(5)
        if not self.connect_and_prep():
            return

        print(f"--- Executing Batch of {len(segments)} DISCHARGE segments ---")
        try:
            self.inst.write(':BATT:TEST:MODE DIS')
            self.inst.write(f':BATT:TEST:CURR:LIM:SOUR {DISCHARGE_CURRENT}')
            self.inst.write(':BATT:OUTP ON')
            print(f"Output is ON. Applying constant {DISCHARGE_CURRENT}A discharge...")

            for i, segment in enumerate(segments):
                duration = segment['duration_s']
                step_no = step_offset + i + 1
                print(f"  -> Segment {step_no}: Waiting for {duration:.2f}s")
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
            if self.inst:
                self.inst.write(':BATT:OUTP OFF')
            self.release_control()
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
        print("Profile loaded successfully.")
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

    controller = ManualKeithleySwitcher(RESOURCE_ADDR)
    controller.start_timer()

    print("\nStarting profile execution with manual mode switching...")

    last_mode = None
    segment_chunk = []
    step_offset = 0

    # Add a dummy row at the end to ensure the last chunk is processed
    sentinel = pd.DataFrame([{'current_a': 999, 'duration_s': 0}], index=[len(profile_df)])
    processing_df = pd.concat([profile_df, sentinel])

    for index, row in processing_df.iterrows():
        current = row['current_a']
        current_mode = 'charge' if current >= 0 else 'discharge'

        if current_mode != last_mode and last_mode is not None:
            print(f"\n>>> Mode change detected. Processing {len(segment_chunk)} segments in {last_mode.upper()} mode.")
            if last_mode == 'charge':
                controller.run_charge_segments(segment_chunk, step_offset)
            else:
                controller.run_discharge_segments(segment_chunk, step_offset)
            step_offset += len(segment_chunk)
            segment_chunk = []
        if index < len(profile_df):
            segment_chunk.append(row)
        last_mode = current_mode

    controller.save_log_csv()
    print("\n\n✅✅✅ Profile execution completed. ✅✅✅")


if __name__ == '__main__':
    main() 