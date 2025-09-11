#!/usr/bin/env python3
"""
Debug Current Reading Problem
Test different command formats and check load status
"""

from prodigit_final import Prodigit34205A
import time

def debug_current_reading():
    print("=== DEBUG CURRENT READING ===")
    
    load = Prodigit34205A()
    
    try:
        print("1. Initial Status:")
        status = load.get_status_dict()
        print(f"   Mode: {status['mode']}, Enabled: {status['enabled']}, Error: {status['error']}")
        print(f"   V={status['voltage']:.3f}V, I={status['current']:.3f}A, P={status['power']:.3f}W")
        
        print("\n2. Set Current and Check:")
        load.set_current(1.0)
        print("   Current set to 1.0A")
        
        print("\n3. Enable Load and Check Status:")
        load.enable()  # Uses INP ON + LOAD ON
        time.sleep(1)
        
        enabled = load.is_enabled()
        print(f"   Load enabled status: {enabled}")
        
        print("\n4. Take Measurements:")
        v, i, p = load.get_measurements()
        print(f"   Measurements: {v:.3f}V, {i:.3f}A, {p:.3f}W")
        
        print("\n5. Try Different Current Values:")
        for curr in [0.5, 2.0, 3.0]:
            load.set_current(curr)
            time.sleep(0.5)
            v, i, p = load.get_measurements()
            print(f"   {curr}A set -> {v:.3f}V, {i:.3f}A, {p:.3f}W")
        
        print("\n6. Check Error Code:")
        error = load.get_error()
        print(f"   Error code: {error}")
        
        print("\n7. Test Manual Commands:")
        print("   Sending LOAD ON directly...")
        load.send('LOAD ON')
        time.sleep(0.5)
        load_status = load.query('LOAD?')
        print(f"   LOAD? response: '{load_status}'")
        
        print("\n8. Final Measurements:")
        v, i, p = load.get_measurements()
        print(f"   Final: {v:.3f}V, {i:.3f}A, {p:.3f}W")
        
    finally:
        load.disable()
        load.close()
        print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_current_reading()
