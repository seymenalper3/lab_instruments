#!/usr/bin/env python3
"""
Generic device control tab
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any
from models.device_config import DeviceSpec, ConnectionConfig
from controllers.base_controller import BaseDeviceController
from gui.connection_widget import ConnectionWidget


class DeviceTab:
    """Generic device control tab"""
    
    def __init__(self, parent, device_spec: DeviceSpec, controller_class):
        self.parent = parent
        self.device_spec = device_spec
        self.controller_class = controller_class
        self.controller: Optional[BaseDeviceController] = None
        
        self.create_tab()
        
    def create_tab(self):
        """Create the device tab"""
        # Main frame
        self.frame = ttk.Frame(self.parent)
        
        # Connection widget
        self.connection_widget = ConnectionWidget(
            self.frame, 
            self.device_spec,
            self.on_connect,
            self.on_disconnect
        )
        self.connection_widget.pack(fill='x', padx=5, pady=5)
        
        # Status bar
        self.create_status_bar()
        
        # Control frame
        self.control_frame = ttk.LabelFrame(self.frame, text="Control Settings")
        self.control_frame.pack(fill='x', padx=5, pady=5)
        
        # Create device-specific controls
        self.create_controls()
        
        # Measurements frame
        self.meas_frame = ttk.LabelFrame(self.frame, text="Measurements")
        self.meas_frame.pack(fill='x', padx=5, pady=5)
        
        self.voltage_label = ttk.Label(self.meas_frame, text="Voltage: -- V")
        self.voltage_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.current_label = ttk.Label(self.meas_frame, text="Current: -- A")
        self.current_label.grid(row=0, column=1, padx=10, pady=5)
        
        if self.device_spec.max_power:
            self.power_label = ttk.Label(self.meas_frame, text="Power: -- W")
            self.power_label.grid(row=0, column=2, padx=10, pady=5)
        
    def create_status_bar(self):
        """Create a status bar for displaying connection status and messages."""
        style = ttk.Style(self.frame)
        style.configure("Success.TLabel", foreground="green")
        style.configure("Error.TLabel", foreground="red")
        
        self.status_bar = ttk.Label(self.frame, text="Disconnected", style="Error.TLabel", anchor='w')
        self.status_bar.pack(fill='x', padx=5, pady=(0, 5))

    def create_controls(self):
        """Create device-specific control widgets - to be overridden"""
        pass
        
    def on_connect(self, config: ConnectionConfig):
        """Handle connect button click"""
        try:
            # Create interface based on configuration
            interface = self._create_interface(config)

            # Create controller
            self.controller = self.controller_class(interface)

            # Connect to device
            self.controller.connect()

            self.status_bar.config(text=f"Connected to: {self.controller.model}", style="Success.TLabel")
            self.on_successful_connect()
            return True

        except Exception as e:
            self.controller = None
            self.status_bar.config(text=f"Connection failed: {e}", style="Error.TLabel")
            messagebox.showerror("Connection Error", str(e))
            return False

    def on_disconnect(self):
        """Handle device disconnection"""
        if self.controller:
            self.controller.disconnect()
            self.controller = None
        self.status_bar.config(text="Disconnected", style="Error.TLabel")
        self.on_successful_disconnect()

    def on_successful_connect(self):
        """Hook for child classes to override after a successful connection."""
        pass

    def on_successful_disconnect(self):
        """Hook for child classes to override after a successful disconnection."""
        pass

    def _create_interface(self, config: ConnectionConfig):
        """Create interface instance from configuration"""
        if config.interface_type.value == "RS232":
            from interfaces.serial_interface import SerialInterface
            return SerialInterface(**config.parameters)
        elif config.interface_type.value == "Ethernet":
            from interfaces.ethernet_interface import EthernetInterface
            return EthernetInterface(**config.parameters)
        elif config.interface_type.value in ["USB", "GPIB"]:
            from interfaces.visa_interface import VISAInterface
            return VISAInterface(**config.parameters)
        else:
            raise ValueError(f"Unsupported interface type: {config.interface_type}")
            
    def update_measurements(self, data: Dict[str, Any]):
        """Update measurement displays"""
        if 'voltage' in data and data['voltage'] is not None:
            self.voltage_label.config(text=f"Voltage: {data['voltage']:.3f} V")
        if 'current' in data and data['current'] is not None:
            self.current_label.config(text=f"Current: {data['current']:.3f} A")
        if hasattr(self, 'power_label') and 'power' in data and data['power'] is not None:
            self.power_label.config(text=f"Power: {data['power']:.3f} W")
            
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.controller is not None and self.controller.is_connected()
        
    def get_controller(self) -> Optional[BaseDeviceController]:
        """Get the device controller"""
        return self.controller
        
    def safe_execute(self, func, *args, **kwargs):
        """Safely execute a function with error handling"""
        if not self.is_connected():
            messagebox.showerror("Error", f"{self.device_spec.name} not connected")
            return None
            
        try:
            result = func()
            # Some functions might return a result that we want to show
            if isinstance(result, str):
                self.status_bar.config(text=result, style="Success.TLabel")
            return result
        except Exception as e:
            self.status_bar.config(text=f"Error: {e}", style="Error.TLabel")
            messagebox.showerror("Error", f"Operation failed: {e}")
            return None