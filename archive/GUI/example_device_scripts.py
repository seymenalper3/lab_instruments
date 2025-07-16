#!/usr/bin/env python3
"""
Example scripts for communicating with each device individually.
These can be used to test connections before using the GUI.
"""

import serial
import socket
import time
import sys

# Try to import PyVISA
try:
    import pyvisa
    VISA_AVAILABLE = True
except ImportError:
    VISA_AVAILABLE = False
    print("Warning: PyVISA not available. USB/GPIB examples will not work.")

def test_sorensen_ethernet():
    """Test Sorensen SGX400-12 via Ethernet"""
    print("Testing Sorensen SGX400-12 via Ethernet...")
    
    try:
        # Connect to power supply
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("192.168.0.200", 9221))  # Default IP and port
        
        # Send identification query
        sock.send(b"*IDN?\n")
        response = sock.recv(1024).decode().strip()
        print(f"Device ID: {response}")
        
        # Set voltage and current
        sock.send(b"SOUR:VOLT 5.0\n")
        sock.send(b"SOUR:CURR 1.0\n")
        sock.send(b"SOUR:VOLT:PROT 6.0\n")  # OVP setting
        
        # Turn output on
        sock.send(b"OUTP:STAT ON\n")
        time.sleep(1)
        
        # Read measurements
        sock.send(b"MEAS:VOLT?\n")
        voltage = float(sock.recv(1024).decode().strip())
        
        sock.send(b"MEAS:CURR?\n")
        current = float(sock.recv(1024).decode().strip())
        
        print(f"Output: {voltage:.3f}V, {current:.3f}A")
        
        # Turn output off
        sock.send(b"OUTP:STAT OFF\n")
        
        sock.close()
        print("Sorensen test completed successfully!")
        
    except Exception as e:
        print(f"Sorensen test failed: {e}")

def test_sorensen_serial():
    """Test Sorensen SGX400-12 via RS232"""
    print("Testing Sorensen SGX400-12 via RS232...")
    
    try:
        # Adjust COM port as needed
        ser = serial.Serial(
            port='COM1',  # Change to your port (e.g., '/dev/ttyUSB0' on Linux)
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=5,
            rtscts=True
        )
        
        # Send identification query
        ser.write(b"*IDN?\r\n")
        time.sleep(0.1)
        response = ser.readline().decode().strip()
        print(f"Device ID: {response}")
        
        # Set parameters
        ser.write(b"SOUR:VOLT 3.3\r\n")
        ser.write(b"SOUR:CURR 0.5\r\n")
        
        # Read back settings
        ser.write(b"SOUR:VOLT?\r\n")
        time.sleep(0.1)
        voltage_set = ser.readline().decode().strip()
        print(f"Voltage setting: {voltage_set}V")
        
        ser.close()
        print("Sorensen RS232 test completed successfully!")
        
    except Exception as e:
        print(f"Sorensen RS232 test failed: {e}")

def test_keithley_usb():
    """Test Keithley 2281S via USB"""
    if not VISA_AVAILABLE:
        print("PyVISA not available, skipping Keithley USB test")
        return
        
    print("Testing Keithley 2281S via USB...")
    
    try:
        rm = pyvisa.ResourceManager()
        
        # Adjust resource string as needed
        # Format: USB0::0x05E6::0x2281S::[serial_number]::INSTR
        inst = rm.open_resource('USB0::0x05E6::0x2281S::4587429::0::INSTR')
        inst.timeout = 5000
        
        # Identify device
        response = inst.query("*IDN?")
        print(f"Device ID: {response.strip()}")
        
        # Set to power supply mode
        inst.write(":FUNC SOUR")
        
        # Configure output
        inst.write(":SOUR:VOLT 5.0")
        inst.write(":SOUR:CURR 1.0")
        
        # Turn output on
        inst.write(":OUTP ON")
        time.sleep(1)
        
        # Read measurements
        voltage = float(inst.query(":MEAS:VOLT?"))
        current = float(inst.query(":MEAS:CURR?"))
        
        print(f"Output: {voltage:.3f}V, {current:.3f}A")
        
        # Turn output off
        inst.write(":OUTP OFF")
        
        inst.close()
        print("Keithley USB test completed successfully!")
        
    except Exception as e:
        print(f"Keithley USB test failed: {e}")

def test_keithley_ethernet():
    """Test Keithley 2281S via Ethernet"""
    print("Testing Keithley 2281S via Ethernet...")
    
    try:
        # Connect to instrument
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("192.168.1.100", 5025))  # Adjust IP as needed
        
        # Send identification query
        sock.send(b"*IDN?\n")
        response = sock.recv(1024).decode().strip()
        print(f"Device ID: {response}")
        
        # Battery test example
        sock.send(b":FUNC TEST\n")  # Switch to battery test function
        sock.send(b":BATT:TEST:MODE DIS\n")  # Discharge mode
        sock.send(b":BATT:TEST:VOLT 3.0\n")  # End voltage
        sock.send(b":BATT:TEST:CURR:END 0.1\n")  # End current
        
        # Check status
        sock.send(b":STAT:OPER:INST:ISUM:COND?\n")
        status = sock.recv(1024).decode().strip()
        print(f"Status: {status}")
        
        sock.close()
        print("Keithley Ethernet test completed successfully!")
        
    except Exception as e:
        print(f"Keithley Ethernet test failed: {e}")

def test_prodigit_serial():
    """Test Prodigit 34205A via RS232"""
    print("Testing Prodigit 34205A via RS232...")
    
    try:
        # Adjust COM port as needed
        ser = serial.Serial(
            port='COM2',  # Change to your port
            baudrate=115200,  # Prodigit typically uses 115200
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=5,
            rtscts=True
        )
        
        # Send identification query
        ser.write(b"SYST:NAME?\r\n")
        time.sleep(0.1)
        response = ser.readline().decode().strip()
        print(f"Device ID: {response}")
        
        # Set constant current mode
        ser.write(b"STAT:MODE CC\r\n")
        ser.write(b"CURR:HIGH 1.0\r\n")  # 1A constant current
        
        # Turn load on
        ser.write(b"STAT:LOAD ON\r\n")
        time.sleep(1)
        
        # Read measurements
        ser.write(b"MEAS:VOLT?\r\n")
        time.sleep(0.1)
        voltage = ser.readline().decode().strip()
        
        ser.write(b"MEAS:CURR?\r\n")
        time.sleep(0.1)
        current = ser.readline().decode().strip()
        
        ser.write(b"MEAS:POW?\r\n")
        time.sleep(0.1)
        power = ser.readline().decode().strip()
        
        print(f"Load: {voltage}V, {current}A, {power}W")
        
        # Turn load off
        ser.write(b"STAT:LOAD OFF\r\n")
        
        ser.close()
        print("Prodigit RS232 test completed successfully!")
        
    except Exception as e:
        print(f"Prodigit RS232 test failed: {e}")

def test_prodigit_ethernet():
    """Test Prodigit 34205A via Ethernet"""
    print("Testing Prodigit 34205A via Ethernet...")
    
    try:
        # Connect to load
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("192.168.1.101", 4001))  # Default port 4001
        
        # Send identification query
        sock.send(b"SYST:NAME?\n")
        response = sock.recv(1024).decode().strip()
        print(f"Device ID: {response}")
        
        # Set constant voltage mode
        sock.send(b"STAT:MODE CV\n")
        sock.send(b"VOLT:HIGH 12.0\n")  # 12V constant voltage
        
        # Set current limit
        sock.send(b"LIMit:CURR:HIGH 2.0\n")  # 2A current limit
        
        # Turn load on
        sock.send(b"STAT:LOAD ON\n")
        time.sleep(1)
        
        # Read measurements
        sock.send(b"MEAS:VOLT?\n")
        voltage = float(sock.recv(1024).decode().strip())
        
        sock.send(b"MEAS:CURR?\n")
        current = float(sock.recv(1024).decode().strip())
        
        sock.send(b"MEAS:POW?\n")
        power = float(sock.recv(1024).decode().strip())
        
        print(f"Load: {voltage:.3f}V, {current:.3f}A, {power:.3f}W")
        
        # Turn load off
        sock.send(b"STAT:LOAD OFF\n")
        
        sock.close()
        print("Prodigit Ethernet test completed successfully!")
        
    except Exception as e:
        print(f"Prodigit Ethernet test failed: {e}")

def test_all_devices():
    """Test all devices with all available interfaces"""
    print("=" * 60)
    print("MULTI-DEVICE COMMUNICATION TEST")
    print("=" * 60)
    
    # Test Sorensen
    print("\n1. SORENSEN SGX400-12 TESTS")
    print("-" * 30)
    test_sorensen_ethernet()
    print()
    test_sorensen_serial()
    
    # Test Keithley
    print("\n2. KEITHLEY 2281S TESTS")
    print("-" * 30)
    test_keithley_usb()
    print()
    test_keithley_ethernet()
    
    # Test Prodigit
    print("\n3. PRODIGIT 34205A TESTS")
    print("-" * 30)
    test_prodigit_serial()
    print()
    test_prodigit_ethernet()
    
    print("\n" + "=" * 60)
    print("ALL DEVICE TESTS COMPLETED")
    print("=" * 60)

def simple_power_supply_load_test():
    """Example of coordinated power supply and electronic load test"""
    print("COORDINATED POWER SUPPLY + LOAD TEST")
    print("-" * 40)
    
    # This example shows how to coordinate a power supply with an electronic load
    # Adjust IP addresses and settings as needed for your setup
    
    sorensen_sock = None
    prodigit_sock = None
    
    try:
        # Connect to Sorensen power supply
        print("Connecting to Sorensen power supply...")
        sorensen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sorensen_sock.settimeout(5)
        sorensen_sock.connect(("192.168.0.200", 9221))
        
        # Connect to Prodigit load
        print("Connecting to Prodigit load...")
        prodigit_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        prodigit_sock.settimeout(5)
        prodigit_sock.connect(("192.168.1.101", 4001))
        
        # Configure power supply
        print("Configuring power supply: 12V, 2A limit")
        sorensen_sock.send(b"SOUR:VOLT 12.0\n")
        sorensen_sock.send(b"SOUR:CURR 2.0\n")
        sorensen_sock.send(b"OUTP:STAT ON\n")
        time.sleep(2)  # Let output stabilize
        
        # Test different load conditions
        load_currents = [0.5, 1.0, 1.5, 2.0]  # Test currents in amperes
        
        print("\nTesting different load conditions:")
        print("Load(A)  Supply(V)  Supply(I)  Load(V)  Load(I)  Load(P)")
        print("-" * 60)
        
        for load_current in load_currents:
            # Set load current
            prodigit_sock.send(b"STAT:MODE CC\n")
            prodigit_sock.send(f"CURR:HIGH {load_current}\n".encode())
            prodigit_sock.send(b"STAT:LOAD ON\n")
            time.sleep(2)  # Let load settle
            
            # Read power supply measurements
            sorensen_sock.send(b"MEAS:VOLT?\n")
            ps_voltage = float(sorensen_sock.recv(1024).decode().strip())
            
            sorensen_sock.send(b"MEAS:CURR?\n")
            ps_current = float(sorensen_sock.recv(1024).decode().strip())
            
            # Read load measurements
            prodigit_sock.send(b"MEAS:VOLT?\n")
            load_voltage = float(prodigit_sock.recv(1024).decode().strip())
            
            prodigit_sock.send(b"MEAS:CURR?\n")
            load_current_meas = float(prodigit_sock.recv(1024).decode().strip())
            
            prodigit_sock.send(b"MEAS:POW?\n")
            load_power = float(prodigit_sock.recv(1024).decode().strip())
            
            print(f"{load_current:6.1f}  {ps_voltage:8.3f}  {ps_current:8.3f}  "
                  f"{load_voltage:7.3f}  {load_current_meas:7.3f}  {load_power:7.3f}")
            
            # Turn load off between measurements
            prodigit_sock.send(b"STAT:LOAD OFF\n")
            time.sleep(1)
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Coordinated test failed: {e}")
        
    finally:
        # Clean up connections
        if sorensen_sock:
            try:
                sorensen_sock.send(b"OUTP:STAT OFF\n")
                sorensen_sock.close()
            except:
                pass
                
        if prodigit_sock:
            try:
                prodigit_sock.send(b"STAT:LOAD OFF\n")
                prodigit_sock.close()
            except:
                pass

def main():
    """Main function to run tests"""
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        if test_name == 'sorensen_eth':
            test_sorensen_ethernet()
        elif test_name == 'sorensen_ser':
            test_sorensen_serial()
        elif test_name == 'keithley_usb':
            test_keithley_usb()
        elif test_name == 'keithley_eth':
            test_keithley_ethernet()
        elif test_name == 'prodigit_ser':
            test_prodigit_serial()
        elif test_name == 'prodigit_eth':
            test_prodigit_ethernet()
        elif test_name == 'coordinated':
            simple_power_supply_load_test()
        elif test_name == 'all':
            test_all_devices()
        else:
            print("Unknown test name")
            print("Available tests:")
            print("  sorensen_eth, sorensen_ser")
            print("  keithley_usb, keithley_eth")
            print("  prodigit_ser, prodigit_eth")
            print("  coordinated, all")
    else:
        print("Device Communication Test Examples")
        print("=" * 40)
        print("Usage: python example_scripts.py <test_name>")
        print()
        print("Available tests:")
        print("  sorensen_eth  - Test Sorensen via Ethernet")
        print("  sorensen_ser  - Test Sorensen via RS232")
        print("  keithley_usb  - Test Keithley via USB")
        print("  keithley_eth  - Test Keithley via Ethernet")
        print("  prodigit_ser  - Test Prodigit via RS232")
        print("  prodigit_eth  - Test Prodigit via Ethernet")
        print("  coordinated   - Power supply + load test")
        print("  all          - Run all individual tests")
        print()
        print("Examples:")
        print("  python example_scripts.py sorensen_eth")
        print("  python example_scripts.py all")
        print("  python example_scripts.py coordinated")

if __name__ == "__main__":
    main()
