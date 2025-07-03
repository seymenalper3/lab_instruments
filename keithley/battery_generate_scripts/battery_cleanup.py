#!/usr/bin/env python3
"""
Cleanup script to reset Keithley 2281S before battery test
"""

import pyvisa
import time

def cleanup_instrument():
    """Reset instrument to clean state"""
    print("Cleaning up Keithley 2281S...")
    
    try:
        # Connect
        rm = pyvisa.ResourceManager('@py')
        inst = rm.open_resource('USB0::1510::8833::4587429::0::INSTR')
        inst.read_termination = '\n'
        inst.write_termination = '\n'
        inst.timeout = 5000
        
        print("Connected to instrument")
        
        # Clear and reset
        print("Resetting instrument...")
        inst.write('*CLS')  # Clear status
        inst.write('*RST')  # Reset to default
        time.sleep(2)
        
        # Set to remote mode
        inst.write('SYST:REM')
        
        # Clear all buffers
        print("Clearing buffers...")
        try:
            inst.write(':BATT1:DATA:CLE')
            inst.write(':BATT:DATA:CLE')
            inst.write(':TRACe:CLEar')
            inst.write(':DATA:CLE')
        except:
            pass  # Some commands might not be available in all modes
        
        # Make sure output is OFF
        inst.write(':OUTP OFF')
        inst.write(':BATT:OUTP OFF')
        
        # Set battery test mode
        print("Setting battery test mode...")
        inst.write(':BATT:TEST:MODE DIS')
        
        # Verify status
        time.sleep(1)
        try:
            status = inst.query(':STAT:OPER:INST:ISUM:COND?').strip()
            output = inst.query(':OUTP?').strip()
            points = inst.query(':TRACe:POINts:ACTual?').strip()
            
            print(f"\nStatus after cleanup:")
            print(f"  Status register: {status}")
            print(f"  Output: {'ON' if output == '1' else 'OFF'}")
            print(f"  Buffer points: {points}")
            
        except Exception as e:
            print(f"Status check error: {e}")
        
        # Return to local
        inst.write('SYST:LOC')
        inst.close()
        rm.close()
        
        print("\nCleanup completed! Instrument is ready for battery test.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    return True

if __name__ == "__main__":
    cleanup_instrument()
