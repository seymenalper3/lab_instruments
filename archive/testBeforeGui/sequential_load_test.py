#!/usr/bin/env python3
"""
Sequential Constant Current Load Test
Applies a sequence of different current loads for specified durations.
"""

import serial
import time
import csv
from datetime import datetime

# --- Configuration ---
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200
TEST_STEPS = [
    {"label": "Step 1", "current": 3.0, "duration": 10},
    {"label": "Step 2", "current": 2.0, "duration": 10},
]
# ---------------------

def run_sequential_test():
    """Connects, runs a sequence of CC load tests, and disconnects."""
    ser = None
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"testBeforeGui/test_results/cc_test_{timestamp_str}.csv"

    print("=== SEQUENTIAL CC LOAD TEST ===")
    print(f"Running {len(TEST_STEPS)} steps on {SERIAL_PORT}")
    print(f"💾 Results will be saved to: {filename}")
    print("-" * 50)

    try:
        # Create CSV file and writer
        with open(filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            # Write header row
            csv_writer.writerow(['timestamp_iso', 'elapsed_s', 'step_label', 'target_current_A', 'voltage_V', 'current_A'])

            # 1. Connect to the device
            ser = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=2)
            print("✅ Connection established.")
            time.sleep(1)

            # Set CC mode once at the beginning
            ser.write(b'MODE CC\r\n')
            time.sleep(0.2)
            print("✅ Mode set to CC.")

            # Loop through each test step
            for step in TEST_STEPS:
                target_current = step["current"]
                duration = step["duration"]
                label = step["label"]

                print(f"\n--- Starting {label}: {target_current}A for {duration}s ---")

                # 2. Set current for the current step
                ser.write(f'CC:HIGH {target_current}\r\n'.encode())
                time.sleep(0.2)
                print(f"✅ Current target set to {target_current}A.")

                # 3. Start the load for this step
                ser.write(b'LOAD ON\r\n')
                start_time = time.time()
                
                print("Time  | Voltage | Current")
                print("---------------------------")

                while (time.time() - start_time) < duration:
                    elapsed = time.time() - start_time
                    
                    # Request measurements
                    ser.write(b'MEAS:VOLT?\r\n')
                    time.sleep(0.1)
                    voltage = ser.readline().decode().strip()
                    
                    ser.write(b'MEAS:CURR?\r\n')
                    time.sleep(0.1)
                    current = ser.readline().decode().strip()
                    
                    print(f"{elapsed:04.1f}s | {voltage:>7}V | {current:>9}A")
                    
                    # Write data to CSV
                    csv_writer.writerow([
                        datetime.now().isoformat(),
                        f"{elapsed:.2f}",
                        label,
                        target_current,
                        voltage,
                        current
                    ])
                    
                    # Wait until the next second
                    time.sleep(max(0, 1.0 - (time.time() - start_time - elapsed)))

                print("---------------------------")
                print(f"⏹️ {label} complete.")
                # Briefly turn off load between steps for safety
                ser.write(b'LOAD OFF\r\n')
                time.sleep(0.5)

    except serial.SerialException as e:
        print(f"❌ SERIAL ERROR: {e}")
    except FileNotFoundError:
        print(f"❌ FILE ERROR: Could not write to '{filename}'. Does the 'test_results' directory exist?")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
    finally:
        # 4. Cleanup
        if ser and ser.is_open:
            print("\nDisabling load and closing connection...")
            # Ensure load is off at the very end
            ser.write(b'LOAD OFF\r\n')
            ser.close()
            print("✅ Load disabled. Connection closed.")
        
        print("\n=== TEST FINISHED ===")

if __name__ == "__main__":
    run_sequential_test()
