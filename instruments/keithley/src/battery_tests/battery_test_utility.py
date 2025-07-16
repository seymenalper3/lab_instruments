#!/usr/bin/env python3
"""
Connection test utility for Keithley 2281S
Tests basic connectivity and battery test mode functions
"""

import pyvisa
import time
import sys

def test_connection():
    """Test basic instrument connection"""
    print("=" * 60)
    print("Keithley 2281S Connection Test")
    print("=" * 60)
    
    # List resources
    print("\n1. Searching for instruments...")
    try:
        rm = pyvisa.ResourceManager('@py')
        resources = rm.list_resources()
        print(f"Found {len(resources)} resources:")
        for r in resources:
            print(f"  - {r}")
    except Exception as e:
        print(f"ERROR: Failed to list resources: {e}")
        return False
    
    # Find Keithley
    keithley = None
    for r in resources:
        if '1510' in r and '8833' in r:  # Keithley vendor/product ID
            keithley = r
            break
    
    if not keithley:
        print("\nERROR: No Keithley 2281S found!")
        print("Please check:")
        print("  - USB cable is connected")
        print("  - Instrument is powered on")
        print("  - USB drivers are installed")
        return False
    
    print(f"\n2. Connecting to: {keithley}")
    
    # Connect
    try:
        inst = rm.open_resource(keithley)
        inst.read_termination = '\n'
        inst.write_termination = '\n'
        inst.timeout = 5000
        
        # Clear device
        try:
            inst.clear()
        except:
            pass  # Some instruments don't support clear
        
        # Get ID
        inst.write('*CLS')
        idn = inst.query('*IDN?').strip()
        print(f"Connected to: {idn}")
        
        # Set remote mode
        inst.write('SYST:REM')
        print("Instrument set to remote mode")
        
    except Exception as e:
        print(f"ERROR: Failed to connect: {e}")
        return False
    
    print("\n3. Testing battery test mode...")
    
    try:
        # Check if we can query status
        status = inst.query(':STAT:OPER:INST:ISUM:COND?').strip()
        print(f"Status register: {status}")
        
        # Check output state
        output = inst.query(':OUTP?').strip()
        print(f"Output state: {'ON' if output == '1' else 'OFF'}")
        
        # Try to get buffer points
        try:
            points = inst.query(':TRACe:POINts:ACTual?').strip()
            print(f"Buffer points: {points}")
        except:
            print("Buffer points: Not available")
        
        print("\n4. Testing measurement capabilities...")
        
        # Try different measurement methods
        print("Testing measurement commands:")
        
        # Method 1: Direct measurement
        try:
            v = inst.query(':MEAS:VOLT?').strip()
            print(f"  :MEAS:VOLT? = {v}")
        except Exception as e:
            print(f"  :MEAS:VOLT? = Failed ({str(e)[:50]}...)")
        
        # Method 2: Buffer data
        try:
            inst.write(':TRACe:CLEar')
            time.sleep(0.5)
            data = inst.query(':BATT:DATA:DATA:SEL? 1,1,"VOLT,CURR"').strip()
            print(f"  Buffer data = {data if data else 'Empty'}")
        except Exception as e:
            print(f"  Buffer data = Failed ({str(e)[:50]}...)")
        
        print("\n5. Battery test mode configuration...")
        
        # Try to set discharge mode
        try:
            inst.write(':BATT:TEST:MODE DIS')
            mode = inst.query(':BATT:TEST:MODE?').strip()
            print(f"  Test mode: {mode}")
        except Exception as e:
            print(f"  Test mode: Failed ({str(e)[:50]}...)")
        
        # Check available model slots
        try:
            slots = inst.query(':BATT:TEST:SENS:AH:GMOD:CAT?').strip()
            print(f"  Model slots in use: {slots if slots else 'None'}")
        except:
            print("  Model slots: Query not supported")
        
    except Exception as e:
        print(f"ERROR during tests: {e}")
    
    finally:
        # Return to local mode
        try:
            inst.write(':BATT:OUTP OFF')
            inst.write('SYST:LOC')
            print("\n6. Returned to local mode")
        except:
            pass
        
        inst.close()
        rm.close()
    
    print("\n" + "=" * 60)
    print("Connection test completed successfully!")
    print("=" * 60)
    return True


def test_quick_measurement():
    """Perform a quick measurement test"""
    print("\n" + "=" * 60)
    print("Quick Measurement Test")
    print("=" * 60)
    
    response = input("\nConnect a battery and press Enter to continue (or 'q' to quit): ")
    if response.lower() == 'q':
        return
    
    try:
        rm = pyvisa.ResourceManager('@py')
        keithley = None
        for r in rm.list_resources():
            if '1510' in r and '8833' in r:
                keithley = r
                break
        
        if not keithley:
            print("ERROR: No Keithley 2281S found!")
            return
        
        inst = rm.open_resource(keithley)
        inst.read_termination = '\n'
        inst.write_termination = '\n'
        inst.timeout = 10000
        
        print("Configuring instrument...")
        inst.write('*CLS')
        inst.write('SYST:REM')
        
        # Set battery test mode
        inst.write(':BATT:TEST:MODE DIS')
        
        # Configure for Voc/ESR measurement
        inst.write(':BATT:TEST:SENS:EVOC:DELA 0.5')
        
        print("Measuring Voc and ESR...")
        result = inst.query(':BATT:TEST:MEAS:EVOC?').strip()
        
        if result:
            parts = result.split(',')
            if len(parts) >= 2:
                voc = float(parts[0])
                esr = float(parts[1])
                print(f"\nMeasurement Results:")
                print(f"  Open Circuit Voltage (Voc): {voc:.3f} V")
                print(f"  Equivalent Series Resistance (ESR): {esr:.3f} Ω")
            else:
                print(f"Unexpected result format: {result}")
        else:
            print("No measurement result received")
        
        inst.write('SYST:LOC')
        inst.close()
        rm.close()
        
    except Exception as e:
        print(f"ERROR: {e}")


def main():
    """Main test menu"""
    while True:
        print("\n" + "=" * 60)
        print("Keithley 2281S Test Utilities")
        print("=" * 60)
        print("1. Test connection and basic functions")
        print("2. Quick battery measurement (Voc/ESR)")
        print("3. Exit")
        
        choice = input("\nSelect option (1-3): ")
        
        if choice == '1':
            test_connection()
        elif choice == '2':
            test_quick_measurement()
        elif choice == '3':
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()
