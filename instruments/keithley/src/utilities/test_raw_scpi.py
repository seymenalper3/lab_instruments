#!/usr/bin/env python3
"""
Test raw SCPI communication with Keithley 2281S over TCP/IP
This bypasses PyVISA to test direct socket communication
"""

import socket
import time

def test_raw_scpi():
    """Test raw SCPI communication over TCP/IP"""
    host = '169.254.31.79'
    port = 5025
    
    print(f"Testing raw SCPI communication to {host}:{port}")
    
    try:
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        # Connect to instrument
        sock.connect((host, port))
        print("✅ Socket connection established")
        
        # Send identification query
        command = '*IDN?\n'
        sock.send(command.encode())
        print(f"Sent: {command.strip()}")
        
        # Receive response
        response = sock.recv(1024).decode().strip()
        print(f"Received: {response}")
        
        # Test additional commands
        test_commands = [
            '*OPC?',
            ':FUNC?',
            ':OUTP?',
            ':SYST:ERR?'
        ]
        
        for cmd in test_commands:
            try:
                sock.send(f'{cmd}\n'.encode())
                response = sock.recv(1024).decode().strip()
                print(f"{cmd} -> {response}")
                time.sleep(0.1)
            except Exception as e:
                print(f"{cmd} -> ERROR: {e}")
        
        sock.close()
        print("✅ Raw SCPI communication successful!")
        return True
        
    except Exception as e:
        print(f"❌ Raw SCPI communication failed: {e}")
        return False

def test_visa_with_correct_format():
    """Test different VISA resource string formats"""
    import pyvisa
    
    # Try different resource string formats
    resource_formats = [
        'TCPIP::169.254.31.79::5025::SOCKET',
        'TCPIP0::169.254.31.79::5025::SOCKET',
        'TCPIP::169.254.31.79::inst0::INSTR',
        'TCPIP0::169.254.31.79::inst0::INSTR',
        'TCPIP::169.254.31.79::INSTR',
        'TCPIP0::169.254.31.79::INSTR',
    ]
    
    for resource_str in resource_formats:
        print(f"\nTesting VISA resource: {resource_str}")
        
        try:
            rm = pyvisa.ResourceManager('@py')
            inst = rm.open_resource(resource_str)
            inst.timeout = 10000
            
            # Test basic communication
            idn = inst.query('*IDN?').strip()
            print(f"✅ SUCCESS: {idn}")
            
            inst.close()
            rm.close()
            
            return resource_str
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
    
    return None

if __name__ == "__main__":
    print("=== RAW SCPI COMMUNICATION TEST ===")
    raw_success = test_raw_scpi()
    
    if raw_success:
        print("\n=== VISA RESOURCE STRING TEST ===")
        working_resource = test_visa_with_correct_format()
        
        if working_resource:
            print(f"\n✅ WORKING VISA RESOURCE: {working_resource}")
            print("\nUpdate your script with:")
            print(f"RESOURCE_ADDR = '{working_resource}'")
        else:
            print("\n❌ No working VISA resource found, but raw SCPI works")
            print("Consider using socket communication instead of PyVISA")
    else:
        print("\n❌ Raw SCPI communication failed - check instrument connection") 