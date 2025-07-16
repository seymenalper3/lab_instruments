#!/usr/bin/env python3
"""
Reusable connection widget for device interfaces
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from models.device_config import InterfaceType, ConnectionConfig, DeviceSpec
from interfaces.serial_interface import SerialInterface
from interfaces.ethernet_interface import EthernetInterface
from interfaces.visa_interface import VISAInterface


class ConnectionWidget:
    """Reusable connection widget for device interfaces"""
    
    def __init__(self, parent, device_spec: DeviceSpec, 
                 on_connect: Callable, on_disconnect: Callable):
        self.parent = parent
        self.device_spec = device_spec
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.connected = False
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create connection interface widgets"""
        # Main frame
        self.frame = ttk.LabelFrame(self.parent, text="Connection Settings")
        
        # Interface selection
        ttk.Label(self.frame, text="Interface:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        
        interface_values = [iface.value for iface in self.device_spec.supported_interfaces]
        self.interface_combo = ttk.Combobox(self.frame, values=interface_values, state="readonly")
        self.interface_combo.grid(row=0, column=1, padx=5, pady=2)
        self.interface_combo.bind('<<ComboboxSelected>>', self._on_interface_change)
        
        # Connection button
        self.connect_btn = ttk.Button(self.frame, text="Connect", command=self._on_connect_click)
        self.connect_btn.grid(row=0, column=2, padx=5, pady=2)
        
        # Status label
        self.status_label = ttk.Label(self.frame, text="Disconnected", foreground="red")
        self.status_label.grid(row=0, column=3, padx=5, pady=2)
        
        # Dynamic settings frame
        self.settings_frame = ttk.Frame(self.frame)
        self.settings_frame.grid(row=1, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        
        # Set default interface
        if interface_values:
            self.interface_combo.set(interface_values[0])
            self._on_interface_change()
            
    def _on_interface_change(self, event=None):
        """Handle interface type change"""
        self._clear_settings()
        
        interface_type = self.interface_combo.get()
        if interface_type == InterfaceType.RS232.value:
            self._create_serial_settings()
        elif interface_type == InterfaceType.ETHERNET.value:
            self._create_ethernet_settings()
        elif interface_type in [InterfaceType.USB.value, InterfaceType.GPIB.value]:
            self._create_visa_settings(interface_type)
            
    def _clear_settings(self):
        """Clear existing settings widgets"""
        for widget in self.settings_frame.winfo_children():
            widget.destroy()
            
    def _create_serial_settings(self):
        """Create serial port settings"""
        ttk.Label(self.settings_frame, text="Port:").grid(row=0, column=0, sticky='w', padx=5)
        
        ports = SerialInterface.get_available_ports()
        self.port_combo = ttk.Combobox(self.settings_frame, values=ports)
        self.port_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.settings_frame, text="Baud Rate:").grid(row=0, column=2, sticky='w', padx=5)
        
        baud_rates = ["9600", "19200", "38400", "57600", "115200"]
        self.baud_combo = ttk.Combobox(self.settings_frame, values=baud_rates)
        self.baud_combo.grid(row=0, column=3, padx=5)
        
        # Set device-specific defaults
        if self.device_spec.device_type.name == "SORENSEN_SGX":
            self.baud_combo.set("9600")
        elif self.device_spec.device_type.name == "PRODIGIT_34205A":
            self.baud_combo.set("115200")
        else:
            self.baud_combo.set("9600")
            
    def _create_ethernet_settings(self):
        """Create ethernet settings"""
        ttk.Label(self.settings_frame, text="IP Address:").grid(row=0, column=0, sticky='w', padx=5)
        
        self.ip_entry = ttk.Entry(self.settings_frame, width=15)
        self.ip_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.settings_frame, text="Port:").grid(row=0, column=2, sticky='w', padx=5)
        
        self.port_entry = ttk.Entry(self.settings_frame, width=8)
        self.port_entry.grid(row=0, column=3, padx=5)
        
        # Set device-specific defaults
        if self.device_spec.device_type.name == "SORENSEN_SGX":
            self.ip_entry.insert(0, "192.168.0.200")
            self.port_entry.insert(0, "9221")
        elif self.device_spec.device_type.name == "KEITHLEY_2281S":
            self.ip_entry.insert(0, "192.168.1.100")
            self.port_entry.insert(0, "5025")
        elif self.device_spec.device_type.name == "PRODIGIT_34205A":
            self.ip_entry.insert(0, "192.168.1.101")
            self.port_entry.insert(0, "4001")
            
    def _create_visa_settings(self, interface_type):
        """Create VISA settings"""
        ttk.Label(self.settings_frame, text="Resource:").grid(row=0, column=0, sticky='w', padx=5)
        
        self.resource_entry = ttk.Entry(self.settings_frame, width=40)
        self.resource_entry.grid(row=0, column=1, padx=5)
        
        # Set default based on interface and device type
        if interface_type == InterfaceType.USB.value:
            if self.device_spec.device_type.name == "KEITHLEY_2281S":
                default = "USB0::0x05E6::0x2281S::4587429::0::INSTR"
            else:
                default = "USB0::0x0000::0x0000::000000::INSTR"
        else:  # GPIB
            default = "GPIB0::5::INSTR"
            
        self.resource_entry.insert(0, default)
        
        # Detect button
        detect_btn = ttk.Button(self.settings_frame, text="Detect", command=self._detect_visa_resources)
        detect_btn.grid(row=0, column=2, padx=5)
        
    def _detect_visa_resources(self):
        """Detect and show available VISA resources"""
        try:
            resources = VISAInterface.get_available_resources()
            if not resources:
                messagebox.showinfo("Info", "No VISA resources found")
                return
                
            # Create selection dialog
            dialog = tk.Toplevel(self.parent)
            dialog.title("Select VISA Resource")
            dialog.geometry("500x300")
            dialog.transient(self.parent)
            dialog.grab_set()
            
            ttk.Label(dialog, text="Available Resources:").pack(pady=5)
            
            listbox = tk.Listbox(dialog, height=8)
            listbox.pack(fill='both', expand=False, padx=10, pady=5)
            
            for resource in resources:
                listbox.insert(tk.END, resource)
            
            # Button frame - pack at bottom first
            button_frame = ttk.Frame(dialog)
            button_frame.pack(side='bottom', fill='x', padx=10, pady=10)
            
            # Selected resource display - pack at bottom before buttons
            selected_frame = ttk.Frame(dialog)
            selected_frame.pack(side='bottom', fill='x', padx=10, pady=5)
            
            ttk.Label(selected_frame, text="Selected:").pack(side='left')
            selected_var = tk.StringVar(value="None")
            selected_label = ttk.Label(selected_frame, textvariable=selected_var, foreground="blue")
            selected_label.pack(side='left', padx=(5,0))
            
            def on_listbox_select(event):
                selection = listbox.curselection()
                if selection:
                    selected = listbox.get(selection[0])
                    selected_var.set(selected)
                else:
                    selected_var.set("None")
            
            listbox.bind('<<ListboxSelect>>', on_listbox_select)
            
            def confirm_selection():
                selection = listbox.curselection()
                if selection:
                    selected = listbox.get(selection[0])
                    self.resource_entry.delete(0, tk.END)
                    self.resource_entry.insert(0, selected)
                    dialog.destroy()
                    # Focus back to parent window and update resource entry
                    self.parent.focus_set()
                    self.resource_entry.focus_set()
                else:
                    messagebox.showwarning("Warning", "Please select a resource first")
            
            def cancel_selection():
                dialog.destroy()
                    
            confirm_btn = ttk.Button(button_frame, text="Confirm", command=confirm_selection)
            confirm_btn.pack(side='left', padx=10, pady=5)
            
            cancel_btn = ttk.Button(button_frame, text="Cancel", command=cancel_selection)
            cancel_btn.pack(side='left', padx=10, pady=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to detect resources: {e}")
            
    def _on_connect_click(self):
        """Handle connect/disconnect button click"""
        if self.connected:
            self._disconnect()
        else:
            self._connect()
            
    def _connect(self):
        """Attempt to connect to device"""
        try:
            config = self._get_connection_config()
            if config:
                self.on_connect(config)
                self._set_connected_state(True)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            
    def _disconnect(self):
        """Disconnect from device"""
        try:
            self.on_disconnect()
            self._set_connected_state(False)
        except Exception as e:
            messagebox.showerror("Disconnect Error", f"Failed to disconnect: {e}")
            
    def _get_connection_config(self) -> Optional[ConnectionConfig]:
        """Get connection configuration from current settings"""
        interface_type = self.interface_combo.get()
        
        if interface_type == InterfaceType.RS232.value:
            port = self.port_combo.get()
            baudrate = int(self.baud_combo.get())
            if not port:
                raise ValueError("Please select a serial port")
            return ConnectionConfig.create_serial(port, baudrate)
            
        elif interface_type == InterfaceType.ETHERNET.value:
            host = self.ip_entry.get().strip()
            port = int(self.port_entry.get())
            if not host:
                raise ValueError("Please enter IP address")
            return ConnectionConfig.create_ethernet(host, port)
            
        elif interface_type in [InterfaceType.USB.value, InterfaceType.GPIB.value]:
            resource = self.resource_entry.get().strip()
            if not resource:
                raise ValueError("Please enter VISA resource string")
            return ConnectionConfig.create_visa(resource)
            
        return None
        
    def _set_connected_state(self, connected: bool):
        """Update UI to reflect connection state"""
        self.connected = connected
        if connected:
            self.connect_btn.config(text="Disconnect")
            self.status_label.config(text="Connected", foreground="green")
            self.interface_combo.config(state="disabled")
        else:
            self.connect_btn.config(text="Connect")
            self.status_label.config(text="Disconnected", foreground="red")
            self.interface_combo.config(state="readonly")
            
    def pack(self, **kwargs):
        """Pack the widget"""
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the widget"""
        self.frame.grid(**kwargs)