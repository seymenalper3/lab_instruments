#!/usr/bin/env python3
"""
Keithley 2281S device tab
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.device_tab import DeviceTab
from models.device_config import DEVICE_SPECS, DeviceType
from controllers.keithley_controller import KeithleyController


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
        ttk.Button(btn_frame, text="Run Pulse Test", 
                  command=self.run_pulse_test).pack(side='left', padx=5)
                  
        # Pulse test parameters frame
        pulse_frame = ttk.LabelFrame(self.control_frame, text="Pulse Test Parameters")
        pulse_frame.grid(row=3, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        
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