#!/usr/bin/env python3
"""
Simple 9V Current Draw Test
Try to get ANY current reading with 9V source
"""

import serial
import time

class Simple9VTest:
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
    
    def test_gradual_current_increase(self):
        """Test gradually increasing current values"""
        print("=== 9V SOURCE CURRENT DRAW TEST ===")
        print("Trying different current values to see if ANY works...")
        
        # Start with very small currents
        test_currents = [0.1, 0.2, 0.5, 1.0, 2.0]
        
        for target_current in test_currents:
            print(f"\n--- Testing {target_current}A ---")
            
            # Reset and set mode
            self.send('LOAD OFF')
            time.sleep(0.2)
            self.send('MODE CC')  # Try explicit CC mode
            time.sleep(0.2)
            
            # Set current
            self.send(f'CURR {target_current}')
            time.sleep(0.2)
            
            # Enable load
            self.send('LOAD ON')
            time.sleep(1)  # Wait for settling
            
            # Check status
            mode = self.query('MODE?')
            load_status = self.query('LOAD?')
            error = self.query('ERR?')
            
            # Get readings
            v, i, p = self.get_readings()
            
            print(f"Mode: {mode}, Load: {load_status}, Error: {error}")
            print(f"Readings: {v:.3f}V, {i:.6f}A, {p:.3f}W")
            
            if i > 0.01:  # If we got any meaningful current
                print(f"🎉 SUCCESS! Got {i:.3f}A current draw!")
                
                # Test a few more readings to confirm
                print("Confirming with multiple readings:")
                for j in range(3):
                    time.sleep(1)
                    v, i, p = self.get_readings()
                    print(f"  Reading {j+1}: {v:.3f}V, {i:.6f}A, {p:.3f}W")
                
                return target_current, i
        
        print("\n❌ No current draw achieved with any value")
        return None, 0
    
    def test_panel_override_check(self):
        """Check if panel settings might be overriding"""
        print(f"\n=== PANEL OVERRIDE CHECK ===")
        print("The load might need panel configuration...")
        
        # Try querying various settings
        queries = [
            'SENS?',  # Sense settings
            'PRES?',  # Preset settings  
            'DYN?',   # Dynamic mode
            'SHOR?',  # Short mode
            'PROT?',  # Protection status
            'NG?',    # Status
        ]
        
        print("Current device settings:")
        for query in queries:
            try:
                response = self.query(query)
                print(f"  {query} → {response}")
            except Exception as e:
                print(f"  {query} → Error: {e}")
        
        print("\n💡 SUGGESTION:")
        print("1. Check FRONT PANEL of the device:")
        print("   - Is it in REMOTE mode?")
        print("   - Are there any error indicators?")
        print("   - Is CC mode selected on panel?")
        print("2. Try manually setting current on panel first")
        print("3. Then try remote control")
    
    def test_simple_on_off(self):
        """Test basic on/off to see if load affects voltage"""
        print(f"\n=== SIMPLE ON/OFF TEST ===")
        print("Testing if load affects source voltage at all...")
        
        # Measure with load off
        self.send('LOAD OFF')
        time.sleep(1)
        v_off, i_off, p_off = self.get_readings()
        print(f"Load OFF: {v_off:.3f}V, {i_off:.6f}A, {p_off:.3f}W")
        
        # Set a reasonable current
        self.send('CURR 0.5')
        time.sleep(0.2)
        
        # Measure with load on
        self.send('LOAD ON')
        time.sleep(2)  # Longer wait
        v_on, i_on, p_on = self.get_readings()
        print(f"Load ON:  {v_on:.3f}V, {i_on:.6f}A, {p_on:.3f}W")
        
        # Check for voltage drop (indicates load is working)
        voltage_drop = v_off - v_on
        print(f"Voltage drop: {voltage_drop:.3f}V")
        
        if abs(voltage_drop) > 0.1:
            print("✅ Voltage drop detected - load is affecting the source!")
        else:
            print("❌ No voltage drop - load may not be working")
    
    def run_all_tests(self):
        """Run all tests"""
        try:
            # Test 1: Try different currents
            working_current, actual_current = self.test_gradual_current_increase()
            
            # Test 2: Simple on/off
            self.test_simple_on_off()
            
            # Test 3: Check panel settings
            self.test_panel_override_check()
            
            if working_current:
                print(f"\n🎉 FINAL RESULT: Current draw working at {working_current}A")
                return True
            else:
                print(f"\n⚠️  FINAL RESULT: No current draw achieved")
                print("   Check panel settings and connections")
                return False
        
        finally:
            self.send('LOAD OFF')
    
    def close(self):
        self.ser.close()

def main():
    tester = Simple9VTest()
    
    try:
        success = tester.run_all_tests()
        
        if not success:
            print(f"\n📋 NEXT STEPS:")
            print("1. Check device front panel - is it in REMOTE mode?")
            print("2. Try setting current manually on panel first")
            print("3. Check for error messages on panel display")
            print("4. Verify connections are secure")
            
    finally:
        tester.close()

if __name__ == "__main__":
    main()
