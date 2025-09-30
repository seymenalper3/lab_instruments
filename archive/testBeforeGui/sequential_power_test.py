#!/usr/bin/env python3
"""
Sequential Constant Power (CP) Load Test
Applies a sequence of different power loads for specified durations.
"""

import serial
import time
import csv
from datetime import datetime

# --- Configuration ---
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200
TEST_STEPS = [
    {"label": "Step 1", "power": 70.0, "duration": 10},
    {"label": "Step 2", "power": 150.0, "duration": 10},
]
# ---------------------

def run_sequential_power_test():
    """Connects, runs a sequence of CP load tests, and disconnects."""
    ser = None
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"testBeforeGui/test_results/cp_test_{timestamp_str}.csv"

    print("=== SEQUENTIAL CP LOAD TEST ===")
    print(f"Running {len(TEST_STEPS)} steps on {SERIAL_PORT}")
    print(f"💾 Results will be saved to: {filename}")
    print("-" * 50)

    try:
        # Create CSV file and writer
        with open(filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            # Write header row
            csv_writer.writerow(['timestamp_iso', 'elapsed_s', 'step_label', 'target_power_W', 'voltage_V', 'current_A', 'power_W'])

            # 1. Connect to the device
            ser = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=2)
            print("✅ Connection established.")
            time.sleep(1)

            # Set CP mode once at the beginning
            ser.write(b'MODE CP\r\n')
            time.sleep(0.2)
            print("✅ Mode set to CP.")

            # Loop through each test step
            for step in TEST_STEPS:
                target_power = step["power"]
                duration = step["duration"]
                label = step["label"]

                print(f"\n--- Starting {label}: {target_power}W for {duration}s ---")

                # 2. Set power for the current step (ASSUMING CP:HIGH command)
                command = f'CP:HIGH {target_power}\r\n'.encode()
                ser.write(command)
                time.sleep(0.2)
                print(f"✅ Power target set to {target_power}W (using assumed command).")

                # 3. Start the load for this step
                ser.write(b'LOAD ON\r\n')
                start_time = time.time()
                
                print("Time  | Voltage | Current | Power")
                print("-------------------------------------")

                while (time.time() - start_time) < duration:
                    elapsed = time.time() - start_time
                    
                    # Request measurements
                    ser.write(b'MEAS:VOLT?\r\n')
                    time.sleep(0.1)
                    voltage = ser.readline().decode().strip()
                    
                    ser.write(b'MEAS:CURR?\r\n')
                    time.sleep(0.1)
                    current = ser.readline().decode().strip()

                    ser.write(b'MEAS:POW?\r\n')
                    time.sleep(0.1)
                    power = ser.readline().decode().strip()
                    
                    print(f"{elapsed:04.1f}s | {voltage:>7}V | {current:>9}A | {power:>7}W")
                    
                    # Write data to CSV
                    csv_writer.writerow([
                        datetime.now().isoformat(),
                        f"{elapsed:.2f}",
                        label,
                        target_power,
                        voltage,
                        current,
                        power
                    ])
                    
                    # Wait before next reading
                    time.sleep(max(0, 0.7 - (time.time() - start_time - elapsed)))

                print("-------------------------------------")
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
            ser.write(b'LOAD OFF\r\n')
            ser.close()
            print("✅ Load disabled. Connection closed.")
        
        print("\n=== TEST FINISHED ===")

if __name__ == "__main__":
    run_sequential_power_test()
