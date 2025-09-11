#!/usr/bin/env python3
"""
Diagnose Why Current Reading is Zero
Test different sequences and modes
"""

import serial
import time

class CurrentDiagnostics:
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
        """Send command to device"""
        self.ser.write((cmd + '\r\n').encode())
        time.sleep(0.5)
        
    def query(self, cmd):
        """Send query and get response"""
        self.send(cmd)
        return self.ser.readline().decode().strip()
    
    def get_measurements(self):
        """Get current measurements"""
        v = float(self.query('MEAS:VOLT?'))
        i = float(self.query('MEAS:CURR?'))
        p = float(self.query('MEAS:POW?'))
        return v, i, p
    
    def print_status(self, step_name):
        """Print current device status"""
        print(f"\n--- {step_name} ---")
        mode = self.query('MODE?')
        load_status = self.query('LOAD?')
        error = self.query('ERR?')
        v, i, p = self.get_measurements()
        
        print(f"Mode: {mode}, Load: {load_status}, Error: {error}")
        print(f"V: {v:.3f}V, I: {i:.6f}A, P: {p:.3f}W")
    
    def test_sequence_1_basic(self):
        """Test basic sequence"""
        print("=== TEST 1: BASIC SEQUENCE ===")
        
        self.print_status("Initial")
        
        # Set current and enable
        self.send('CURR 1.0')
        self.send('LOAD ON')
        time.sleep(1)
        
        self.print_status("After CURR + LOAD ON")
    
    def test_sequence_2_with_mode(self):
        """Test with explicit CC mode setting"""
        print("\n=== TEST 2: WITH CC MODE ===")
        
        # Disable first
        self.send('LOAD OFF')
        time.sleep(0.5)
        
        # Set CC mode first
        self.send('MODE CC')
        time.sleep(0.5)
        self.print_status("After MODE CC")
        
        # Set current
        self.send('CURR 1.0')
        time.sleep(0.5)
        self.print_status("After CURR 1.0")
        
        # Enable load
        self.send('LOAD ON')
        time.sleep(1)
        self.print_status("After LOAD ON")
    
    def test_sequence_3_with_start(self):
        """Test with START command"""
        print("\n=== TEST 3: WITH START COMMAND ===")
        
        # Disable and reset
        self.send('LOAD OFF')
        self.send('MODE CC')
        self.send('CURR 1.0')
        time.sleep(0.5)
        
        # Enable load
        self.send('LOAD ON')
        time.sleep(0.5)
        self.print_status("Before START")
        
        # Try START command
        self.send('START')
        time.sleep(1)
        self.print_status("After START")
    
    def test_sequence_4_different_current_formats(self):
        """Test different current setting formats"""
        print("\n=== TEST 4: DIFFERENT CURRENT FORMATS ===")
        
        self.send('LOAD OFF')
        self.send('MODE CC')
        time.sleep(0.5)
        
        # Test different current formats
        current_commands = [
            'CURR 1.000',
            'CURR:LEV 1.0',  # Try with :LEV
            'CC 1.0',        # Try CC directly
        ]
        
        for cmd in current_commands:
            print(f"\nTesting: {cmd}")
            try:
                self.send(cmd)
                time.sleep(0.5)
                self.send('LOAD ON')
                time.sleep(1)
                
                v, i, p = self.get_measurements()
                print(f"  Result: {v:.3f}V, {i:.6f}A, {p:.3f}W")
                
                if i > 0.001:  # If we got current
                    print(f"  ✅ SUCCESS with {cmd}!")
                    return cmd
                
                self.send('LOAD OFF')
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Error: {e}")
        
        return None
    
    def test_sequence_5_preset_commands(self):
        """Test PRESET commands from documentation"""
        print("\n=== TEST 5: PRESET COMMANDS ===")
        
        self.send('LOAD OFF')
        time.sleep(0.5)
        
        # Try preset commands
        preset_commands = [
            'PRESET CC:LOW 1.0',
            'PRESET CC:HIGH 1.0',
        ]
        
        for cmd in preset_commands:
            print(f"\nTesting: {cmd}")
            try:
                self.send(cmd)
                time.sleep(0.5)
                
                self.send('MODE CC')
                self.send('LOAD ON')
                time.sleep(1)
                
                v, i, p = self.get_measurements()
                print(f"  Result: {v:.3f}V, {i:.6f}A, {p:.3f}W")
                
                if i > 0.001:
                    print(f"  ✅ SUCCESS with {cmd}!")
                    return cmd
                
                self.send('LOAD OFF')
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Error with {cmd}: {e}")
        
        return None
    
    def test_all_sequences(self):
        """Run all test sequences"""
        print("=== CURRENT DRAW DIAGNOSTICS ===")
        print("Target: 1A current from 15V DC source")
        
        # Run all tests
        self.test_sequence_1_basic()
        self.test_sequence_2_with_mode()
        self.test_sequence_3_with_start()
        
        working_cmd = self.test_sequence_4_different_current_formats()
        if working_cmd:
            print(f"\n🎉 FOUND WORKING COMMAND: {working_cmd}")
            return working_cmd
        
        working_preset = self.test_sequence_5_preset_commands()
        if working_preset:
            print(f"\n🎉 FOUND WORKING PRESET: {working_preset}")
            return working_preset
        
        print(f"\n❌ NO CURRENT DRAW ACHIEVED")
        print("Possible issues:")
        print("- Device safety interlocks active")
        print("- Different command format needed")
        print("- Hardware issue")
        print("- Missing activation sequence")
        
        return None
    
    def close(self):
        self.send('LOAD OFF')
        self.ser.close()

def main():
    diagnostics = CurrentDiagnostics()
    
    try:
        working_command = diagnostics.test_all_sequences()
        
        if working_command:
            print(f"\n✅ SUCCESS: Use '{working_command}' for current setting")
        else:
            print(f"\n⚠️  No current draw achieved - check hardware/settings")
    
    finally:
        diagnostics.close()

if __name__ == "__main__":
    main()
