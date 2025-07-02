# test_sgx.py
import socket
import time

def simple_test():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("169.254.134.194", 9221))
    
    # Temel komutlar
    sock.send(b"*IDN?\n")
    print("Cihaz:", sock.recv(1024).decode().strip())
    
    sock.send(b"MEAS:VOLT?\n")
    print("Voltaj:", sock.recv(1024).decode().strip())
    
    sock.close()

simple_test()
