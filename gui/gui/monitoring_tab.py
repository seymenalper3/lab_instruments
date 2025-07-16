#!/usr/bin/env python3
"""
Monitoring and data logging tab
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import Dict, List
from utils.data_logger import DataLogger


class MonitoringTab:
    """Monitoring and data logging tab"""
    
    def __init__(self, parent):
        self.parent = parent
        self.data_logger = DataLogger()
        self.main_window = None  # Will be set by main window
        self.create_tab()
        
        # Start update cycle
        self.update_display()
        
    def create_tab(self):
        """Create monitoring tab"""
        self.frame = ttk.Frame(self.parent)
        
        # Control frame
        control_frame = ttk.LabelFrame(self.frame, text="Monitoring Control")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Sample interval
        ttk.Label(control_frame, text="Sample Interval (s):").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.interval_entry = ttk.Entry(control_frame, width=10)
        self.interval_entry.grid(row=0, column=1, padx=5, pady=2)
        self.interval_entry.insert(0, "1.0")
        self.interval_entry.bind('<KeyRelease>', self._on_interval_change)
        
        # Control buttons
        self.monitor_btn = ttk.Button(control_frame, text="Start Monitoring", 
                                    command=self.toggle_monitoring)
        self.monitor_btn.grid(row=0, column=2, padx=5, pady=2)
        
        ttk.Button(control_frame, text="Save Data", 
                  command=self.save_data).grid(row=0, column=3, padx=5, pady=2)
                  
        ttk.Button(control_frame, text="Clear Data", 
                  command=self.clear_data).grid(row=0, column=4, padx=5, pady=2)
                  
        ttk.Button(control_frame, text="Refresh Devices", 
                  command=self.refresh_devices).grid(row=0, column=5, padx=5, pady=2)
        
        # Status frame
        status_frame = ttk.LabelFrame(self.frame, text="Status")
        status_frame.pack(fill='x', padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Monitoring stopped")
        self.status_label.grid(row=0, column=0, padx=5, pady=2)
        
        self.data_count_label = ttk.Label(status_frame, text="Data points: 0")
        self.data_count_label.grid(row=0, column=1, padx=20, pady=2)
        
        # Real-time measurements frame
        meas_frame = ttk.LabelFrame(self.frame, text="Real-time Measurements")
        meas_frame.pack(fill='x', padx=5, pady=5)
        
        # Create measurement display widgets
        self.measurement_widgets = {}
        
        # Data display frame
        data_frame = ttk.LabelFrame(self.frame, text="Monitoring Data")
        data_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Scrolled text for data display
        self.data_display = scrolledtext.ScrolledText(data_frame, height=15)
        self.data_display.pack(fill='both', expand=True, padx=5, pady=5)
        
    def add_device(self, name: str, controller):
        """Add a device to monitoring"""
        self.data_logger.add_device(name, controller)
        print(f"Device {name} added to monitoring. Total devices: {len(self.data_logger.devices)}")
        
        # Create measurement display widgets for this device
        if name not in self.measurement_widgets:
            meas_frame = self.frame.children['!labelframe2']  # Real-time measurements frame
            
            row = len(self.measurement_widgets)
            
            device_frame = ttk.LabelFrame(meas_frame, text=name.title())
            device_frame.grid(row=row, column=0, sticky='ew', padx=5, pady=2)
            
            voltage_label = ttk.Label(device_frame, text="Voltage: -- V")
            voltage_label.grid(row=0, column=0, padx=10, pady=2)
            
            current_label = ttk.Label(device_frame, text="Current: -- A")
            current_label.grid(row=0, column=1, padx=10, pady=2)
            
            power_label = ttk.Label(device_frame, text="Power: -- W")
            power_label.grid(row=0, column=2, padx=10, pady=2)
            
            self.measurement_widgets[name] = {
                'frame': device_frame,
                'voltage': voltage_label,
                'current': current_label,
                'power': power_label
            }
    
    def refresh_devices(self):
        """Manually refresh connected devices from all tabs"""
        if self.main_window and hasattr(self.main_window, 'device_tabs'):
            print("Checking for connected devices...")
            for device_name, tab in self.main_window.device_tabs.items():
                if tab.is_connected():
                    print(f"Found connected device: {device_name}")
                    if device_name not in self.data_logger.devices:
                        print(f"Adding {device_name} to monitoring")
                        self.add_device(device_name, tab.get_controller())
                    else:
                        print(f"{device_name} already in monitoring")
                else:
                    print(f"Device {device_name} is not connected")
        else:
            print("No main window reference or device tabs found")
            
    def remove_device(self, name: str):
        """Remove a device from monitoring"""
        self.data_logger.remove_device(name)
        
        if name in self.measurement_widgets:
            self.measurement_widgets[name]['frame'].destroy()
            del self.measurement_widgets[name]
            
    def _on_interval_change(self, event=None):
        """Handle sample interval change"""
        try:
            interval = float(self.interval_entry.get())
            self.data_logger.set_sample_interval(interval)
        except ValueError:
            pass
            
    def toggle_monitoring(self):
        """Start or stop monitoring"""
        if self.data_logger.monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
            
    def start_monitoring(self):
        """Start monitoring"""
        try:
            interval = float(self.interval_entry.get())
            self.data_logger.set_sample_interval(interval)
            self.data_logger.start_monitoring()
            
            self.monitor_btn.config(text="Stop Monitoring")
            self.status_label.config(text="Monitoring active")
            self.interval_entry.config(state="disabled")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid sample interval")
            
    def stop_monitoring(self):
        """Stop monitoring"""
        self.data_logger.stop_monitoring()
        
        self.monitor_btn.config(text="Start Monitoring")
        self.status_label.config(text="Monitoring stopped")
        self.interval_entry.config(state="normal")
        
    def update_display(self):
        """Update monitoring display with new data"""
        try:
            # Get new data points
            new_data = self.data_logger.get_new_data()
            
            for data_point in new_data:
                # Update real-time measurement displays
                for device_name in self.measurement_widgets:
                    widgets = self.measurement_widgets[device_name]
                    
                    voltage_key = f'{device_name}_voltage'
                    current_key = f'{device_name}_current'
                    power_key = f'{device_name}_power'
                    
                    # Get device busy status from data
                    is_busy = data_point.get(f'{device_name}_busy', False)
                    
                    # Show measurements with busy indicator if applicable
                    if voltage_key in data_point and data_point[voltage_key] is not None:
                        voltage_text = f"Voltage: {data_point[voltage_key]:.3f} V"
                        if is_busy:
                            voltage_text += " [PULSE]"
                        widgets['voltage'].config(text=voltage_text, foreground="orange" if is_busy else "black")
                    elif is_busy:
                        widgets['voltage'].config(text="Voltage: PULSE", foreground="orange")
                        
                    if current_key in data_point and data_point[current_key] is not None:
                        current_text = f"Current: {data_point[current_key]:.3f} A"
                        if is_busy:
                            current_text += " [PULSE]"
                        widgets['current'].config(text=current_text, foreground="orange" if is_busy else "black")
                    elif is_busy:
                        widgets['current'].config(text="Current: PULSE", foreground="orange")
                        
                    if power_key in data_point and data_point[power_key] is not None:
                        power_text = f"Power: {data_point[power_key]:.3f} W"
                        if is_busy:
                            power_text += " [PULSE]"
                        widgets['power'].config(text=power_text, foreground="orange" if is_busy else "black")
                    elif is_busy:
                        widgets['power'].config(text="Power: PULSE", foreground="orange")
                
                # Update data display
                self._add_data_line(data_point)
                
            # Update data count
            count = self.data_logger.get_data_count()
            self.data_count_label.config(text=f"Data points: {count}")
            
        except Exception as e:
            print(f"Display update error: {e}")
            
        # Schedule next update
        self.parent.after(100, self.update_display)
        
    def _add_data_line(self, data_point: Dict):
        """Add a data line to the display"""
        timestamp = data_point.get('timestamp', 'Unknown')
        line_parts = [f"{timestamp}:"]
        
        for device_name in self.measurement_widgets:
            voltage = data_point.get(f'{device_name}_voltage')
            current = data_point.get(f'{device_name}_current')
            power = data_point.get(f'{device_name}_power')
            is_busy = data_point.get(f'{device_name}_busy', False)
            
            if voltage is not None or current is not None or power is not None:
                device_part = f" {device_name.upper()}:"
                if voltage is not None:
                    device_part += f" {voltage:.3f}V"
                if current is not None:
                    device_part += f" {current:.3f}A"
                if power is not None:
                    device_part += f" {power:.3f}W"
                # Add busy indicator if device is busy but still measuring
                if is_busy:
                    device_part += " [PULSE]"
                device_part += " |"
                line_parts.append(device_part)
        
        if len(line_parts) > 1:
            line = "".join(line_parts).rstrip(" |") + "\n"
            self.data_display.insert(tk.END, line)
            self.data_display.see(tk.END)
            
    def save_data(self):
        """Save monitoring data to CSV file"""
        if self.data_logger.get_data_count() == 0:
            messagebox.showwarning("Warning", "No data to save")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save monitoring data"
        )
        
        if filename:
            if self.data_logger.save_to_csv(filename):
                messagebox.showinfo("Success", f"Data saved to {filename}")
            else:
                messagebox.showerror("Error", "Failed to save data")
                
    def clear_data(self):
        """Clear all monitoring data"""
        self.data_logger.clear_data()
        self.data_display.delete(1.0, tk.END)
        self.data_count_label.config(text="Data points: 0")
        messagebox.showinfo("Success", "Data cleared")