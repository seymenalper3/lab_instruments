#!/usr/bin/env python3
"""
Test Different Measurement Command Formats
"""

import serial
import time

class MeasurementTester:
    def __init__(self, port='/dev/ttyUSB0'):
        self.ser = serial.Serial(
            port=port, baudrate=115200, bytesize=8, 
            parity='N', stopbits=1, timeout=2,  # Longer timeout
            xonxoff=False, rtscts=False, dsrdtr=False
        )
        time.sleep(1)
        self.ser.flushInput()
        self.ser.flushOutput()
        
    def send(self, cmd):
        """Send command to device"""
        self.ser.write((cmd + '\r\n').encode())
        time.sleep(0.5)  # Longer delay
        
    def query(self, cmd):
        """Send query and get response"""
        print(f"Testing: {cmd}")
        self.send(cmd)
        response = self.ser.readline().decode().strip()
        print(f"  Response: '{response}' (length: {len(response)})")
        return response
    
    def test_all_measurement_formats(self):
        """Test different measurement command formats"""
        print("=== MEASUREMENT COMMAND FORMAT TEST ===")
        
        # Test different formats
        formats_to_test = [
            # Original working formats
            'MEAS:VOLT?',
            'MEAS:CURR?', 
            'MEAS:POW?',
            
            # Official documentation formats
            'MEAS:VOLTage?',
            'MEAS:CURRent?',
            'MEAS:POWer?',
            
            # Alternative formats
            'MEASure:VOLTage?',
            'MEASure:CURRent?',
            'MEASure:POWer?',
            
            # Try without colon
            'MEAS VOLT?',
            'MEAS CURR?',
            'MEAS POW?',
        ]
        
        results = {}
        for cmd in formats_to_test:
            try:
                response = self.query(cmd)
                results[cmd] = response
                if response and response != '':
                    try:
                        value = float(response)
                        print(f"  ✅ SUCCESS: {value}")
                    except ValueError:
                        print(f"  ⚠️  Non-numeric: {response}")
                else:
                    print(f"  ❌ Empty response")
            except Exception as e:
                print(f"  ❌ Error: {e}")
                results[cmd] = f"ERROR: {e}"
            
            time.sleep(0.2)
        
        print(f"\n=== SUMMARY ===")
        for cmd, result in results.items():
            if result and result != '' and not result.startswith('ERROR'):
                print(f"✅ {cmd} → {result}")
        
        return results
    
    def test_parameter_setting(self):
        """Test parameter setting for 12V 1A"""
        print(f"\n=== PARAMETER SETTING TEST (12V 1A) ===")
        
        # Test old formats first
        old_commands = [
            'CURR 1.0',
            'VOLT 12.0',
        ]
        
        for cmd in old_commands:
            print(f"Testing: {cmd}")
            self.send(cmd)
            print("  Sent (no response expected)")
        
        # Enable load
        print("Enabling load...")
        self.send('LOAD ON')
        time.sleep(1)
        
        # Check if load is enabled
        load_status = self.query('LOAD?')
        print(f"Load status: {load_status}")
        
        # Try to read measurements
        print("Reading measurements after parameter set:")
        working_commands = ['MEAS:VOLT?', 'MEAS:CURR?', 'MEAS:POW?']  # Use original format
        
        for cmd in working_commands:
            try:
                response = self.query(cmd)
                if response:
                    value = float(response)
                    print(f"  {cmd} = {value}")
            except:
                print(f"  {cmd} failed")
        
        # Disable load
        self.send('LOAD OFF')
    
    def close(self):
        self.ser.close()

def run_test():
    tester = MeasurementTester()
    
    try:
        # Test measurement formats
        results = tester.test_all_measurement_formats()
        
        # Test parameter setting
        tester.test_parameter_setting()
        
    finally:
        tester.close()

if __name__ == "__main__":
    run_test()
