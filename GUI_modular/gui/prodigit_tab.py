#!/usr/bin/env python3
"""
Prodigit 34205A device tab
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.device_tab import DeviceTab
from models.device_config import DEVICE_SPECS, DeviceType
from controllers.prodigit_controller import ProdigitController


class ProdigitTab(DeviceTab):
    """Prodigit 34205A control tab"""
    
    def __init__(self, parent):
        super().__init__(parent, DEVICE_SPECS[DeviceType.PRODIGIT_34205A], ProdigitController)
        
    def create_controls(self):
        """Create Prodigit-specific controls"""
        # Mode selection
        ttk.Label(self.control_frame, text="Mode:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.mode_combo = ttk.Combobox(self.control_frame, 
                                     values=["CC (Constant Current)", "CV (Constant Voltage)", 
                                            "CP (Constant Power)", "CR (Constant Resistance)"],
                                     state="readonly")
        self.mode_combo.grid(row=0, column=1, padx=5, pady=2)
        self.mode_combo.set("CC (Constant Current)")
        self.mode_combo.bind('<<ComboboxSelected>>', self._on_mode_change)
        
        # Value setting
        ttk.Label(self.control_frame, text="Value:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.value_entry = ttk.Entry(self.control_frame, width=10)
        self.value_entry.grid(row=1, column=1, padx=5, pady=2)
        self.value_entry.insert(0, "0")
        
        ttk.Label(self.control_frame, text="Unit:").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.unit_label = ttk.Label(self.control_frame, text="A")
        self.unit_label.grid(row=1, column=3, sticky='w', padx=5, pady=2)
        
        # Control buttons
        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Set Parameters", 
                  command=self.set_parameters).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Load ON", 
                  command=self.load_on).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Load OFF", 
                  command=self.load_off).pack(side='left', padx=5)
                  
    def _on_mode_change(self, event=None):
        """Update unit label based on selected mode"""
        mode = self.mode_combo.get()
        if "CC" in mode:
            self.unit_label.config(text="A")
        elif "CV" in mode:
            self.unit_label.config(text="V")
        elif "CP" in mode:
            self.unit_label.config(text="W")
        elif "CR" in mode:
            self.unit_label.config(text="Ω")
                  
    def set_parameters(self):
        """Set load parameters based on selected mode"""
        def _set_params():
            value = float(self.value_entry.get())
            mode = self.mode_combo.get()
            
            if "CC" in mode:
                self.controller.set_mode_cc(value)
            elif "CV" in mode:
                self.controller.set_mode_cv(value)
            elif "CP" in mode:
                self.controller.set_mode_cp(value)
            elif "CR" in mode:
                self.controller.set_mode_cr(value)
                
            return "Parameters set successfully"
            
        result = self.safe_execute(_set_params)
        if result:
            messagebox.showinfo("Success", result)
            
    def load_on(self):
        """Turn load on"""
        def _load_on():
            self.controller.load_on()
            return "Load turned ON"
            
        result = self.safe_execute(_load_on)
        if result:
            messagebox.showinfo("Success", result)
            
    def load_off(self):
        """Turn load off"""
        def _load_off():
            self.controller.load_off()
            return "Load turned OFF"
            
        result = self.safe_execute(_load_off)
        if result:
            messagebox.showinfo("Success", result)