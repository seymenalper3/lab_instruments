#!/usr/bin/env python3
"""
Reusable connection widget for device interfaces
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import json
import os
from pathlib import Path
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
        
        # Settings file path
        self.settings_file = Path.home() / ".lab_instruments" / "connection_settings.json"
        self.settings_file.parent.mkdir(exist_ok=True)
        
        # Load saved settings
        self.saved_settings = self._load_settings()
        
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
        
        # Add info button for Keithley devices
        if self.device_spec.device_type.name == "KEITHLEY_2281S":
            info_btn = ttk.Button(self.settings_frame, text="?", width=3, 
                                command=self._show_keithley_ip_info)
            info_btn.grid(row=0, column=4, padx=5)
        
        # Set device-specific defaults or load saved settings
        device_key = f"{self.device_spec.device_type.name}_ethernet"
        if device_key in self.saved_settings:
            # Use saved settings
            saved = self.saved_settings[device_key]
            self.ip_entry.insert(0, saved.get("ip", ""))
            self.port_entry.insert(0, str(saved.get("port", "")))
        else:
            # Use default values
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
        
        # Set default based on interface and device type or load saved settings
        device_key = f"{self.device_spec.device_type.name}_{interface_type.lower()}"
        if device_key in self.saved_settings:
            # Use saved settings
            saved_resource = self.saved_settings[device_key].get("resource", "")
            self.resource_entry.insert(0, saved_resource)
        else:
            # Use default values
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
    
    def _show_keithley_ip_info(self):
        """Show information dialog for Keithley IP address setup"""
        info_dialog = tk.Toplevel(self.parent)
        info_dialog.title("Keithley IP Address Setup")
        info_dialog.geometry("450x300")
        info_dialog.resizable(False, False)
        info_dialog.transient(self.parent)
        info_dialog.grab_set()
        
        # Center the dialog
        info_dialog.update_idletasks()
        x = (info_dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (info_dialog.winfo_screenheight() // 2) - (300 // 2)
        info_dialog.geometry(f"450x300+{x}+{y}")
        
        # Title
        title_label = ttk.Label(info_dialog, text="Keithley Ethernet Connection Setup", 
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(10, 15))
        
        # Main frame
        main_frame = ttk.Frame(info_dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Instructions text
        instructions = """To connect to Keithley via Ethernet, you need to get the IP address from the device:

1. On the Keithley device front panel, press MENU button

2. Navigate to: Settings → Communication → LAN

3. Note down the IP Address shown on the screen

4. Enter that IP address in the connection settings above

5. Default port is usually 5025 (SCPI standard)

Important Notes:
• Make sure your computer and Keithley are on the same network
• The device must have Ethernet cable connected
• Some models may show the IP in a different menu location
• If using DHCP, the IP address may change after reboot"""
        
        text_widget = tk.Text(main_frame, wrap=tk.WORD, height=12, width=50)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert("1.0", instructions)
        text_widget.config(state='disabled')  # Make it read-only
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # OK button
        ok_btn = ttk.Button(info_dialog, text="Got it!", command=info_dialog.destroy)
        ok_btn.pack(pady=10)
        
        # Focus on OK button
        ok_btn.focus_set()
            
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
                # Save settings before connecting
                self._save_current_settings()
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
    
    def _load_settings(self) -> dict:
        """Load saved connection settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load settings: {e}")
        return {}
    
    def _save_settings(self, settings: dict):
        """Save connection settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save settings: {e}")
    
    def _save_current_settings(self):
        """Save current connection settings"""
        interface_type = self.interface_combo.get()
        device_name = self.device_spec.device_type.name
        
        # Load existing settings
        settings = self._load_settings()
        
        if interface_type == InterfaceType.ETHERNET.value:
            device_key = f"{device_name}_ethernet"
            settings[device_key] = {
                "ip": self.ip_entry.get().strip(),
                "port": int(self.port_entry.get()) if self.port_entry.get().strip() else 5025
            }
        elif interface_type in [InterfaceType.USB.value, InterfaceType.GPIB.value]:
            device_key = f"{device_name}_{interface_type.lower()}"
            settings[device_key] = {
                "resource": self.resource_entry.get().strip()
            }
        # Note: Serial settings are not saved as ports may change between sessions
        
        # Save updated settings
        self._save_settings(settings)
        
        # Update our local copy
        self.saved_settings = settings
            
    def pack(self, **kwargs):
        """Pack the widget"""
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the widget"""
        self.frame.grid(**kwargs)