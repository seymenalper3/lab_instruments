#!/usr/bin/env python3
"""
Realistic 9V Source Testing
Test what we CAN do with 9V source
"""

import serial
import time

class Realistic9VTest:
    def __init__(self, port='/dev/ttyUSB0'):
        self.ser = serial.Serial(
            port=port, baudrate=115200, bytesize=8, 
            parity='N', stopbits=1, timeout=2,
            xonxoff=False, rtscts=False, dsrdtr=False
        )
        time.sleep(1)
        self.ser.flushInput()
        self.ser.flushOutput()
        
    def send(self, cmd):
        self.ser.write((cmd + '\r\n').encode())
        time.sleep(0.5)
        
    def query(self, cmd):
        self.send(cmd)
        return self.ser.readline().decode().strip()
    
    def get_readings(self):
        v = float(self.query('MEAS:VOLT?'))
        i = float(self.query('MEAS:CURR?'))
        p = float(self.query('MEAS:POW?'))
        return v, i, p
    
    def test_cc_mode_with_9v(self):
        """Test CC (Constant Current) mode with 9V source"""
        print("=== CC MODE TEST (9V Source) ===")
        print("Testing current draw from 9V source...")
        
        # Test different current values that 9V source can provide
        test_currents = [0.1, 0.25, 0.5, 0.75, 1.0]
        
        for target_i in test_currents:
            print(f"\n--- Testing {target_i}A Current Draw ---")
            
            # Reset
            self.send('LOAD OFF')
            time.sleep(0.2)
            
            # Set CC mode
            self.send('MODE CC')
            time.sleep(0.2)
            
            # Set current
            self.send(f'CURR {target_i}')
            time.sleep(0.2)
            
            # Measure before load
            v_before, i_before, p_before = self.get_readings()
            print(f"Before: {v_before:.3f}V, {i_before:.3f}A")
            
            # Enable load
            self.send('LOAD ON')
            time.sleep(1)
            
            # Measure with load
            v_after, i_after, p_after = self.get_readings()
            mode = self.query('MODE?')
            load_status = self.query('LOAD?')
            
            print(f"After:  {v_after:.3f}V, {i_after:.6f}A, {p_after:.3f}W")
            print(f"Mode: {mode}, Load: {load_status}")
            
            # Check for voltage drop (indicates working)
            v_drop = v_before - v_after
            if v_drop > 0.1:
                print(f"✅ Voltage drop: {v_drop:.3f}V - Load is working!")
            else:
                print(f"❌ No significant voltage drop")
            
            if i_after > 0.01:
                print(f"🎉 SUCCESS: Drawing {i_after:.3f}A!")
                break
    
    def test_cv_mode_realistic(self):
        """Test CV mode with realistic voltage (lower than source)"""
        print(f"\n=== CV MODE TEST (Realistic) ===")
        print("Testing CV mode with voltage LOWER than source...")
        
        # 9V source can provide these CV voltages
        test_voltages = [6.0, 7.0, 8.0, 8.5]
        
        for target_v in test_voltages:
            print(f"\n--- Testing CV {target_v}V ---")
            
            self.send('LOAD OFF')
            time.sleep(0.2)
            
            # Set CV mode  
            self.send('MODE CV')
            time.sleep(0.2)
            
            # Set voltage (lower than 9V source)
            self.send(f'VOLT {target_v}')
            time.sleep(0.2)
            
            # Enable load
            self.send('LOAD ON')
            time.sleep(1)
            
            v, i, p = self.get_readings()
            mode = self.query('MODE?')
            
            print(f"Result: {v:.3f}V, {i:.6f}A, {p:.3f}W (Mode: {mode})")
            
            if abs(v - target_v) < 0.5 and i > 0.01:
                print(f"✅ CV mode working! Regulated to {v:.3f}V")
            else:
                print(f"❌ CV mode not working properly")
    
    def test_impossible_cv_mode(self):
        """Demonstrate what happens when CV voltage > source voltage"""
        print(f"\n=== IMPOSSIBLE CV MODE DEMO ===")
        print("Showing what happens when CV voltage > source voltage...")
        
        # Try to set CV to 12V with 9V source (impossible)
        self.send('LOAD OFF')
        time.sleep(0.2)
        
        print("Setting CV mode to 12V (higher than 9V source)...")
        self.send('MODE CV')
        self.send('VOLT 12.0')
        time.sleep(0.2)
        
        v_before, _, _ = self.get_readings()
        print(f"Before load: {v_before:.3f}V")
        
        self.send('LOAD ON')
        time.sleep(1)
        
        v_after, i_after, p_after = self.get_readings()
        print(f"With load:   {v_after:.3f}V, {i_after:.6f}A, {p_after:.3f}W")
        
        print("RESULT: Load cannot create 12V from 9V source!")
        print("The load will just be at source voltage (~9V)")
    
    def test_power_mode(self):
        """Test CP (Constant Power) mode"""
        print(f"\n=== CP MODE TEST ===")
        print("Testing constant power draw from 9V source...")
        
        # Test reasonable power levels for 9V source
        test_powers = [2.0, 5.0, 8.0]  # Watts
        
        for target_p in test_powers:
            print(f"\n--- Testing {target_p}W Power ---")
            
            self.send('LOAD OFF')
            time.sleep(0.2)
            
            self.send('MODE CP')
            time.sleep(0.2)
            
            self.send(f'POW {target_p}')
            time.sleep(0.2)
            
            self.send('LOAD ON')
            time.sleep(1)
            
            v, i, p = self.get_readings()
            expected_current = target_p / v if v > 0 else 0
            
            print(f"Result: {v:.3f}V, {i:.6f}A, {p:.3f}W")
            print(f"Expected current: {expected_current:.3f}A")
            
            if abs(p - target_p) < 1.0:
                print(f"✅ CP mode working!")
            else:
                print(f"❌ CP mode not achieving target power")
    
    def run_all_realistic_tests(self):
        """Run all realistic tests with 9V source"""
        print("=== 9V SOURCE REALISTIC TESTING ===")
        print("Testing what we CAN do with 9V source...")
        
        try:
            # Test CC mode (most likely to work)
            self.test_cc_mode_with_9v()
            
            # Test realistic CV mode
            self.test_cv_mode_realistic()
            
            # Demonstrate impossible CV
            self.test_impossible_cv_mode()
            
            # Test power mode
            self.test_power_mode()
            
        finally:
            self.send('LOAD OFF')
    
    def close(self):
        self.ser.close()

def main():
    print("=== UNDERSTANDING ELECTRONIC LOAD ===")
    print("Electronic Load = Power Consumer (not power source!)")
    print("- Can only draw current from existing voltage")
    print("- Cannot boost 9V to 12V")
    print("- CV mode regulates load voltage (if source > target)")
    print()
    
    tester = Realistic9VTest()
    
    try:
        tester.run_all_realistic_tests()
        
        print(f"\n📋 SUMMARY:")
        print("✅ CC Mode: Draw specified current from any voltage")
        print("✅ CV Mode: Regulate load voltage (if source allows)")
        print("✅ CP Mode: Draw specified power")
        print("❌ Cannot create higher voltage than source!")
        
    finally:
        tester.close()

if __name__ == "__main__":
    main()
