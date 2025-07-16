#!/usr/bin/env python3
"""
Sorensen SGX400-12 D device tab
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.device_tab import DeviceTab
from models.device_config import DEVICE_SPECS, DeviceType
from controllers.sorensen_controller import SorensenController


class SorensenTab(DeviceTab):
    """Sorensen SGX400-12 D control tab"""
    
    def __init__(self, parent):
        super().__init__(parent, DEVICE_SPECS[DeviceType.SORENSEN_SGX], SorensenController)
        
    def create_controls(self):
        """Create Sorensen-specific controls"""
        # Voltage setting
        ttk.Label(self.control_frame, text="Voltage (V):").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.voltage_entry = ttk.Entry(self.control_frame, width=10)
        self.voltage_entry.grid(row=0, column=1, padx=5, pady=2)
        self.voltage_entry.insert(0, "0")
        
        # Current setting
        ttk.Label(self.control_frame, text="Current (A):").grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.current_entry = ttk.Entry(self.control_frame, width=10)
        self.current_entry.grid(row=0, column=3, padx=5, pady=2)
        self.current_entry.insert(0, "0")
        
        # OVP setting
        ttk.Label(self.control_frame, text="OVP (V):").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.ovp_entry = ttk.Entry(self.control_frame, width=10)
        self.ovp_entry.grid(row=1, column=1, padx=5, pady=2)
        self.ovp_entry.insert(0, "10")
        
        # Control buttons
        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Set Parameters", 
                  command=self.set_parameters).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output ON", 
                  command=self.output_on).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output OFF", 
                  command=self.output_off).pack(side='left', padx=5)
                  
    def set_parameters(self):
        """Set voltage, current, and OVP parameters"""
        def _set_params():
            voltage = float(self.voltage_entry.get())
            current = float(self.current_entry.get())
            ovp = float(self.ovp_entry.get())
            
            self.controller.set_voltage(voltage)
            self.controller.set_current(current)
            self.controller.set_ovp(ovp)
            
            return "Parameters set successfully"
            
        result = self.safe_execute(_set_params)
        if result:
            messagebox.showinfo("Success", result)
            
    def output_on(self):
        """Turn output on"""
        def _output_on():
            self.controller.output_on()
            return "Output turned ON"
            
        result = self.safe_execute(_output_on)
        if result:
            messagebox.showinfo("Success", result)
            
    def output_off(self):
        """Turn output off"""
        def _output_off():
            self.controller.output_off()
            return "Output turned OFF"
            
        result = self.safe_execute(_output_off)
        if result:
            messagebox.showinfo("Success", result)