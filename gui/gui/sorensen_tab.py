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
        ttk.Label(self.control_frame, text=f"Voltage (V, max: {self.device_spec.max_voltage:.0f}):").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.voltage_entry = ttk.Entry(self.control_frame, width=10)
        self.voltage_entry.grid(row=0, column=1, padx=5, pady=2)
        self.voltage_entry.insert(0, "0")
        
        # Current setting
        ttk.Label(self.control_frame, text=f"Current (A, max: {self.device_spec.max_current:.1f}):").grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.current_entry = ttk.Entry(self.control_frame, width=10)
        self.current_entry.grid(row=0, column=3, padx=5, pady=2)
        self.current_entry.insert(0, "0")
        
        # OVP setting
        ttk.Label(self.control_frame, text=f"OVP (V, max: {self.device_spec.max_voltage:.0f}):").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.ovp_entry = ttk.Entry(self.control_frame, width=10)
        self.ovp_entry.grid(row=1, column=1, padx=5, pady=2)
        self.ovp_entry.insert(0, "10")
        
        # Current Limit setting (SGX has soft limit, not hardware OCP)
        ttk.Label(self.control_frame, text=f"I-Limit (A, max: {self.device_spec.max_current:.1f}):").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.ocp_entry = ttk.Entry(self.control_frame, width=10)
        self.ocp_entry.grid(row=1, column=3, padx=5, pady=2)
        self.ocp_entry.insert(0, "12")
        
        # Output status indicator
        status_frame = ttk.Frame(self.control_frame)
        status_frame.grid(row=2, column=0, columnspan=4, pady=5)
        ttk.Label(status_frame, text="Output Status:").pack(side='left', padx=5)
        
        # LED-like indicator using canvas
        self.output_status_canvas = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0)
        self.output_status_canvas.pack(side='left', padx=5)
        self.output_status_label = ttk.Label(status_frame, text="OFF", font=('Arial', 9))
        self.output_status_label.pack(side='left', padx=5)
        self._update_output_status_indicator(False)
        
        # Control buttons
        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Set Parameters", 
                  command=self.set_parameters).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output ON", 
                  command=self.output_on).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output OFF", 
                  command=self.output_off).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="❓ Help", 
                  command=self.show_help).pack(side='left', padx=15)
                  
    def set_parameters(self):
        """Set voltage, current, OVP, and OCP parameters"""
        def _set_params():
            voltage = float(self.voltage_entry.get())
            current = float(self.current_entry.get())
            ovp = float(self.ovp_entry.get())
            ocp = float(self.ocp_entry.get())
            
            self.controller.set_voltage(voltage)
            self.controller.set_current(current)
            self.controller.set_ovp(ovp)
            self.controller.set_current_limit(ocp)
            
            return "Parameters set successfully"
            
        result = self.safe_execute(_set_params)
        if result:
            messagebox.showinfo("Success", result)
            
    def _update_output_status_indicator(self, is_on: bool):
        """Update output status LED indicator"""
        self.output_status_canvas.delete("all")
        color = "#00ff00" if is_on else "#808080"  # Green if ON, Gray if OFF
        self.output_status_canvas.create_oval(2, 2, 18, 18, fill=color, outline="black", width=1)
        self.output_status_label.config(text="ON" if is_on else "OFF", 
                                       foreground="green" if is_on else "gray")
    
    def output_on(self):
        """Turn output on with safety checks"""
        def _output_on():
            # Get current parameter values
            voltage = float(self.voltage_entry.get())
            ovp = float(self.ovp_entry.get())
            
            # Safety check: OVP must be greater than set voltage
            if ovp <= voltage:
                raise ValueError(
                    f"OVP ({ovp}V) must be greater than set voltage ({voltage}V). "
                    f"Please adjust OVP to at least {voltage * 1.01:.2f}V for safety."
                )
            
            # Get current value BEFORE OCP check to avoid NameError
            current = float(self.current_entry.get())
            
            # Safety check: Current limit must be >= set current
            ocp = float(self.ocp_entry.get())
            if ocp < current:
                raise ValueError(
                    f"Current limit ({ocp}A) must be >= set current ({current}A). "
                    f"Please adjust current limit to at least {current:.2f}A."
                )
            
            # Validate parameters are within device limits
            if voltage < 0 or voltage > self.device_spec.max_voltage:
                raise ValueError(f"Voltage ({voltage}V) out of range: 0-{self.device_spec.max_voltage}V")
            
            if current < 0 or current > self.device_spec.max_current:
                raise ValueError(f"Current ({current}A) out of range: 0-{self.device_spec.max_current}A")
            
            # Check power limit
            power = voltage * current
            if self.device_spec.max_power and power > self.device_spec.max_power:
                raise ValueError(
                    f"Power limit exceeded: {power:.1f}W > {self.device_spec.max_power}W. "
                    f"Reduce voltage or current."
                )
            
            # Safety confirmation for high values
            HIGH_VOLTAGE_THRESHOLD = self.device_spec.max_voltage * 0.8
            HIGH_CURRENT_THRESHOLD = self.device_spec.max_current * 0.8
            HIGH_POWER_THRESHOLD = self.device_spec.max_power * 0.8 if self.device_spec.max_power else None
            
            needs_confirmation = (
                voltage >= HIGH_VOLTAGE_THRESHOLD or
                current >= HIGH_CURRENT_THRESHOLD or
                (HIGH_POWER_THRESHOLD and power >= HIGH_POWER_THRESHOLD)
            )
            
            if needs_confirmation:
                confirm_msg = f"⚠️ HIGH VALUE WARNING ⚠️\n\n"
                confirm_msg += f"You are about to enable output with:\n"
                confirm_msg += f"  Voltage: {voltage}V (max: {self.device_spec.max_voltage}V)\n"
                confirm_msg += f"  Current: {current}A (max: {self.device_spec.max_current}A)\n"
                confirm_msg += f"  Power: {power:.1f}W"
                if self.device_spec.max_power:
                    confirm_msg += f" (max: {self.device_spec.max_power}W)\n"
                else:
                    confirm_msg += "\n"
                confirm_msg += f"\nThese values are near the device limits.\n"
                confirm_msg += f"Are you sure you want to proceed?"
                
                if not messagebox.askyesno("High Value Confirmation", confirm_msg, icon='warning'):
                    return None  # User cancelled
            
            self.controller.output_on()
            self._update_output_status_indicator(True)
            return "Output turned ON"
            
        result = self.safe_execute(_output_on)
        if result:
            messagebox.showinfo("Success", result)
        else:
            self._update_output_status_indicator(False)
            
    def output_off(self):
        """Turn output off"""
        def _output_off():
            self.controller.output_off()
            self._update_output_status_indicator(False)
            return "Output turned OFF"
            
        result = self.safe_execute(_output_off)
        if result:
            messagebox.showinfo("Success", result)
        else:
            self._update_output_status_indicator(False)
    
    def show_help(self):
        """Show Sorensen help guide"""
        help_window = tk.Toplevel(self.frame)
        help_window.title("Sorensen SGX400-12 D Help Guide")
        help_window.geometry("700x550")
        
        from tkinter import scrolledtext
        
        help_text = """
SORENSEN SGX400-12 D POWER SUPPLY HELP GUIDE

═══════════════════════════════════════════════════════════

🔌 DEVICE OVERVIEW

The Sorensen SGX400-12 D is a precision programmable DC power supply.

Specifications:
  • Maximum Voltage: 400V
  • Maximum Current: 12A
  • Maximum Power: 4800W

═══════════════════════════════════════════════════════════

🎛️ BASIC OPERATIONS

1. Set Parameters:
   • Voltage (V): Output voltage in volts
   • Current (A): Current limit in amperes
   • OVP (V): Over-Voltage Protection limit
   • OCP (A): Over-Current Protection limit
   
   Click "Set Parameters" to apply all settings

2. Output ON:
   • Enables power supply output
   • Safety checks validate parameters first
   • High-value warning for values near device limits
   
   Requirements:
   ✓ OVP must be > set voltage
   ✓ OCP must be ≥ set current
   ✓ Power (V×I) must be ≤ 4800W

3. Output OFF:
   • Safely disables power supply output
   • Parameters remain configured

═══════════════════════════════════════════════════════════

⚡ PROTECTION FEATURES

OVP (Over-Voltage Protection):
  • Protects load from excessive voltage
  • Must be set higher than target voltage
  • Recommended: Set 10-20% above target voltage

OCP (Over-Current Protection):
  • Protects supply from excessive current draw
  • Must be set at or above target current limit
  • Recommended: Set to maximum expected current

Safety Warnings:
  ⚠️  High value warning appears at 80% of device limits
  ⚠️  Power limit check: V × I ≤ 4800W

═══════════════════════════════════════════════════════════

📊 LOGGING & MONITORING

The Sorensen power supply does NOT have automatic test functions.
All measurements must be recorded manually.

To Record Data:
  1. Connect device in Sorensen tab
  2. Set parameters and enable output
  3. Switch to "Monitoring & Logging" tab
  4. Click "Start Monitoring"
  5. Perform your test/measurements
  6. Click "Save Data" to export CSV

The monitoring tab will show:
  • Voltage (V): Actual output voltage
  • Current (A): Actual output current  
  • Power (W): Calculated power (V × I)

═══════════════════════════════════════════════════════════

💡 USAGE EXAMPLES

Battery Charging:
  1. Set voltage to battery max voltage (e.g., 4.2V for Li-ion)
  2. Set current to desired charge rate (e.g., 2A)
  3. Set OVP to 10% above max voltage (e.g., 4.6V)
  4. Set OCP to charge current + margin (e.g., 2.5A)
  5. Enable Output ON
  6. Monitor in "Monitoring & Logging" tab

Component Testing:
  1. Set voltage to component rating
  2. Set current limit for protection
  3. Configure OVP/OCP for safety
  4. Enable output and record data via monitoring

═══════════════════════════════════════════════════════════

⚠️ SAFETY GUIDELINES

• Always verify parameters before Output ON
• Start with low values and increase gradually
• Never exceed device specifications:
  - Voltage: 0-400V
  - Current: 0-12A
  - Power: ≤4800W

• Use appropriate cables and connections for high power
• Monitor temperature during extended high-power operation
• Set OVP/OCP for load protection

═══════════════════════════════════════════════════════════

📝 NOTES

• No automatic CSV logging - use Monitoring & Logging tab
• Real-time measurements available only via monitoring
• All operations are manual - ideal for steady-state testing
• For dynamic profiles, consider using Keithley device instead
        """
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=('Courier', 9))
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        text_widget.insert('1.0', help_text)
        text_widget.config(state='disabled')
        
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)