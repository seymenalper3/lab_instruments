#!/usr/bin/env python3
"""
Keithley 2281S device tab with enhanced functionality
Enhanced with reference script patterns from auto_mode_profile.py
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from gui.device_tab import DeviceTab
from models.device_config import DEVICE_SPECS, DeviceType
from controllers.keithley_controller import KeithleyController
import threading
from pathlib import Path
import pandas as pd


class KeithleyTab(DeviceTab):
    """Keithley 2281S control tab"""
    
    def __init__(self, parent):
        super().__init__(parent, DEVICE_SPECS[DeviceType.KEITHLEY_2281S], KeithleyController)
        
    def create_controls(self):
        """Create Keithley-specific controls"""
        # Function selection with mode switching
        ttk.Label(self.control_frame, text="Function/Mode:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.function_combo = ttk.Combobox(self.control_frame, 
                                         values=["Power Supply", "Battery Test", "Battery Simulator"],
                                         state="readonly")
        self.function_combo.grid(row=0, column=1, padx=5, pady=2)
        self.function_combo.set("Power Supply")
        
        # Status label to show current mode
        self.mode_status_label = ttk.Label(self.control_frame, text="Mode: Not Set", foreground="gray")
        self.mode_status_label.grid(row=0, column=2, columnspan=2, sticky='w', padx=10, pady=2)
        
        # Voltage setting
        ttk.Label(self.control_frame, text=f"Voltage (V, max: {self.device_spec.max_voltage:.1f}):").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.voltage_entry = ttk.Entry(self.control_frame, width=10)
        self.voltage_entry.grid(row=1, column=1, padx=5, pady=2)
        self.voltage_entry.insert(0, "0")
        
        # Current setting
        ttk.Label(self.control_frame, text=f"Current (A, max: {self.device_spec.max_current:.1f}):").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.current_entry = ttk.Entry(self.control_frame, width=10)
        self.current_entry.grid(row=1, column=3, padx=5, pady=2)
        self.current_entry.insert(0, "0")
        
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
        
        ttk.Button(btn_frame, text="Set Parameters & Mode", 
                  command=self.set_parameters).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output ON", 
                  command=self.output_on).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output OFF", 
                  command=self.output_off).pack(side='left', padx=5)
        
        # Test buttons and Help
        test_frame = ttk.Frame(self.control_frame)
        test_frame.grid(row=4, column=0, columnspan=4, pady=5)
        
        ttk.Button(test_frame, text="Run Pulse Test", 
                  command=self.run_pulse_test).pack(side='left', padx=5)
        ttk.Button(test_frame, text="Generate Battery Model", 
                  command=self.run_battery_model).pack(side='left', padx=5)
        ttk.Button(test_frame, text="Run Current Profile", 
                  command=self.run_current_profile).pack(side='left', padx=5)
        ttk.Button(test_frame, text="❓ Help", 
                  command=self.show_help).pack(side='left', padx=15)
        
        # Output format selection
        format_frame = ttk.Frame(self.control_frame)
        format_frame.grid(row=5, column=0, columnspan=4, pady=2, sticky='w', padx=5)
        
        ttk.Label(format_frame, text="Output Format:").pack(side='left', padx=5)
        self.output_format_var = tk.StringVar(value="csv")
        ttk.Radiobutton(format_frame, text="CSV (Fast)", 
                       variable=self.output_format_var, value="csv").pack(side='left', padx=2)
        ttk.Radiobutton(format_frame, text="Excel", 
                       variable=self.output_format_var, value="xlsx").pack(side='left', padx=2)
        ttk.Radiobutton(format_frame, text="Both", 
                       variable=self.output_format_var, value="both").pack(side='left', padx=2)
                  
        # Current Profile parameters frame
        profile_frame = ttk.LabelFrame(self.control_frame, text="Current Profile Parameters")
        profile_frame.grid(row=6, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        
        ttk.Label(profile_frame, text="Profile File:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.profile_file_var = tk.StringVar()
        self.profile_file_entry = ttk.Entry(profile_frame, textvariable=self.profile_file_var, width=40)
        self.profile_file_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=2, sticky='ew')
        ttk.Button(profile_frame, text="Browse", 
                  command=self.browse_profile_file).grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(profile_frame, text="Discharge Current (A):").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.profile_discharge_current_entry = ttk.Entry(profile_frame, width=10)
        self.profile_discharge_current_entry.grid(row=1, column=1, padx=5, pady=2)
        self.profile_discharge_current_entry.insert(0, "1.0")
        
        ttk.Label(profile_frame, text="Charge Voltage (V):").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.profile_charge_voltage_entry = ttk.Entry(profile_frame, width=10)
        self.profile_charge_voltage_entry.grid(row=1, column=3, padx=5, pady=2)
        self.profile_charge_voltage_entry.insert(0, "4.2")
        
        ttk.Label(profile_frame, text="Sample Period (s):").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.profile_sample_period_entry = ttk.Entry(profile_frame, width=10)
        self.profile_sample_period_entry.grid(row=2, column=1, padx=5, pady=2)
        self.profile_sample_period_entry.insert(0, "1.0")
        
        # Pulse test parameters frame
        pulse_frame = ttk.LabelFrame(self.control_frame, text="Pulse Test Parameters")
        pulse_frame.grid(row=7, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        
        ttk.Label(pulse_frame, text="Pulses:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.pulses_entry = ttk.Entry(pulse_frame, width=8)
        self.pulses_entry.grid(row=0, column=1, padx=5, pady=2)
        self.pulses_entry.insert(0, "2")
        
        ttk.Label(pulse_frame, text="Pulse Time (s):").grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.pulse_time_entry = ttk.Entry(pulse_frame, width=8)
        self.pulse_time_entry.grid(row=0, column=3, padx=5, pady=2)
        self.pulse_time_entry.insert(0, "30")
        
        ttk.Label(pulse_frame, text="Rest Time (s):").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.rest_time_entry = ttk.Entry(pulse_frame, width=8)
        self.rest_time_entry.grid(row=1, column=1, padx=5, pady=2)
        self.rest_time_entry.insert(0, "30")
        
        ttk.Label(pulse_frame, text="Pulse Current (A):").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.pulse_current_entry = ttk.Entry(pulse_frame, width=8)
        self.pulse_current_entry.grid(row=1, column=3, padx=5, pady=2)
        self.pulse_current_entry.insert(0, "1.0")
        
        # Battery model parameters frame
        model_frame = ttk.LabelFrame(self.control_frame, text="Battery Model Parameters")
        model_frame.grid(row=8, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        
        # Discharge parameters
        ttk.Label(model_frame, text="Discharge End Voltage (V):").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.discharge_voltage_entry = ttk.Entry(model_frame, width=8)
        self.discharge_voltage_entry.grid(row=0, column=1, padx=5, pady=2)
        self.discharge_voltage_entry.insert(0, "3.0")
        
        ttk.Label(model_frame, text="Discharge End Current (A):").grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.discharge_current_entry = ttk.Entry(model_frame, width=8)
        self.discharge_current_entry.grid(row=0, column=3, padx=5, pady=2)
        self.discharge_current_entry.insert(0, "0.4")
        
        # Charge parameters
        ttk.Label(model_frame, text="Charge Full Voltage (V):").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.charge_voltage_entry = ttk.Entry(model_frame, width=8)
        self.charge_voltage_entry.grid(row=1, column=1, padx=5, pady=2)
        self.charge_voltage_entry.insert(0, "4.20")
        
        ttk.Label(model_frame, text="Charge Current Limit (A):").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.charge_current_entry = ttk.Entry(model_frame, width=8)
        self.charge_current_entry.grid(row=1, column=3, padx=5, pady=2)
        self.charge_current_entry.insert(0, "1.0")
        
        # Model parameters
        ttk.Label(model_frame, text="ESR Interval (s):").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.esr_interval_entry = ttk.Entry(model_frame, width=8)
        self.esr_interval_entry.grid(row=2, column=1, padx=5, pady=2)
        self.esr_interval_entry.insert(0, "30")
        
        ttk.Label(model_frame, text="Model Slot (1-9):").grid(row=2, column=2, sticky='w', padx=5, pady=2)
        self.model_slot_entry = ttk.Entry(model_frame, width=8)
        self.model_slot_entry.grid(row=2, column=3, padx=5, pady=2)
        self.model_slot_entry.insert(0, "4")
        
        # Model voltage range
        ttk.Label(model_frame, text="Model V-min (V):").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.model_vmin_entry = ttk.Entry(model_frame, width=8)
        self.model_vmin_entry.grid(row=3, column=1, padx=5, pady=2)
        self.model_vmin_entry.insert(0, "2.5")
        
        ttk.Label(model_frame, text="Model V-max (V):").grid(row=3, column=2, sticky='w', padx=5, pady=2)
        self.model_vmax_entry = ttk.Entry(model_frame, width=8)
        self.model_vmax_entry.grid(row=3, column=3, padx=5, pady=2)
        self.model_vmax_entry.insert(0, "4.2")
        
        # Export CSV checkbox
        self.export_csv_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(model_frame, text="Export model to CSV", 
                       variable=self.export_csv_var).grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=5)
                  
    def set_parameters(self):
        """Set voltage and current parameters with automatic mode switching"""
        def _set_params():
            voltage = float(self.voltage_entry.get())
            current = float(self.current_entry.get())
            
            # Get selected function and switch mode accordingly
            func = self.function_combo.get()
            mode_switched = False
            
            if func == "Power Supply":
                success = self.controller.switch_to_power_supply_mode()
                if success:
                    self.mode_status_label.config(text="Mode: Power Supply", foreground="green")
                    mode_switched = True
                else:
                    raise Exception("Failed to switch to Power Supply mode")
                    
            elif func == "Battery Test":
                success = self.controller.switch_to_battery_test_mode()
                if success:
                    self.mode_status_label.config(text="Mode: Battery Test", foreground="blue")
                    mode_switched = True
                    print("Battery Test mode: Using BATT:TEST commands for current/voltage control")
                else:
                    raise Exception("Failed to switch to Battery Test mode")
                    
            elif func == "Battery Simulator":
                # For Battery Simulator mode, we can use Power Supply mode as base
                success = self.controller.switch_to_power_supply_mode()
                if success:
                    self.mode_status_label.config(text="Mode: Battery Simulator", foreground="orange")
                    mode_switched = True
                else:
                    raise Exception("Failed to switch to Battery Simulator mode")
            
            # Set voltage and current parameters
            self.controller.set_voltage(voltage)
            self.controller.set_current_limit(current)
            
            # Set voltage protection for Power Supply mode (safety requirement)
            if func == "Power Supply" or func == "Battery Simulator":
                # Set protection voltage to 10% above set voltage (minimum safety margin)
                protection_voltage = voltage * 1.1
                # Ensure protection doesn't exceed device max voltage
                protection_voltage = min(protection_voltage, self.device_spec.max_voltage)
                try:
                    self.controller.send_command(f':SOUR:VOLT:PROT {protection_voltage}')
                    print(f"Voltage protection set to {protection_voltage:.2f}V")
                except Exception as e:
                    print(f"Warning: Could not set voltage protection: {e}")
            
            if mode_switched:
                return f"Mode switched to {func} and parameters set successfully"
            else:
                return "Parameters set successfully"
            
        result = self.safe_execute(_set_params)
        if result:
            messagebox.showinfo("Success", result)
            
    def output_on(self):
        """Turn output on with safety checks"""
        def _output_on():
            # Validate parameters before enabling output
            voltage = float(self.voltage_entry.get())
            current = float(self.current_entry.get())
            
            # Validate voltage range
            if voltage < 0 or voltage > self.device_spec.max_voltage:
                raise ValueError(f"Voltage ({voltage}V) out of range: 0-{self.device_spec.max_voltage}V")
            
            # Validate current range
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
    
    def _update_output_status_indicator(self, is_on: bool):
        """Update output status LED indicator"""
        self.output_status_canvas.delete("all")
        color = "#00ff00" if is_on else "#808080"  # Green if ON, Gray if OFF
        self.output_status_canvas.create_oval(2, 2, 18, 18, fill=color, outline="black", width=1)
        self.output_status_label.config(text="ON" if is_on else "OFF", 
                                       foreground="green" if is_on else "gray")
            
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
    
    def browse_profile_file(self):
        """Browse for current profile file (CSV or Excel)"""
        # Show format info first
        info = ("📄 Current Profile Format\n\n"
                "Supported formats: CSV (.csv) or Excel (.xlsx)\n\n"
                "Required columns:\n"
                "  • time_s: Time in seconds (start time of segment)\n"
                "  • current_a: Current in Amperes\n"
                "    - Positive values = Charging (Power Supply mode)\n"
                "    - Negative values = Discharging (Battery Test mode)\n\n"
                "Example:\n"
                "  time_s | current_a\n"
                "  0      | 1.5        (charge at 1.5A)\n"
                "  60     | -1.0       (discharge at 1.0A)\n"
                "  120    | 0.5        (charge at 0.5A)\n\n"
                "Note: CSV loads faster (~4x) than Excel\n"
                "For large profiles (>10K rows), prefer CSV\n\n"
                "Output Files:\n"
                "  logs/keithley_log_YYYYMMDD_HHMMSS.csv/.xlsx")
        messagebox.showinfo("Profile Format Info", info)
        
        file_path = filedialog.askopenfilename(
            title="Select Current Profile File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ],
            initialdir="."
        )
        if file_path:
            self.profile_file_var.set(file_path)
    
    def show_help(self):
        """Show Keithley help guide"""
        help_window = tk.Toplevel(self.frame)
        help_window.title("Keithley 2281S Help Guide")
        help_window.geometry("750x600")
        
        from tkinter import scrolledtext
        
        help_text = """
KEITHLEY 2281S BATTERY SIMULATOR HELP GUIDE

═══════════════════════════════════════════════════════════

🔌 BASIC CONTROLS

Set Parameters & Mode:
- Select mode: Power Supply, Battery Test, or Battery Simulator
- Set voltage and current limits
- Device automatically switches mode before applying settings

Output ON/OFF:
- Turn device output on or off
- Safety checks validate parameters before enabling
- Use "Monitoring & Logging" tab to record manual measurements

═══════════════════════════════════════════════════════════

🧪 TEST FUNCTIONS

All test functions create automatic CSV logs in logs/ folder.
During tests, device shows [BUSY] in Monitoring tab - this is normal!

───────────────────────────────────────────────────────────

1️⃣  RUN PULSE TEST

Performs battery pulse discharge/rest cycles for impedance testing.

Parameters:
  • Pulses: Number of pulse cycles
  • Pulse Time: Discharge duration (seconds)
  • Rest Time: Rest/recovery duration (seconds)
  • Pulse Current: Discharge current (Amperes)

Output Files:
  • logs/pulse_bt_YYYYMMDD_HHMMSS.csv (pulse data)
  • logs/rest_evoc_YYYYMMDD_HHMMSS.csv (rest data)

Note: Uses Battery Test mode automatically

───────────────────────────────────────────────────────────

2️⃣  GENERATE BATTERY MODEL

Creates battery model from full discharge/charge cycle.

Parameters:
  • Discharge End Voltage: Stop discharge at this voltage
  • Discharge End Current: Stop discharge at this current
  • Charge Full Voltage: Target charge voltage
  • Charge Current Limit: Maximum charge current
  • ESR Interval: ESR measurement interval (seconds)
  • Model Slot: Device memory slot (1-9)

Output Files:
  • logs/battery_model_data_YYYYMMDD_HHMMSS.csv (test data)
  • battery_model_slot_X.csv (model file, if enabled)

⚠️  WARNING: This test takes hours! Full discharge + charge cycle.

───────────────────────────────────────────────────────────

3️⃣  RUN CURRENT PROFILE

Executes custom current profile with automatic mode switching.

CSV Format:
  time_s,current_a
  0,1.5          # Charge at 1.5A (Power Supply mode)
  60,-1.0        # Discharge at 1.0A (Battery Test mode)
  120,0.5        # Charge at 0.5A (Power Supply mode)

Parameters:
  • Profile File: CSV with time_s and current_a columns
  • Discharge Current: Constant current for negative segments
  • Charge Voltage: Voltage limit for positive segments
  • Sample Period: Measurement interval (default: 1s)

Output File:
  • logs/keithley_log_YYYYMMDD_HHMMSS.csv

Features:
  ✓ Automatic mode switching (positive→charge, negative→discharge)
  ✓ Continuous measurements during execution
  ✓ USB connection required (not Ethernet)

═══════════════════════════════════════════════════════════

📊 LOGGING BEHAVIOR

Test Functions:
  ✓ Create automatic CSV logs
  ✗ Monitoring tab shows [BUSY] (can't measure during test)
  ✓ Check logs/ folder after test completes

Manual Operations (Set Parameters, Output ON/OFF):
  ✗ No automatic logging
  ✓ Use "Monitoring & Logging" tab to record data
  ✓ Click "Start Monitoring" → "Save Data"

═══════════════════════════════════════════════════════════

💡 TIPS

• Always check logs/ folder after tests complete
• Use USB connection for profile tests (Ethernet not supported)
• Battery Test mode discharges at ~1A (device limitation)
• During tests, monitoring shows NULL - this is normal behavior
        """
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=('Courier', 9))
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        text_widget.insert('1.0', help_text)
        text_widget.config(state='disabled')
        
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)
            
    def run_pulse_test(self):
        """Run battery pulse test"""
        if not self.is_connected():
            messagebox.showerror("Error", "Keithley not connected")
            return
            
        try:
            # Get test parameters
            pulses = int(self.pulses_entry.get())
            pulse_time = float(self.pulse_time_entry.get())
            rest_time = float(self.rest_time_entry.get())
            pulse_current = float(self.pulse_current_entry.get())
            
            # Confirm test execution
            msg = f"Run pulse test with:\n"
            msg += f"Pulses: {pulses}\n"
            msg += f"Pulse Time: {pulse_time}s\n"
            msg += f"Rest Time: {rest_time}s\n"
            msg += f"Discharge Current: ~1A (Battery Test mode)\n\n"
            msg += f"⚠️ Note: Keithley 2281S discharges at ~1A regardless of current setting\n"
            msg += f"Total time per pulse: {pulse_time + rest_time}s\n"
            msg += f"This will take approximately {pulses * (pulse_time + rest_time):.0f} seconds total"
            
            if not messagebox.askyesno("Confirm Pulse Test", msg):
                return
                
            # Disable the pulse test button
            for widget in self.control_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for btn in widget.winfo_children():
                        if isinstance(btn, ttk.Button) and btn.cget('text') == 'Run Pulse Test':
                            btn.config(state='disabled')
            
            # Run the test in a separate thread
            import threading
            test_thread = threading.Thread(
                target=self._run_pulse_test_thread,
                args=(pulses, pulse_time, rest_time, pulse_current)
            )
            test_thread.daemon = True
            test_thread.start()
                
        except Exception as e:
            # Re-enable the pulse test button on error
            for widget in self.control_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for btn in widget.winfo_children():
                        if isinstance(btn, ttk.Button) and btn.cget('text') == 'Run Pulse Test':
                            btn.config(state='normal')
                            
            messagebox.showerror("Error", f"Pulse test failed: {e}")
            
    def run_battery_model(self):
        """Run battery model generation test"""
        if not self.is_connected():
            messagebox.showerror("Error", "Keithley not connected")
            return
            
        try:
            # Get test parameters
            discharge_voltage = float(self.discharge_voltage_entry.get())
            discharge_current = float(self.discharge_current_entry.get())
            charge_voltage = float(self.charge_voltage_entry.get())
            charge_current = float(self.charge_current_entry.get())
            esr_interval = int(self.esr_interval_entry.get())
            model_slot = int(self.model_slot_entry.get())
            v_min = float(self.model_vmin_entry.get())
            v_max = float(self.model_vmax_entry.get())
            export_csv = self.export_csv_var.get()
            
            # Estimate test duration
            discharge_time_est = (charge_voltage - discharge_voltage) * 2.0 * 3600 / discharge_current  # rough estimate
            charge_time_est = (charge_voltage - discharge_voltage) * 2.5 * 3600 / charge_current
            total_time_est = (discharge_time_est + charge_time_est) / 3600  # convert to hours
            
            # Confirm test execution
            msg = f"Generate battery model with:\n\n"
            msg += f"Discharge: {discharge_voltage}V @ {discharge_current}A\n"
            msg += f"Charge: {charge_voltage}V @ {charge_current}A\n"
            msg += f"ESR Interval: {esr_interval}s\n"
            msg += f"Model Slot: {model_slot}\n"
            msg += f"Model Range: {v_min}V - {v_max}V\n"
            msg += f"Export CSV: {'Yes' if export_csv else 'No'}\n\n"
            msg += f"⚠️ WARNING: This test will take approximately {total_time_est:.1f} hours!\n"
            msg += "The battery will be fully discharged and charged.\n\n"
            msg += "Continue?"
            
            if not messagebox.askyesno("Confirm Battery Model Test", msg, icon='warning'):
                return
                
            # Disable the battery model button
            for widget in self.control_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for btn in widget.winfo_children():
                        if isinstance(btn, ttk.Button) and btn.cget('text') == 'Generate Battery Model':
                            btn.config(state='disabled')
            
            # Run the test in a separate thread
            import threading
            test_thread = threading.Thread(
                target=self._run_battery_model_thread,
                args=(discharge_voltage, discharge_current, charge_voltage, charge_current,
                      esr_interval, model_slot, v_min, v_max, export_csv)
            )
            test_thread.daemon = True
            test_thread.start()
                
        except Exception as e:
            # Re-enable the battery model button on error
            for widget in self.control_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for btn in widget.winfo_children():
                        if isinstance(btn, ttk.Button) and btn.cget('text') == 'Generate Battery Model':
                            btn.config(state='normal')
                            
            messagebox.showerror("Error", f"Battery model test failed: {e}")
    
    def _run_pulse_test_thread(self, pulses, pulse_time, rest_time, pulse_current):
        """Run pulse test in background thread with automatic Battery Test mode switching"""
        try:
            # Automatically switch to Battery Test mode before running pulse test
            print("Switching to Battery Test mode for pulse test...")
            mode_success = self.controller.switch_to_battery_test_mode()
            if not mode_success:
                raise Exception("Failed to switch to Battery Test mode - pulse test requires Battery Test mode")
            
            # Update mode status on main thread
            self.frame.after(0, lambda: self.mode_status_label.config(
                text="Mode: Battery Test (Auto)", foreground="blue"))
            
            print("Battery Test mode activated - running pulse test...")
            
            # Run the test
            pulse_file, rest_file = self.controller.run_pulse_test(
                pulses=pulses,
                pulse_time=pulse_time,
                rest_time=rest_time,
                i_pulse=pulse_current
            )
            
            # Schedule GUI update on main thread
            self.frame.after(0, lambda pf=pulse_file, rf=rest_file: self._pulse_test_completed(pf, rf))
                                  
        except Exception as e:
            # Schedule error handling on main thread
            error_msg = str(e)
            self.frame.after(0, lambda msg=error_msg: self._pulse_test_failed(msg))
    
    def _pulse_test_completed(self, pulse_file, rest_file):
        """Handle pulse test completion on main thread"""
        # Re-enable the pulse test button
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for btn in widget.winfo_children():
                    if isinstance(btn, ttk.Button) and btn.cget('text') == 'Run Pulse Test':
                        btn.config(state='normal')
        
        messagebox.showinfo("Pulse Test Complete", 
                          f"✓ Test completed successfully!\n\n"
                          f"Pulse data: {pulse_file}\n"
                          f"Rest data: {rest_file}")
    
    def _pulse_test_failed(self, error_msg):
        """Handle pulse test failure on main thread"""
        # Re-enable the pulse test button
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for btn in widget.winfo_children():
                    if isinstance(btn, ttk.Button) and btn.cget('text') == 'Run Pulse Test':
                        btn.config(state='normal')
                        
        messagebox.showerror("Error", f"Pulse test failed: {error_msg}")
        
    def _run_battery_model_thread(self, discharge_voltage, discharge_current, 
                                 charge_voltage, charge_current, esr_interval, 
                                 model_slot, v_min, v_max, export_csv):
        """Run battery model test in background thread with automatic Battery Test mode switching"""
        try:
            # Automatically switch to Battery Test mode before running battery model test
            print("Switching to Battery Test mode for battery model generation...")
            mode_success = self.controller.switch_to_battery_test_mode()
            if not mode_success:
                raise Exception("Failed to switch to Battery Test mode - battery model test requires Battery Test mode")
            
            # Update mode status on main thread
            self.frame.after(0, lambda: self.mode_status_label.config(
                text="Mode: Battery Test (Auto)", foreground="blue"))
            
            print("Battery Test mode activated - running battery model test...")
            
            # Run the test
            results = self.controller.run_battery_model_test(
                discharge_voltage=discharge_voltage,
                discharge_current_end=discharge_current,
                charge_vfull=charge_voltage,
                charge_ilimit=charge_current,
                esr_interval=esr_interval,
                model_slot=model_slot,
                v_min=v_min,
                v_max=v_max,
                export_csv=export_csv
            )
            
            # Schedule GUI update on main thread
            self.frame.after(0, lambda r=results: self._battery_model_completed(r))
                                  
        except Exception as e:
            # Schedule error handling on main thread
            error_msg = str(e)
            self.frame.after(0, lambda msg=error_msg: self._battery_model_failed(msg))
    
    def _battery_model_completed(self, results):
        """Handle battery model test completion on main thread"""
        # Re-enable the battery model button
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for btn in widget.winfo_children():
                    if isinstance(btn, ttk.Button) and btn.cget('text') == 'Generate Battery Model':
                        btn.config(state='normal')
        
        msg = f"✓ Battery model test completed successfully!\n\n"
        msg += f"Test ID: {results['test_id']}\n"
        msg += f"Model saved to slot: {results['model_slot']}\n"
        
        if results.get('model_file'):
            msg += f"\nModel file: {results['model_file']}\n"
        if results.get('data_file'):
            msg += f"Measurement data: {results['data_file']}\n"
            
        messagebox.showinfo("Battery Model Complete", msg)
    
    def _battery_model_failed(self, error_msg):
        """Handle battery model test failure on main thread"""
        # Re-enable the battery model button
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for btn in widget.winfo_children():
                    if isinstance(btn, ttk.Button) and btn.cget('text') == 'Generate Battery Model':
                        btn.config(state='normal')
                        
        messagebox.showerror("Error", f"Battery model test failed: {error_msg}")
    
    def run_current_profile(self):
        """Run current profile with automatic mode switching"""
        if not self.is_connected():
            messagebox.showerror("Error", "Keithley not connected")
            return
            
        # Check if profile file is selected
        profile_path = self.profile_file_var.get().strip()
        if not profile_path:
            messagebox.showerror("Error", "Please select a current profile CSV file")
            return
            
        if not Path(profile_path).exists():
            messagebox.showerror("Error", f"Profile file not found: {profile_path}")
            return
            
        try:
            # Get profile parameters
            discharge_current = float(self.profile_discharge_current_entry.get())
            charge_voltage = float(self.profile_charge_voltage_entry.get())
            sample_period = float(self.profile_sample_period_entry.get())
            output_format = self.output_format_var.get()  # Get selected format
            
            # Estimate duration by loading profile
            try:
                df = pd.read_csv(profile_path)
                if 'time_s' in df.columns and len(df) > 0:
                    total_time = df['time_s'].max()
                else:
                    total_time = len(df) * 10  # Rough estimate
            except Exception as e:
                print(f"Warning: Could not estimate duration: {e}")
                total_time = 300  # Default estimate
            
            # Confirm profile execution
            msg = f"Run current profile with:\n\n"
            msg += f"Profile: {Path(profile_path).name}\n"
            msg += f"Discharge Current: {discharge_current}A\n"
            msg += f"Charge Voltage: {charge_voltage}V\n"
            msg += f"Sample Period: {sample_period}s (measurements every {sample_period}s)\n"
            msg += f"Output Format: {output_format.upper()}\n\n"
            msg += f"Estimated duration: {total_time/60:.0f} minutes\n\n"
            msg += "⚠️ This will automatically switch between Power Supply and Battery Test modes\n"
            msg += "Continue?"
            
            if not messagebox.askyesno("Confirm Current Profile", msg, icon='question'):
                return
                
            # Disable the profile button
            for widget in self.control_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for btn in widget.winfo_children():
                        if isinstance(btn, ttk.Button) and btn.cget('text') == 'Run Current Profile':
                            btn.config(state='disabled')
            
            # Run the profile in a separate thread
            profile_thread = threading.Thread(
                target=self._run_current_profile_thread,
                args=(profile_path, discharge_current, charge_voltage, sample_period, output_format)
            )
            profile_thread.daemon = True
            profile_thread.start()
                
        except Exception as e:
            # Re-enable the profile button on error
            for widget in self.control_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for btn in widget.winfo_children():
                        if isinstance(btn, ttk.Button) and btn.cget('text') == 'Run Current Profile':
                            btn.config(state='normal')
                            
            messagebox.showerror("Error", f"Current profile failed: {e}")
    
    def _run_current_profile_thread(self, profile_path, discharge_current, charge_voltage, sample_period=1.0, output_format='csv'):
        """Run current profile in background thread"""
        try:
            # Run the profile
            log_file = self.controller.run_current_profile(
                profile_path=profile_path,
                discharge_current=discharge_current,
                charge_voltage=charge_voltage,
                sample_period=sample_period,
                output_format=output_format
            )
            
            # Schedule GUI update on main thread
            self.frame.after(0, lambda lf=log_file: self._current_profile_completed(lf))
                                  
        except Exception as e:
            # Schedule error handling on main thread
            error_msg = str(e)
            self.frame.after(0, lambda msg=error_msg: self._current_profile_failed(msg))
    
    def _current_profile_completed(self, log_file):
        """Handle current profile completion on main thread"""
        # Re-enable the profile button
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for btn in widget.winfo_children():
                    if isinstance(btn, ttk.Button) and btn.cget('text') == 'Run Current Profile':
                        btn.config(state='normal')
        
        if log_file:
            messagebox.showinfo("Current Profile Complete", 
                              f"✓ Profile executed successfully!\n\n"
                              f"Log file: {log_file}\n\n"
                              f"Check the logs directory for detailed results.")
        else:
            messagebox.showwarning("Current Profile", 
                                 "Profile execution completed but no log file was generated.")
    
    def _current_profile_failed(self, error_msg):
        """Handle current profile failure on main thread"""
        # Re-enable the profile button
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for btn in widget.winfo_children():
                    if isinstance(btn, ttk.Button) and btn.cget('text') == 'Run Current Profile':
                        btn.config(state='normal')
                        
        messagebox.showerror("Error", f"Current profile failed: {error_msg}")