#!/usr/bin/env python3
"""
Simple test to verify Keithley 2281S current output
"""

import pyvisa
import time

# Connect to instrument
rm = pyvisa.ResourceManager('@py')
inst = rm.open_resource('USB0::1510::8833::4587429::0::INSTR')
inst.read_termination = '\n'
inst.write_termination = '\n'
inst.timeout = 10000

print("Testing Keithley 2281S current output...")

try:
    # Initialize
    inst.write('*RST')
    time.sleep(2)
    inst.write('*CLS')
    
    # Get ID
    idn = inst.query('*IDN?').strip()
    print(f"Connected to: {idn}")
    
    # Check if output is already on
    output_state = inst.query(':OUTP?').strip()
    print(f"Initial output state: {'ON' if output_state == '1' else 'OFF'}")
    
    # Simple power supply test
    print("\nTesting power supply mode...")
    inst.write(':VOLT 3.7')      # Safe voltage
    inst.write(':VOLT:PROT 4.2') # Protection
    inst.write(':CURR 0.5')      # 0.5A current
    
    print("Turning output ON...")
    inst.write(':OUTP ON')
    
    # Check if output turned on
    output_state = inst.query(':OUTP?').strip()
    print(f"Output state after ON command: {'ON' if output_state == '1' else 'OFF'}")
    
    # Wait 5 seconds
    print("Waiting 5 seconds...")
    time.sleep(5)
    
    # Try to measure
    try:
        voltage = inst.query(':MEAS:VOLT?').strip()
        print(f"Measured voltage: {voltage}")
    except Exception as e:
        print(f"Voltage measurement failed: {e}")
    
    # Turn off
    print("Turning output OFF...")
    inst.write(':OUTP OFF')
    
    # Final check
    output_state = inst.query(':OUTP?').strip()
    print(f"Final output state: {'ON' if output_state == '1' else 'OFF'}")
    
    # Check for errors
    error = inst.query('SYST:ERR?').strip()
    print(f"System error: {error}")
    
except Exception as e:
    print(f"Error: {e}")
    
finally:
    # Cleanup
    try:
        inst.write(':OUTP OFF')
    except:
        pass
    inst.close()
    rm.close()
    print("Test completed.") 