#!/usr/bin/env python3
"""
Keithley 2281S Connection Diagnostics
Tests different connection methods and identifies available resources
"""

import pyvisa
import time
import sys

def test_connection_methods():
    """Test different PyVISA backends and connection methods"""
    print("=== KEITHLEY 2281S CONNECTION DIAGNOSTICS ===\n")
    
    # Test different backends
    backends = ['@py', '@ni', '']
    
    for backend in backends:
        print(f"Testing PyVISA backend: {backend if backend else 'default'}")
        try:
            if backend:
                rm = pyvisa.ResourceManager(backend)
            else:
                rm = pyvisa.ResourceManager()
            
            # List all available resources
            resources = rm.list_resources()
            print(f"  Available resources: {resources}")
            
            # Test common resource patterns
            test_resources = [
                'TCPIP0::169.254.31.79::inst0::INSTR',  # Current TCP/IP
                'USB0::1510::8833::4587429::0::INSTR',  # USB from utilities
                'GPIB0::1::INSTR',  # GPIB
                'ASRL1::INSTR',  # Serial
            ]
            
            # Add any detected resources
            for resource in resources:
                if resource not in test_resources:
                    test_resources.append(resource)
            
            # Test each resource
            for resource in test_resources:
                print(f"  Testing resource: {resource}")
                try:
                    inst = rm.open_resource(resource)
                    inst.timeout = 5000
                    inst.read_termination = '\n'
                    inst.write_termination = '\n'
                    
                    # Clear errors
                    inst.write('*CLS')
                    time.sleep(0.5)
                    
                    # Test basic communication
                    idn = inst.query('*IDN?').strip()
                    print(f"    ✅ SUCCESS: {idn}")
                    
                    # Test additional commands
                    try:
                        status = inst.query('*OPC?').strip()
                        print(f"    Operation complete: {status}")
                    except:
                        print(f"    Operation complete: Not supported")
                    
                    # Test function query
                    try:
                        func = inst.query(':FUNC?').strip()
                        print(f"    Current function: {func}")
                    except:
                        print(f"    Current function: Not available")
                    
                    inst.close()
                    return resource, backend  # Return first working connection
                    
                except Exception as e:
                    print(f"    ❌ FAILED: {e}")
                    
            rm.close()
            
        except Exception as e:
            print(f"  Backend error: {e}")
        
        print()
    
    return None, None

def test_specific_resource(resource, backend='@py'):
    """Test a specific resource in detail"""
    print(f"=== DETAILED TEST: {resource} ===")
    
    try:
        rm = pyvisa.ResourceManager(backend)
        inst = rm.open_resource(resource)
        inst.timeout = 10000
        inst.read_termination = '\n'
        inst.write_termination = '\n'
        
        # Basic communication test
        print("1. Basic Communication:")
        inst.write('*CLS')
        time.sleep(0.5)
        
        idn = inst.query('*IDN?').strip()
        print(f"   Device ID: {idn}")
        
        # Test various commands
        print("\n2. Command Tests:")
        
        test_commands = [
            ('*OPC?', 'Operation Complete'),
            (':FUNC?', 'Current Function'),
            (':OUTP?', 'Output State'),
            (':SYST:ERR?', 'System Error'),
            (':STAT:OPER:COND?', 'Operation Status'),
        ]
        
        for cmd, desc in test_commands:
            try:
                result = inst.query(cmd).strip()
                print(f"   {desc}: {result}")
            except Exception as e:
                print(f"   {desc}: ERROR - {e}")
        
        # Test measurement
        print("\n3. Measurement Test:")
        try:
            # Try to read measurement
            result = inst.query(':READ?').strip()
            print(f"   Read measurement: {result}")
        except Exception as e:
            print(f"   Read measurement: ERROR - {e}")
        
        # Test voltage/current measurement separately
        try:
            volt = inst.query(':MEAS:VOLT?').strip()
            print(f"   Voltage measurement: {volt}")
        except Exception as e:
            print(f"   Voltage measurement: ERROR - {e}")
        
        try:
            curr = inst.query(':MEAS:CURR?').strip()
            print(f"   Current measurement: {curr}")
        except Exception as e:
            print(f"   Current measurement: ERROR - {e}")
        
        inst.close()
        rm.close()
        
        print("\n✅ Connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("Starting Keithley 2281S connection diagnostics...\n")
    
    # Test all connection methods
    working_resource, working_backend = test_connection_methods()
    
    if working_resource:
        print(f"✅ WORKING CONNECTION FOUND!")
        print(f"   Resource: {working_resource}")
        print(f"   Backend: {working_backend}")
        print()
        
        # Test the working connection in detail
        test_specific_resource(working_resource, working_backend)
        
        # Generate code snippet
        print("\n=== CODE SNIPPET FOR YOUR SCRIPT ===")
        print(f"RESOURCE_ADDR = '{working_resource}'")
        print(f"rm = pyvisa.ResourceManager('{working_backend}')")
        print("inst = rm.open_resource(RESOURCE_ADDR)")
        print("inst.timeout = 30000")
        print("inst.read_termination = '\\n'")
        print("inst.write_termination = '\\n'")
        
    else:
        print("❌ NO WORKING CONNECTION FOUND!")
        print("\nTroubleshooting suggestions:")
        print("1. Check if the instrument is powered on")
        print("2. Verify USB/Ethernet cable connections")
        print("3. Check IP address configuration (for TCP/IP)")
        print("4. Install/update NI-VISA drivers")
        print("5. Try different connection methods (USB vs TCP/IP)")
        print("6. Check Windows Device Manager for unrecognized devices")
        
    print("\n=== DIAGNOSTIC COMPLETE ===")

if __name__ == "__main__":
    main() 