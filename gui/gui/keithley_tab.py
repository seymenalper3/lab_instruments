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


class KeithleyTab(DeviceTab):
    """Keithley 2281S control tab"""
    
    def __init__(self, parent):
        super().__init__(parent, DEVICE_SPECS[DeviceType.KEITHLEY_2281S], KeithleyController)
        
    def create_controls(self):
        """Create Keithley-specific controls"""
        # Function selection
        ttk.Label(self.control_frame, text="Function:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.function_combo = ttk.Combobox(self.control_frame, 
                                         values=["Power Supply", "Battery Test", "Battery Simulator"],
                                         state="readonly")
        self.function_combo.grid(row=0, column=1, padx=5, pady=2)
        self.function_combo.set("Power Supply")
        
        # Voltage setting
        ttk.Label(self.control_frame, text="Voltage (V):").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.voltage_entry = ttk.Entry(self.control_frame, width=10)
        self.voltage_entry.grid(row=1, column=1, padx=5, pady=2)
        self.voltage_entry.insert(0, "0")
        
        # Current setting
        ttk.Label(self.control_frame, text="Current (A):").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.current_entry = ttk.Entry(self.control_frame, width=10)
        self.current_entry.grid(row=1, column=3, padx=5, pady=2)
        self.current_entry.insert(0, "0")
        
        # Control buttons
        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Set Parameters", 
                  command=self.set_parameters).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output ON", 
                  command=self.output_on).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output OFF", 
                  command=self.output_off).pack(side='left', padx=5)
        
        # Mode switching buttons
        mode_frame = ttk.Frame(self.control_frame)
        mode_frame.grid(row=3, column=0, columnspan=4, pady=5)
        
        ttk.Label(mode_frame, text="Mode Control:").pack(side='left', padx=5)
        ttk.Button(mode_frame, text="Power Supply Mode", 
                  command=self.switch_to_power_mode).pack(side='left', padx=5)
        ttk.Button(mode_frame, text="Battery Test Mode", 
                  command=self.switch_to_battery_mode).pack(side='left', padx=5)
        
        # Test buttons
        test_frame = ttk.Frame(self.control_frame)
        test_frame.grid(row=4, column=0, columnspan=4, pady=5)
        
        ttk.Button(test_frame, text="Run Pulse Test", 
                  command=self.run_pulse_test).pack(side='left', padx=5)
        ttk.Button(test_frame, text="Generate Battery Model", 
                  command=self.run_battery_model).pack(side='left', padx=5)
        ttk.Button(test_frame, text="Run Current Profile", 
                  command=self.run_current_profile).pack(side='left', padx=5)
                  
        # Current Profile parameters frame
        profile_frame = ttk.LabelFrame(self.control_frame, text="Current Profile Parameters")
        profile_frame.grid(row=5, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        
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
        
        # Pulse test parameters frame
        pulse_frame = ttk.LabelFrame(self.control_frame, text="Pulse Test Parameters")
        pulse_frame.grid(row=6, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        
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
        model_frame.grid(row=7, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        
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
        """Set voltage and current parameters"""
        def _set_params():
            voltage = float(self.voltage_entry.get())
            current = float(self.current_entry.get())
            
            # Switch function if needed
            func = self.function_combo.get()
            if func == "Battery Test":
                self.controller.battery_test_mode()
            
            self.controller.set_voltage(voltage)
            self.controller.set_current_limit(current)
            
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
    
    def switch_to_power_mode(self):
        """Switch to Power Supply mode"""
        def _switch_power():
            success = self.controller.switch_to_power_supply_mode()
            if success:
                return "Switched to Power Supply mode"
            else:
                raise Exception("Failed to switch to Power Supply mode")
                
        result = self.safe_execute(_switch_power)
        if result:
            messagebox.showinfo("Success", result)
    
    def switch_to_battery_mode(self):
        """Switch to Battery Test mode"""
        def _switch_battery():
            success = self.controller.switch_to_battery_test_mode()
            if success:
                return "Switched to Battery Test mode"
            else:
                raise Exception("Failed to switch to Battery Test mode")
                
        result = self.safe_execute(_switch_battery)
        if result:
            messagebox.showinfo("Success", result)
    
    def browse_profile_file(self):
        """Browse for current profile CSV file"""
        file_path = filedialog.askopenfilename(
            title="Select Current Profile CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir="."
        )
        if file_path:
            self.profile_file_var.set(file_path)
            
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
            msg += f"Pulse Current: {pulse_current}A\n\n"
            msg += "This will take approximately "
            msg += f"{pulses * (pulse_time + rest_time + 8):.0f} seconds"
            
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
        """Run pulse test in background thread"""
        try:
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
        """Run battery model test in background thread"""
        try:
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
            
            # Estimate duration by loading profile
            try:
                import pandas as pd
                df = pd.read_csv(profile_path)
                if 'time_s' in df.columns:
                    total_time = df['time_s'].max() if len(df) > 0 else 0
                else:
                    total_time = len(df) * 10  # Rough estimate
            except:
                total_time = 300  # Default estimate
            
            # Confirm profile execution
            msg = f"Run current profile with:\n\n"
            msg += f"Profile: {Path(profile_path).name}\n"
            msg += f"Discharge Current: {discharge_current}A\n"
            msg += f"Charge Voltage: {charge_voltage}V\n\n"
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
                args=(profile_path, discharge_current, charge_voltage)
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
    
    def _run_current_profile_thread(self, profile_path, discharge_current, charge_voltage):
        """Run current profile in background thread"""
        try:
            # Run the profile
            log_file = self.controller.run_current_profile(
                profile_path=profile_path,
                discharge_current=discharge_current,
                charge_voltage=charge_voltage
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