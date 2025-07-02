#pulse test eklenmiş GUI

#!/usr/bin/env python3
"""
Multi-Device Test GUI for:
- Sorensen SGX400-12 D Power Supply
- Keithley 2281S Battery Simulator/Emulator  
- Prodigit 34205A Electronic Load

Supports RS232, Ethernet, USB, and GPIB connections
Compatible with Windows, Linux, and macOS
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
import csv
import socket
import serial
import serial.tools.list_ports
import queue
import datetime
import json
import platform
import sys
import os

# Try to import PyVISA, handle gracefully if not available
try:
    import pyvisa
    VISA_AVAILABLE = True
except ImportError:
    VISA_AVAILABLE = False
    print("PyVISA not available. USB and GPIB connections will be limited.")

class DeviceInterface:
    """Base class for device communication interfaces"""
    def __init__(self):
        self.connected = False
        self.connection = None
        
    def connect(self):
        raise NotImplementedError
        
    def disconnect(self):
        raise NotImplementedError
        
    def write(self, command):
        raise NotImplementedError
        
    def query(self, command):
        raise NotImplementedError

class SerialInterface(DeviceInterface):
    """RS232 Serial communication interface"""
    def __init__(self, port, baudrate=9600, timeout=5):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        
    def connect(self):
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=self.timeout,
                rtscts=True  # Hardware handshaking
            )
            self.connected = True
            return True
        except Exception as e:
            raise Exception(f"Serial connection failed: {e}")
            
    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connected = False
            
    def write(self, command):
        if not self.connected:
            raise Exception("Not connected")
        cmd = command.strip() + '\r\n'
        self.connection.write(cmd.encode())
        
    def query(self, command):
        self.write(command)
        time.sleep(0.1)
        response = self.connection.readline().decode().strip()
        return response

class EthernetInterface(DeviceInterface):
    """Ethernet TCP socket communication interface"""
    def __init__(self, host, port, timeout=5):
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout
        
    def connect(self):
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(self.timeout)
            self.connection.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            raise Exception(f"Ethernet connection failed: {e}")
            
    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connected = False
            
    def write(self, command):
        if not self.connected:
            raise Exception("Not connected")
        cmd = command.strip() + '\n'
        self.connection.send(cmd.encode())
        
    def query(self, command):
        self.write(command)
        response = self.connection.recv(1024).decode().strip()
        return response

class VISAInterface(DeviceInterface):
    """VISA communication interface for USB and GPIB"""
    def __init__(self, resource_string, timeout=5000):
        super().__init__()
        self.resource_string = resource_string
        self.timeout = timeout
        if not VISA_AVAILABLE:
            raise Exception("PyVISA not available")
            
    def connect(self):
        try:
            rm = pyvisa.ResourceManager()
            self.connection = rm.open_resource(self.resource_string)
            self.connection.timeout = self.timeout
            self.connected = True
            return True
        except Exception as e:
            raise Exception(f"VISA connection failed: {e}")
            
    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connected = False
            
    def write(self, command):
        if not self.connected:
            raise Exception("Not connected")
        self.connection.write(command)
        
    def query(self, command):
        if not self.connected:
            raise Exception("Not connected")
        return self.connection.query(command).strip()

class DeviceController:
    """Base class for device-specific controllers"""
    def __init__(self, interface):
        self.interface = interface
        self.model = ""
        self.connected = False
        
    def connect(self):
        try:
            self.interface.connect()
            self.connected = True
            self.identify()
            return True
        except Exception as e:
            self.connected = False
            raise e
            
    def disconnect(self):
        try:
            if hasattr(self, 'output_off'):
                self.output_off()
        except:
            pass
        self.interface.disconnect()
        self.connected = False
        
    def identify(self):
        try:
            self.model = self.interface.query("*IDN?")
        except:
            self.model = "Unknown"

class SorensenSGX(DeviceController):
    """Sorensen SGX400-12 D Power Supply Controller"""
    def __init__(self, interface):
        super().__init__(interface)
        self.max_voltage = 400
        self.max_current = 12
        
    def set_voltage(self, voltage):
        """Set output voltage in volts"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write(f"SOUR:VOLT {voltage}")
        
    def set_current(self, current):
        """Set current limit in amperes"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write(f"SOUR:CURR {current}")
        
    def set_ovp(self, ovp_voltage):
        """Set overvoltage protection"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write(f"SOUR:VOLT:PROT {ovp_voltage}")
        
    def output_on(self):
        """Turn output on"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write("OUTP:STAT ON")
        
    def output_off(self):
        """Turn output off"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write("OUTP:STAT OFF")
        
    def measure_voltage(self):
        """Read actual output voltage"""
        if not self.connected:
            raise Exception("Not connected")
        return float(self.interface.query("MEAS:VOLT?"))
        
    def measure_current(self):
        """Read actual output current"""
        if not self.connected:
            raise Exception("Not connected")
        return float(self.interface.query("MEAS:CURR?"))

class Keithley2281S(DeviceController):
    """Keithley 2281S Battery Simulator/Emulator Controller"""
    def __init__(self, interface):
        super().__init__(interface)
        self.max_voltage = 20
        self.max_current = 6
        
    def set_voltage(self, voltage):
        """Set output voltage in volts"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write(f":SOUR:VOLT {voltage}")
        
    def set_current_limit(self, current):
        """Set current limit in amperes"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write(f":SOUR:CURR {current}")
        
    def output_on(self):
        """Turn output on"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write(":OUTP ON")
        
    def output_off(self):
        """Turn output off"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write(":OUTP OFF")
        
    def measure_voltage(self):
        """Read actual output voltage"""
        if not self.connected:
            raise Exception("Not connected")
        return float(self.interface.query(":MEAS:VOLT?"))
        
    def measure_current(self):
        """Read actual output current"""
        if not self.connected:
            raise Exception("Not connected")
        return float(self.interface.query(":MEAS:CURR?"))
        
    def battery_test_mode(self):
        """Switch to battery test function"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write(":FUNC TEST")

class Prodigit34205A(DeviceController):
    """Prodigit 34205A Electronic Load Controller"""
    def __init__(self, interface):
        super().__init__(interface)
        self.max_voltage = 600
        self.max_current = 160
        self.max_power = 5000
        
    def identify(self):
        try:
            self.model = self.interface.query("SYST:NAME?")
        except:
            self.model = "Prodigit 34205A"
            
    def set_mode_cc(self, current):
        """Set constant current mode"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write("STAT:MODE CC")
        self.interface.write(f"CURR:HIGH {current}")
        
    def set_mode_cv(self, voltage):
        """Set constant voltage mode"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write("STAT:MODE CV")
        self.interface.write(f"VOLT:HIGH {voltage}")
        
    def set_mode_cp(self, power):
        """Set constant power mode"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write("STAT:MODE CP")
        self.interface.write(f"CP:HIGH {power}")
        
    def set_mode_cr(self, resistance):
        """Set constant resistance mode"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write("STAT:MODE CR")
        self.interface.write(f"RES:HIGH {resistance}")
        
    def load_on(self):
        """Turn load on"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write("STAT:LOAD ON")
        
    def load_off(self):
        """Turn load off"""
        if not self.connected:
            raise Exception("Not connected")
        self.interface.write("STAT:LOAD OFF")
        
    def measure_voltage(self):
        """Read actual voltage"""
        if not self.connected:
            raise Exception("Not connected")
        return float(self.interface.query("MEAS:VOLT?"))
        
    def measure_current(self):
        """Read actual current"""
        if not self.connected:
            raise Exception("Not connected")
        return float(self.interface.query("MEAS:CURR?"))
        
    def measure_power(self):
        """Read actual power"""
        if not self.connected:
            raise Exception("Not connected")
        return float(self.interface.query("MEAS:POW?"))

class DeviceTestGUI:
    """Main GUI Application"""
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Device Test Controller")
        self.root.geometry("1200x800")
        
        # Device controllers
        self.devices = {
            'sorensen': None,
            'keithley': None,
            'prodigit': None
        }
        
        # Monitoring
        self.monitoring = False
        self.monitoring_thread = None
        self.data_queue = queue.Queue()
        
        # Create GUI
        self.create_gui()
        
        # Start monitoring data updates
        self.root.after(100, self.update_monitoring_display)
        
    def run_keithley_pulse_test(self):
        if not self.devices['keithley'] or not self.devices['keithley'].connected:
            messagebox.showerror("Error", "Keithley not connected")
            return

        try:
            import csv, datetime, time
            device = self.devices['keithley']
            interface = device.interface
            w = interface.write
            q = interface.query

            PULSES, PULSE_T, REST_T = 2, 30, 30
            RAMP_UP, RAMP_DN = [0.05, 0.20], [0.20, 0.05]
            I_PULSE, I_REST = 1.0, 0.0001
            SAMP_INT, STEP, EVOC_DLY = 0.5, 0.5, 0.05

            def last_vi():
                buf = q(':BATT:DATA:DATA? \"VOLT,CURR,REL\"')
                if not buf:
                    return None, None, None
                vals = list(map(float, buf.split(',')[-3:]))
                return vals[0], vals[1], vals[2]

            w('*CLS'); w('SYST:REM')
            w(':FUNC TEST')
            w(':BATT:TEST:MODE DIS')
            w(f':BATT:TEST:SENS:SAMP:INT {SAMP_INT}')
            w(f':BATT:TEST:SENS:EVOC:DELA {EVOC_DLY}')
            w(':FORM:UNITS OFF'); w(':SYST:AZER OFF')
            w(':BATT:DATA:CLE'); w(':BATT:DATA:STAT ON')
            w(':BATT:TEST:EXEC STAR')

            stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            fpulse = open(f'pulse_bt_{stamp}.csv','w',newline=''); wp = csv.writer(fpulse)
            frest  = open(f'rest_evoc_{stamp}.csv','w',newline=''); wr = csv.writer(frest)
            wp.writerow(['t_rel_s','volt_v','curr_a'])
            wr.writerow(['t_rel_s','voc_v','esr_ohm'])
            t0 = time.time()

            for cyc in range(1, PULSES+1):
                for lim in RAMP_UP:
                    w(f':BATT:TEST:CURR:LIM:SOUR {lim}'); w(':BATT:OUTP ON')
                    end = time.time()+2
                    while time.time()<end:
                        v,i,rel = last_vi()
                        if v is not None: wp.writerow([f'{rel:.3f}',f'{v:.6f}',f'{i:.6f}']); fpulse.flush()
                        time.sleep(STEP)

                w(f':BATT:TEST:CURR:LIM:SOUR {I_PULSE}')
                end = time.time()+PULSE_T
                while time.time()<end:
                    v,i,rel = last_vi()
                    if v is not None: wp.writerow([f'{rel:.3f}',f'{v:.6f}',f'{i:.6f}']); fpulse.flush()
                    time.sleep(STEP)

                for lim in RAMP_DN:
                    w(f':BATT:TEST:CURR:LIM:SOUR {lim}')
                    end = time.time()+2
                    while time.time()<end:
                        v,i,rel = last_vi()
                        if v is not None: wp.writerow([f'{rel:.3f}',f'{v:.6f}',f'{i:.6f}']); fpulse.flush()
                        time.sleep(STEP)

                w(':BATT:OUTP OFF'); w(f':BATT:TEST:CURR:LIM:SOUR {I_REST}')
                end = time.time()+REST_T
                while time.time()<end:
                    esr,voc = map(float,q(':BATT:TEST:MEAS:EVOC?').split(','))
                    wr.writerow([f'{time.time()-t0:.3f}',f'{voc:.6f}',f'{esr:.6f}']); frest.flush()
                    time.sleep(STEP)

            w(':BATT:OUTP OFF'); w('SYST:LOC')
            fpulse.close(); frest.close()
            interface.disconnect()

            messagebox.showinfo("Pulse Test", f"✔ Test tamamlandı.\nPulse CSV: {fpulse.name}\nRest CSV: {frest.name}")


        except Exception as e:
            messagebox.showerror("Error", f"Pulse test failed: {e}")

    def create_gui(self):
        """Create the main GUI interface"""
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs for each device
        self.create_sorensen_tab(notebook)
        self.create_keithley_tab(notebook)
        self.create_prodigit_tab(notebook)
        self.create_monitoring_tab(notebook)
        
    def create_sorensen_tab(self, parent):
        """Create Sorensen SGX400-12 control tab"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Sorensen SGX400-12")
        
        # Connection frame
        conn_frame = ttk.LabelFrame(frame, text="Connection Settings")
        conn_frame.pack(fill='x', padx=5, pady=5)
        
        # Interface selection
        ttk.Label(conn_frame, text="Interface:").grid(row=0, column=0, sticky='w')
        self.sorensen_interface = ttk.Combobox(conn_frame, values=["RS232", "Ethernet", "GPIB"])
        self.sorensen_interface.grid(row=0, column=1, padx=5)
        self.sorensen_interface.bind('<<ComboboxSelected>>', self.on_sorensen_interface_change)
        
        # Dynamic connection settings frame
        self.sorensen_conn_settings = ttk.Frame(conn_frame)
        self.sorensen_conn_settings.grid(row=1, column=0, columnspan=4, sticky='ew', pady=5)
        
        # Connection button
        self.sorensen_connect_btn = ttk.Button(conn_frame, text="Connect", 
                                             command=self.connect_sorensen)
        self.sorensen_connect_btn.grid(row=0, column=2, padx=5)
        
        # Status label
        self.sorensen_status = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.sorensen_status.grid(row=0, column=3, padx=5)
        
        # Control frame
        control_frame = ttk.LabelFrame(frame, text="Control Settings")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Voltage setting
        ttk.Label(control_frame, text="Voltage (V):").grid(row=0, column=0, sticky='w')
        self.sorensen_voltage = ttk.Entry(control_frame, width=10)
        self.sorensen_voltage.grid(row=0, column=1, padx=5)
        self.sorensen_voltage.insert(0, "0")
        
        # Current setting
        ttk.Label(control_frame, text="Current (A):").grid(row=0, column=2, sticky='w')
        self.sorensen_current = ttk.Entry(control_frame, width=10)
        self.sorensen_current.grid(row=0, column=3, padx=5)
        self.sorensen_current.insert(0, "0")
        
        # OVP setting
        ttk.Label(control_frame, text="OVP (V):").grid(row=1, column=0, sticky='w')
        self.sorensen_ovp = ttk.Entry(control_frame, width=10)
        self.sorensen_ovp.grid(row=1, column=1, padx=5)
        self.sorensen_ovp.insert(0, "10")
        
        # Control buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Set Parameters", 
                  command=self.set_sorensen_parameters).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output ON", 
                  command=self.sorensen_output_on).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output OFF", 
                  command=self.sorensen_output_off).pack(side='left', padx=5)
        
        # Measurements frame
        meas_frame = ttk.LabelFrame(frame, text="Measurements")
        meas_frame.pack(fill='x', padx=5, pady=5)
        
        self.sorensen_volt_meas = ttk.Label(meas_frame, text="Voltage: -- V")
        self.sorensen_volt_meas.grid(row=0, column=0, padx=10)
        
        self.sorensen_curr_meas = ttk.Label(meas_frame, text="Current: -- A")
        self.sorensen_curr_meas.grid(row=0, column=1, padx=10)
        
    def create_keithley_tab(self, parent):
        """Create Keithley 2281S control tab"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Keithley 2281S")
        
        # Connection frame
        conn_frame = ttk.LabelFrame(frame, text="Connection Settings")
        conn_frame.pack(fill='x', padx=5, pady=5)
        
        # Interface selection
        ttk.Label(conn_frame, text="Interface:").grid(row=0, column=0, sticky='w')
        self.keithley_interface = ttk.Combobox(conn_frame, values=["USB", "Ethernet", "GPIB"])
        self.keithley_interface.grid(row=0, column=1, padx=5)
        self.keithley_interface.bind('<<ComboboxSelected>>', self.on_keithley_interface_change)
        
        # Dynamic connection settings frame
        self.keithley_conn_settings = ttk.Frame(conn_frame)
        self.keithley_conn_settings.grid(row=1, column=0, columnspan=4, sticky='ew', pady=5)
        
        # Connection button
        self.keithley_connect_btn = ttk.Button(conn_frame, text="Connect", 
                                             command=self.connect_keithley)
        self.keithley_connect_btn.grid(row=0, column=2, padx=5)
        
        # Status label
        self.keithley_status = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.keithley_status.grid(row=0, column=3, padx=5)
        
        # Control frame
        control_frame = ttk.LabelFrame(frame, text="Control Settings")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Function selection
        ttk.Label(control_frame, text="Function:").grid(row=0, column=0, sticky='w')
        self.keithley_function = ttk.Combobox(control_frame, 
                                            values=["Power Supply", "Battery Test", "Battery Simulator"])
        self.keithley_function.grid(row=0, column=1, padx=5)
        self.keithley_function.set("Power Supply")
        
        # Voltage setting
        ttk.Label(control_frame, text="Voltage (V):").grid(row=1, column=0, sticky='w')
        self.keithley_voltage = ttk.Entry(control_frame, width=10)
        self.keithley_voltage.grid(row=1, column=1, padx=5)
        self.keithley_voltage.insert(0, "0")
        
        # Current setting
        ttk.Label(control_frame, text="Current (A):").grid(row=1, column=2, sticky='w')
        self.keithley_current = ttk.Entry(control_frame, width=10)
        self.keithley_current.grid(row=1, column=3, padx=5)
        self.keithley_current.insert(0, "0")
        
        # Control buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Set Parameters", 
                  command=self.set_keithley_parameters).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output ON", 
                  command=self.keithley_output_on).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output OFF", 
                  command=self.keithley_output_off).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Run Pulse Test", command=self.run_keithley_pulse_test).pack(side='left', padx=5)
        
        # Measurements frame
        meas_frame = ttk.LabelFrame(frame, text="Measurements")
        meas_frame.pack(fill='x', padx=5, pady=5)
        
        self.keithley_volt_meas = ttk.Label(meas_frame, text="Voltage: -- V")
        self.keithley_volt_meas.grid(row=0, column=0, padx=10)
        
        self.keithley_curr_meas = ttk.Label(meas_frame, text="Current: -- A")
        self.keithley_curr_meas.grid(row=0, column=1, padx=10)
        
    def create_prodigit_tab(self, parent):
        """Create Prodigit 34205A control tab"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Prodigit 34205A")
        
        # Connection frame
        conn_frame = ttk.LabelFrame(frame, text="Connection Settings")
        conn_frame.pack(fill='x', padx=5, pady=5)
        
        # Interface selection
        ttk.Label(conn_frame, text="Interface:").grid(row=0, column=0, sticky='w')
        self.prodigit_interface = ttk.Combobox(conn_frame, values=["RS232", "Ethernet", "USB", "GPIB"])
        self.prodigit_interface.grid(row=0, column=1, padx=5)
        self.prodigit_interface.bind('<<ComboboxSelected>>', self.on_prodigit_interface_change)
        
        # Dynamic connection settings frame
        self.prodigit_conn_settings = ttk.Frame(conn_frame)
        self.prodigit_conn_settings.grid(row=1, column=0, columnspan=4, sticky='ew', pady=5)
        
        # Connection button
        self.prodigit_connect_btn = ttk.Button(conn_frame, text="Connect", 
                                             command=self.connect_prodigit)
        self.prodigit_connect_btn.grid(row=0, column=2, padx=5)
        
        # Status label
        self.prodigit_status = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.prodigit_status.grid(row=0, column=3, padx=5)
        
        # Control frame
        control_frame = ttk.LabelFrame(frame, text="Load Settings")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Mode selection
        ttk.Label(control_frame, text="Mode:").grid(row=0, column=0, sticky='w')
        self.prodigit_mode = ttk.Combobox(control_frame, 
                                        values=["CC (Constant Current)", "CV (Constant Voltage)", 
                                               "CP (Constant Power)", "CR (Constant Resistance)"])
        self.prodigit_mode.grid(row=0, column=1, padx=5)
        self.prodigit_mode.set("CC (Constant Current)")
        
        # Value setting
        ttk.Label(control_frame, text="Value:").grid(row=1, column=0, sticky='w')
        self.prodigit_value = ttk.Entry(control_frame, width=10)
        self.prodigit_value.grid(row=1, column=1, padx=5)
        self.prodigit_value.insert(0, "0")
        
        ttk.Label(control_frame, text="Unit:").grid(row=1, column=2, sticky='w')
        self.prodigit_unit = ttk.Label(control_frame, text="A")
        self.prodigit_unit.grid(row=1, column=3, sticky='w')
        
        # Bind mode change to update unit
        self.prodigit_mode.bind('<<ComboboxSelected>>', self.on_prodigit_mode_change)
        
        # Control buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Set Parameters", 
                  command=self.set_prodigit_parameters).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Load ON", 
                  command=self.prodigit_load_on).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Load OFF", 
                  command=self.prodigit_load_off).pack(side='left', padx=5)
        
        # Measurements frame
        meas_frame = ttk.LabelFrame(frame, text="Measurements")
        meas_frame.pack(fill='x', padx=5, pady=5)
        
        self.prodigit_volt_meas = ttk.Label(meas_frame, text="Voltage: -- V")
        self.prodigit_volt_meas.grid(row=0, column=0, padx=10)
        
        self.prodigit_curr_meas = ttk.Label(meas_frame, text="Current: -- A")
        self.prodigit_curr_meas.grid(row=0, column=1, padx=10)
        
        self.prodigit_pow_meas = ttk.Label(meas_frame, text="Power: -- W")
        self.prodigit_pow_meas.grid(row=0, column=2, padx=10)
        
    def create_monitoring_tab(self, parent):
        """Create monitoring and logging tab"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Monitoring & Logging")
        
        # Control frame
        control_frame = ttk.LabelFrame(frame, text="Monitoring Control")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Monitoring controls
        ttk.Label(control_frame, text="Sample Interval (s):").grid(row=0, column=0, sticky='w')
        self.sample_interval = ttk.Entry(control_frame, width=10)
        self.sample_interval.grid(row=0, column=1, padx=5)
        self.sample_interval.insert(0, "1.0")
        
        self.monitor_btn = ttk.Button(control_frame, text="Start Monitoring", 
                                    command=self.toggle_monitoring)
        self.monitor_btn.grid(row=0, column=2, padx=5)
        
        ttk.Button(control_frame, text="Save Data", 
                  command=self.save_data).grid(row=0, column=3, padx=5)
        
        ttk.Button(control_frame, text="Clear Data", 
                  command=self.clear_data).grid(row=0, column=4, padx=5)
        
        # Data display
        data_frame = ttk.LabelFrame(frame, text="Monitoring Data")
        data_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create scrolled text widget for data display
        self.data_display = scrolledtext.ScrolledText(data_frame, height=20)
        self.data_display.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Data storage
        self.monitoring_data = []
        
    def on_sorensen_interface_change(self, event=None):
        """Handle Sorensen interface selection change"""
        self.create_connection_settings(self.sorensen_conn_settings, 
                                      self.sorensen_interface.get(), 'sorensen')
        
    def on_keithley_interface_change(self, event=None):
        """Handle Keithley interface selection change"""
        self.create_connection_settings(self.keithley_conn_settings, 
                                      self.keithley_interface.get(), 'keithley')
        
    def on_prodigit_interface_change(self, event=None):
        """Handle Prodigit interface selection change"""
        self.create_connection_settings(self.prodigit_conn_settings, 
                                      self.prodigit_interface.get(), 'prodigit')
        
    def on_prodigit_mode_change(self, event=None):
        """Update unit label based on selected mode"""
        mode = self.prodigit_mode.get()
        if "CC" in mode:
            self.prodigit_unit.config(text="A")
        elif "CV" in mode:
            self.prodigit_unit.config(text="V")
        elif "CP" in mode:
            self.prodigit_unit.config(text="W")
        elif "CR" in mode:
            self.prodigit_unit.config(text="Ω")
            
    def create_connection_settings(self, parent, interface, device):
        """Create dynamic connection settings based on interface type"""
        # Clear existing widgets
        for widget in parent.winfo_children():
            widget.destroy()
            
        if interface == "RS232":
            self.create_serial_settings(parent, device)
        elif interface == "Ethernet":
            self.create_ethernet_settings(parent, device)
        elif interface in ["USB", "GPIB"]:
            self.create_visa_settings(parent, device, interface)
            
    def create_serial_settings(self, parent, device):
        """Create RS232 serial connection settings"""
        ttk.Label(parent, text="Port:").grid(row=0, column=0, sticky='w')
        
        # Get available serial ports
        ports = [port.device for port in serial.tools.list_ports.comports()]
        port_combo = ttk.Combobox(parent, values=ports)
        port_combo.grid(row=0, column=1, padx=5)
        setattr(self, f"{device}_port", port_combo)
        
        ttk.Label(parent, text="Baud Rate:").grid(row=0, column=2, sticky='w')
        
        if device == 'sorensen':
            baud_values = ["9600", "19200", "38400", "57600", "115200"]
            default_baud = "9600"
        elif device == 'prodigit':
            baud_values = ["9600", "19200", "38400", "57600", "115200"]
            default_baud = "115200"
        else:
            baud_values = ["9600", "19200", "38400", "57600", "115200"]
            default_baud = "9600"
            
        baud_combo = ttk.Combobox(parent, values=baud_values)
        baud_combo.grid(row=0, column=3, padx=5)
        baud_combo.set(default_baud)
        setattr(self, f"{device}_baudrate", baud_combo)
        
    def create_ethernet_settings(self, parent, device):
        """Create Ethernet connection settings"""
        ttk.Label(parent, text="IP Address:").grid(row=0, column=0, sticky='w')
        
        ip_entry = ttk.Entry(parent, width=15)
        ip_entry.grid(row=0, column=1, padx=5)
        
        if device == 'sorensen':
            ip_entry.insert(0, "192.168.0.200")
            default_port = "9221"
        elif device == 'keithley':
            ip_entry.insert(0, "192.168.1.100")
            default_port = "5025"
        elif device == 'prodigit':
            ip_entry.insert(0, "192.168.1.101")
            default_port = "4001"
            
        setattr(self, f"{device}_ip", ip_entry)
        
        ttk.Label(parent, text="Port:").grid(row=0, column=2, sticky='w')
        
        port_entry = ttk.Entry(parent, width=8)
        port_entry.grid(row=0, column=3, padx=5)
        port_entry.insert(0, default_port)
        setattr(self, f"{device}_tcp_port", port_entry)
        
    def create_visa_settings(self, parent, device, interface):
        """Create VISA connection settings for USB and GPIB"""
        if not VISA_AVAILABLE:
            ttk.Label(parent, text="PyVISA not available", 
                     foreground="red").grid(row=0, column=0, sticky='w')
            return
            
        ttk.Label(parent, text="Resource:").grid(row=0, column=0, sticky='w')
        
        if interface == "USB":
            if device == 'keithley':
                default_resource = "USB0::0x05E6::0x2281S::4587429::0::INSTR"
            else:
                default_resource = "USB0::0x0000::0x0000::000000::INSTR"
        else:  # GPIB
            default_resource = "GPIB0::5::INSTR"
            
        resource_entry = ttk.Entry(parent, width=40)
        resource_entry.grid(row=0, column=1, padx=5)
        resource_entry.insert(0, default_resource)
        setattr(self, f"{device}_resource", resource_entry)
        
        # Add refresh button to detect available resources
        ttk.Button(parent, text="Detect", 
                  command=lambda: self.detect_visa_resources(device)).grid(row=0, column=2, padx=5)
        
    def detect_visa_resources(self, device):
        """Detect available VISA resources"""
        if not VISA_AVAILABLE:
            messagebox.showerror("Error", "PyVISA not available")
            return
            
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            
            if resources:
                # Create a selection dialog
                selection_window = tk.Toplevel(self.root)
                selection_window.title("Select VISA Resource")
                selection_window.geometry("400x200")
                
                ttk.Label(selection_window, text="Available Resources:").pack(pady=5)
                
                listbox = tk.Listbox(selection_window)
                listbox.pack(fill='both', expand=True, padx=10, pady=5)
                
                for resource in resources:
                    listbox.insert(tk.END, resource)
                    
                def select_resource():
                    selection = listbox.curselection()
                    if selection:
                        selected_resource = listbox.get(selection[0])
                        getattr(self, f"{device}_resource").delete(0, tk.END)
                        getattr(self, f"{device}_resource").insert(0, selected_resource)
                        selection_window.destroy()
                        
                ttk.Button(selection_window, text="Select", 
                          command=select_resource).pack(pady=5)
            else:
                messagebox.showinfo("Info", "No VISA resources found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to detect resources: {e}")
            
    # Device connection methods
    def connect_sorensen(self):
        """Connect to Sorensen SGX400-12"""
        try:
            interface_type = self.sorensen_interface.get()
            
            if interface_type == "RS232":
                port = self.sorensen_port.get()
                baudrate = int(self.sorensen_baudrate.get())
                interface = SerialInterface(port, baudrate)
            elif interface_type == "Ethernet":
                ip = self.sorensen_ip.get()
                port = int(self.sorensen_tcp_port.get())
                interface = EthernetInterface(ip, port)
            elif interface_type == "GPIB":
                resource = self.sorensen_resource.get()
                interface = VISAInterface(resource)
            else:
                raise Exception("Invalid interface type")
                
            self.devices['sorensen'] = SorensenSGX(interface)
            self.devices['sorensen'].connect()
            
            self.sorensen_status.config(text="Connected", foreground="green")
            self.sorensen_connect_btn.config(text="Disconnect", 
                                           command=self.disconnect_sorensen)
            
            messagebox.showinfo("Success", f"Connected to Sorensen SGX400-12\n{self.devices['sorensen'].model}")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            
    def disconnect_sorensen(self):
        """Disconnect from Sorensen SGX400-12"""
        if self.devices['sorensen']:
            self.devices['sorensen'].disconnect()
            self.devices['sorensen'] = None
            
        self.sorensen_status.config(text="Disconnected", foreground="red")
        self.sorensen_connect_btn.config(text="Connect", command=self.connect_sorensen)
        
    def connect_keithley(self):
        """Connect to Keithley 2281S"""
        try:
            interface_type = self.keithley_interface.get()
            
            if interface_type == "USB":
                resource = self.keithley_resource.get()
                interface = VISAInterface(resource)
            elif interface_type == "Ethernet":
                ip = self.keithley_ip.get()
                port = int(self.keithley_tcp_port.get())
                interface = EthernetInterface(ip, port)
            elif interface_type == "GPIB":
                resource = self.keithley_resource.get()
                interface = VISAInterface(resource)
            else:
                raise Exception("Invalid interface type")
                
            self.devices['keithley'] = Keithley2281S(interface)
            self.devices['keithley'].connect()
            
            self.keithley_status.config(text="Connected", foreground="green")
            self.keithley_connect_btn.config(text="Disconnect", 
                                           command=self.disconnect_keithley)
            
            messagebox.showinfo("Success", f"Connected to Keithley 2281S\n{self.devices['keithley'].model}")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            
    def disconnect_keithley(self):
        """Disconnect from Keithley 2281S"""
        if self.devices['keithley']:
            self.devices['keithley'].disconnect()
            self.devices['keithley'] = None
            
        self.keithley_status.config(text="Disconnected", foreground="red")
        self.keithley_connect_btn.config(text="Connect", command=self.connect_keithley)
        
    def connect_prodigit(self):
        """Connect to Prodigit 34205A"""
        try:
            interface_type = self.prodigit_interface.get()
            
            if interface_type == "RS232":
                port = self.prodigit_port.get()
                baudrate = int(self.prodigit_baudrate.get())
                interface = SerialInterface(port, baudrate)
            elif interface_type == "Ethernet":
                ip = self.prodigit_ip.get()
                port = int(self.prodigit_tcp_port.get())
                interface = EthernetInterface(ip, port)
            elif interface_type in ["USB", "GPIB"]:
                resource = self.prodigit_resource.get()
                interface = VISAInterface(resource)
            else:
                raise Exception("Invalid interface type")
                
            self.devices['prodigit'] = Prodigit34205A(interface)
            self.devices['prodigit'].connect()
            
            self.prodigit_status.config(text="Connected", foreground="green")
            self.prodigit_connect_btn.config(text="Disconnect", 
                                           command=self.disconnect_prodigit)
            
            messagebox.showinfo("Success", f"Connected to Prodigit 34205A\n{self.devices['prodigit'].model}")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            
    def disconnect_prodigit(self):
        """Disconnect from Prodigit 34205A"""
        if self.devices['prodigit']:
            self.devices['prodigit'].disconnect()
            self.devices['prodigit'] = None
            
        self.prodigit_status.config(text="Disconnected", foreground="red")
        self.prodigit_connect_btn.config(text="Connect", command=self.connect_prodigit)
        
    # Device control methods
    def set_sorensen_parameters(self):
        """Set Sorensen parameters"""
        if not self.devices['sorensen'] or not self.devices['sorensen'].connected:
            messagebox.showerror("Error", "Sorensen not connected")
            return
            
        try:
            voltage = float(self.sorensen_voltage.get())
            current = float(self.sorensen_current.get())
            ovp = float(self.sorensen_ovp.get())
            
            self.devices['sorensen'].set_voltage(voltage)
            self.devices['sorensen'].set_current(current)
            self.devices['sorensen'].set_ovp(ovp)
            
            messagebox.showinfo("Success", "Parameters set successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set parameters: {e}")
            
    def sorensen_output_on(self):
        """Turn Sorensen output on"""
        if not self.devices['sorensen'] or not self.devices['sorensen'].connected:
            messagebox.showerror("Error", "Sorensen not connected")
            return
            
        try:
            self.devices['sorensen'].output_on()
            messagebox.showinfo("Success", "Output turned ON")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to turn output on: {e}")
            
    def sorensen_output_off(self):
        """Turn Sorensen output off"""
        if not self.devices['sorensen'] or not self.devices['sorensen'].connected:
            messagebox.showerror("Error", "Sorensen not connected")
            return
            
        try:
            self.devices['sorensen'].output_off()
            messagebox.showinfo("Success", "Output turned OFF")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to turn output off: {e}")
            
    def set_keithley_parameters(self):
        """Set Keithley parameters"""
        if not self.devices['keithley'] or not self.devices['keithley'].connected:
            messagebox.showerror("Error", "Keithley not connected")
            return
            
        try:
            voltage = float(self.keithley_voltage.get())
            current = float(self.keithley_current.get())
            
            # Switch function if needed
            func = self.keithley_function.get()
            if func == "Battery Test":
                self.devices['keithley'].battery_test_mode()
            
            self.devices['keithley'].set_voltage(voltage)
            self.devices['keithley'].set_current_limit(current)
            
            messagebox.showinfo("Success", "Parameters set successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set parameters: {e}")
            
    def keithley_output_on(self):
        """Turn Keithley output on"""
        if not self.devices['keithley'] or not self.devices['keithley'].connected:
            messagebox.showerror("Error", "Keithley not connected")
            return
            
        try:
            self.devices['keithley'].output_on()
            messagebox.showinfo("Success", "Output turned ON")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to turn output on: {e}")
            
    def keithley_output_off(self):
        """Turn Keithley output off"""
        if not self.devices['keithley'] or not self.devices['keithley'].connected:
            messagebox.showerror("Error", "Keithley not connected")
            return
            
        try:
            self.devices['keithley'].output_off()
            messagebox.showinfo("Success", "Output turned OFF")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to turn output off: {e}")
            
    def set_prodigit_parameters(self):
        """Set Prodigit parameters"""
        if not self.devices['prodigit'] or not self.devices['prodigit'].connected:
            messagebox.showerror("Error", "Prodigit not connected")
            return
            
        try:
            value = float(self.prodigit_value.get())
            mode = self.prodigit_mode.get()
            
            if "CC" in mode:
                self.devices['prodigit'].set_mode_cc(value)
            elif "CV" in mode:
                self.devices['prodigit'].set_mode_cv(value)
            elif "CP" in mode:
                self.devices['prodigit'].set_mode_cp(value)
            elif "CR" in mode:
                self.devices['prodigit'].set_mode_cr(value)
                
            messagebox.showinfo("Success", "Parameters set successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set parameters: {e}")
            
    def prodigit_load_on(self):
        """Turn Prodigit load on"""
        if not self.devices['prodigit'] or not self.devices['prodigit'].connected:
            messagebox.showerror("Error", "Prodigit not connected")
            return
            
        try:
            self.devices['prodigit'].load_on()
            messagebox.showinfo("Success", "Load turned ON")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to turn load on: {e}")
            
    def prodigit_load_off(self):
        """Turn Prodigit load off"""
        if not self.devices['prodigit'] or not self.devices['prodigit'].connected:
            messagebox.showerror("Error", "Prodigit not connected")
            return
            
        try:
            self.devices['prodigit'].load_off()
            messagebox.showinfo("Success", "Load turned OFF")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to turn load off: {e}")
            
    # Monitoring methods
    def toggle_monitoring(self):
        """Start or stop monitoring"""
        if self.monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
            
    def start_monitoring(self):
        """Start monitoring all connected devices"""
        self.monitoring = True
        self.monitor_btn.config(text="Stop Monitoring")
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitoring_worker)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.monitor_btn.config(text="Start Monitoring")
        
    def monitoring_worker(self):
        """Worker thread for monitoring devices"""
        while self.monitoring:
            try:
                interval = float(self.sample_interval.get())
                timestamp = datetime.datetime.now()
                
                data_point = {
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'sorensen_v': None, 'sorensen_i': None,
                    'keithley_v': None, 'keithley_i': None,
                    'prodigit_v': None, 'prodigit_i': None, 'prodigit_p': None
                }
                
                # Read Sorensen measurements
                if self.devices['sorensen'] and self.devices['sorensen'].connected:
                    try:
                        data_point['sorensen_v'] = self.devices['sorensen'].measure_voltage()
                        data_point['sorensen_i'] = self.devices['sorensen'].measure_current()
                    except:
                        pass
                        
                # Read Keithley measurements
                if self.devices['keithley'] and self.devices['keithley'].connected:
                    try:
                        data_point['keithley_v'] = self.devices['keithley'].measure_voltage()
                        data_point['keithley_i'] = self.devices['keithley'].measure_current()
                    except:
                        pass
                        
                # Read Prodigit measurements
                if self.devices['prodigit'] and self.devices['prodigit'].connected:
                    try:
                        data_point['prodigit_v'] = self.devices['prodigit'].measure_voltage()
                        data_point['prodigit_i'] = self.devices['prodigit'].measure_current()
                        data_point['prodigit_p'] = self.devices['prodigit'].measure_power()
                    except:
                        pass
                        
                # Queue data for GUI update
                self.data_queue.put(data_point)
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(1)
                
    def update_monitoring_display(self):
        """Update monitoring display with new data"""
        try:
            while True:
                data_point = self.data_queue.get_nowait()
                
                # Update measurement displays
                if data_point['sorensen_v'] is not None:
                    self.sorensen_volt_meas.config(text=f"Voltage: {data_point['sorensen_v']:.3f} V")
                if data_point['sorensen_i'] is not None:
                    self.sorensen_curr_meas.config(text=f"Current: {data_point['sorensen_i']:.3f} A")
                    
                if data_point['keithley_v'] is not None:
                    self.keithley_volt_meas.config(text=f"Voltage: {data_point['keithley_v']:.3f} V")
                if data_point['keithley_i'] is not None:
                    self.keithley_curr_meas.config(text=f"Current: {data_point['keithley_i']:.3f} A")
                    
                if data_point['prodigit_v'] is not None:
                    self.prodigit_volt_meas.config(text=f"Voltage: {data_point['prodigit_v']:.3f} V")
                if data_point['prodigit_i'] is not None:
                    self.prodigit_curr_meas.config(text=f"Current: {data_point['prodigit_i']:.3f} A")
                if data_point['prodigit_p'] is not None:
                    self.prodigit_pow_meas.config(text=f"Power: {data_point['prodigit_p']:.3f} W")
                    
                # Add to monitoring data
                self.monitoring_data.append(data_point)
                
                # Update data display
                data_line = f"{data_point['timestamp']}: "
                if data_point['sorensen_v'] is not None:
                    data_line += f"SGX: {data_point['sorensen_v']:.3f}V {data_point['sorensen_i']:.3f}A | "
                if data_point['keithley_v'] is not None:
                    data_line += f"2281S: {data_point['keithley_v']:.3f}V {data_point['keithley_i']:.3f}A | "
                if data_point['prodigit_v'] is not None:
                    data_line += f"34205A: {data_point['prodigit_v']:.3f}V {data_point['prodigit_i']:.3f}A {data_point['prodigit_p']:.3f}W"
                    
                self.data_display.insert(tk.END, data_line + '\n')
                self.data_display.see(tk.END)
                
        except queue.Empty:
            pass
            
        # Schedule next update
        self.root.after(100, self.update_monitoring_display)
        
    def save_data(self):
        """Save monitoring data to CSV file"""
        if not self.monitoring_data:
            messagebox.showwarning("Warning", "No data to save")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save monitoring data"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as csvfile:
                    fieldnames = ['timestamp', 'sorensen_v', 'sorensen_i', 
                                'keithley_v', 'keithley_i', 
                                'prodigit_v', 'prodigit_i', 'prodigit_p']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for data_point in self.monitoring_data:
                        writer.writerow(data_point)
                        
                messagebox.showinfo("Success", f"Data saved to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data: {e}")
                
    def clear_data(self):
        """Clear monitoring data"""
        self.monitoring_data.clear()
        self.data_display.delete(1.0, tk.END)
        messagebox.showinfo("Success", "Data cleared")
        
    def on_closing(self):
        """Handle application closing"""
        # Stop monitoring
        self.monitoring = False
        
        # Disconnect all devices
        for device_name, device in self.devices.items():
            if device and device.connected:
                try:
                    device.disconnect()
                except:
                    pass
                    
        self.root.destroy()

def main():
    """Main application entry point"""
    # Check Python version
    if sys.version_info < (3, 6):
        print("This application requires Python 3.6 or later")
        sys.exit(1)
        
    # Create and run the application
    root = tk.Tk()
    app = DeviceTestGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    print(f"Multi-Device Test GUI started on {platform.system()}")
    if VISA_AVAILABLE:
        print("PyVISA available - USB and GPIB support enabled")
    else:
        print("PyVISA not available - USB and GPIB support limited")
        
    root.mainloop()

if __name__ == "__main__":
    main()
