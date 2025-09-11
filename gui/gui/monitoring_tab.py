#!/usr/bin/env python3
"""
Monitoring and data logging tab
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import Dict, List
import time
from utils.data_logger import DataLogger
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Matplotlib not available - plotting disabled")


class MonitoringTab:
    """Monitoring and data logging tab"""
    
    def __init__(self, parent):
        self.parent = parent
        self.data_logger = DataLogger()
        self.main_window = None  # Will be set by main window
        self.create_tab()
        
        # Auto-refresh devices periodically
        self.auto_refresh_devices()
        
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
        
        if MATPLOTLIB_AVAILABLE:
            ttk.Button(control_frame, text="Plot Data", 
                      command=self.plot_data).grid(row=0, column=6, padx=5, pady=2)
        
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
            
            mode_label = ttk.Label(device_frame, text="Mode: --", foreground="gray")
            mode_label.grid(row=0, column=3, padx=10, pady=2)
            
            self.measurement_widgets[name] = {
                'frame': device_frame,
                'voltage': voltage_label,
                'current': current_label,
                'power': power_label,
                'mode': mode_label
            }
    
    def refresh_devices(self):
        """Manually refresh connected devices from all tabs"""
        if self.main_window and hasattr(self.main_window, 'device_tabs'):
            connected_count = 0
            for device_name, tab in self.main_window.device_tabs.items():
                if tab.is_connected():
                    connected_count += 1
                    if device_name not in self.data_logger.devices:
                        print(f"Adding {device_name} to monitoring")
                        self.add_device(device_name, tab.get_controller())
                        
                        # Show device mode for Keithley
                        controller = tab.get_controller()
                        if hasattr(controller, 'current_mode') and controller.current_mode:
                            mode_text = f" (Mode: {controller.current_mode.upper()})"
                        else:
                            mode_text = ""
                        print(f"Device {device_name} added{mode_text}")
                else:
                    # Remove disconnected devices from monitoring
                    if device_name in self.data_logger.devices:
                        print(f"Removing disconnected device: {device_name}")
                        self.remove_device(device_name)
            
            # Update status display
            if connected_count > 0:
                status_text = f"Monitoring {connected_count} connected device(s)"
                if not self.data_logger.monitoring:
                    status_text += " - Click 'Start Monitoring' to begin"
                self.status_label.config(text=status_text)
            else:
                self.status_label.config(text="No connected devices found")
        else:
            self.status_label.config(text="Waiting for main window initialization...")
            
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
            
            # Debug: Print when we get new data
            if new_data and int(time.time()) % 10 == 0:  # Every 10 seconds
                print(f"Update display: Got {len(new_data)} new data points")
            
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
                    
                    # Update mode display for this device
                    if device_name in self.data_logger.devices:
                        controller = self.data_logger.devices[device_name]
                        if hasattr(controller, 'current_mode') and controller.current_mode:
                            mode_color = "green" if controller.current_mode == 'power' else "blue"
                            widgets['mode'].config(text=f"Mode: {controller.current_mode.upper()}", 
                                                 foreground=mode_color)
                        else:
                            widgets['mode'].config(text="Mode: --", foreground="gray")
                
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
        try:
            timestamp = data_point.get('timestamp', 'Unknown')
            # Shorten timestamp for better readability
            if len(timestamp) > 19:  # Full timestamp format
                timestamp = timestamp[11:19]  # Keep only HH:MM:SS
            
            line_parts = [f"{timestamp}"]
            
            # Debug: Print what devices we're checking
            device_count = 0
            
            for device_name in self.measurement_widgets:
                voltage = data_point.get(f'{device_name}_voltage')
                current = data_point.get(f'{device_name}_current')
                power = data_point.get(f'{device_name}_power')
                is_busy = data_point.get(f'{device_name}_busy', False)
                
                # Check if we have any valid data (including 0.0 values)
                has_data = (voltage is not None) or (current is not None) or (power is not None) or is_busy
                
                if has_data:
                    device_count += 1
                    device_part = f" | {device_name.upper()}:"
                    
                    if voltage is not None:
                        device_part += f" V={voltage:.3f}V"
                    else:
                        device_part += " V=--"
                        
                    if current is not None:
                        device_part += f" I={current:.3f}A"
                    else:
                        device_part += " I=--"
                        
                    if power is not None:
                        device_part += f" P={power:.3f}W"
                    else:
                        device_part += " P=--"
                        
                    # Add busy indicator if device is busy
                    if is_busy:
                        device_part += " [BUSY]"
                        
                    line_parts.append(device_part)
            
            # Always add a line if we have monitoring active, even if no valid data
            if len(line_parts) > 1 or self.data_logger.monitoring:
                if len(line_parts) == 1:  # No device data
                    line_parts.append(" | No measurement data")
                    
                line = "".join(line_parts) + "\n"
                self.data_display.insert(tk.END, line)
                self.data_display.see(tk.END)
                
                # Limit display to last 1000 lines to prevent memory issues
                line_count = int(self.data_display.index('end-1c').split('.')[0])
                if line_count > 1000:
                    self.data_display.delete('1.0', '100.0')
                    
                # Debug output occasionally
                if device_count > 0 and int(time.time()) % 10 == 0:  # Every 10 seconds
                    print(f"Added monitoring line: {device_count} devices, data keys: {list(data_point.keys())}")
                    
        except Exception as e:
            print(f"Error adding data line: {e}")
            print(f"Data point keys: {list(data_point.keys()) if data_point else 'None'}")
            # Add error line to display
            self.data_display.insert(tk.END, f"ERROR: {str(e)}\n")
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
    
    def auto_refresh_devices(self):
        """Automatically check for connected devices periodically"""
        try:
            self.refresh_devices()
        except Exception as e:
            print(f"Auto-refresh error: {e}")
            
        # Schedule next auto-refresh in 5 seconds
        self.parent.after(5000, self.auto_refresh_devices)
    
    def plot_data(self):
        """Plot measurement data in a new window"""
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror("Error", "Matplotlib is not installed. Cannot create plots.")
            return
            
        if self.data_logger.get_data_count() == 0:
            messagebox.showwarning("Warning", "No data to plot")
            return
        
        # Create a new window for the plot
        plot_window = tk.Toplevel(self.parent)
        plot_window.title("Measurement Data Plot")
        plot_window.geometry("800x600")
        
        # Create matplotlib figure
        fig = Figure(figsize=(10, 8), dpi=80)
        
        # Get data from logger
        data = self.data_logger.measurement_data
        if not data:
            messagebox.showwarning("Warning", "No measurement data available")
            return
        
        # Extract time stamps and convert to relative time
        import datetime
        timestamps = []
        for point in data:
            try:
                ts = datetime.datetime.strptime(point['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
                timestamps.append(ts)
            except:
                # Skip invalid timestamps
                continue
        
        if not timestamps:
            messagebox.showerror("Error", "No valid timestamps found")
            return
            
        # Convert to relative time in seconds
        start_time = timestamps[0]
        relative_times = [(ts - start_time).total_seconds() for ts in timestamps]
        
        # Create subplots for each device
        device_names = list(self.data_logger.devices.keys())
        if not device_names:
            messagebox.showwarning("Warning", "No devices to plot")
            return
            
        num_devices = len(device_names)
        
        for i, device_name in enumerate(device_names):
            # Create subplot (3 plots per device: V, I, P)
            ax1 = fig.add_subplot(num_devices, 3, i*3 + 1)
            ax2 = fig.add_subplot(num_devices, 3, i*3 + 2)
            ax3 = fig.add_subplot(num_devices, 3, i*3 + 3)
            
            # Extract data for this device
            voltages = []
            currents = []
            powers = []
            
            for j, point in enumerate(data[:len(relative_times)]):
                voltages.append(point.get(f'{device_name}_voltage'))
                currents.append(point.get(f'{device_name}_current'))
                powers.append(point.get(f'{device_name}_power'))
            
            # Plot voltage
            valid_v = [(t, v) for t, v in zip(relative_times, voltages) if v is not None]
            if valid_v:
                times_v, volts = zip(*valid_v)
                ax1.plot(times_v, volts, 'b-', linewidth=1)
                ax1.set_ylabel('Voltage (V)')
                ax1.set_title(f'{device_name.title()} - Voltage')
                ax1.grid(True, alpha=0.3)
            
            # Plot current  
            valid_i = [(t, i) for t, i in zip(relative_times, currents) if i is not None]
            if valid_i:
                times_i, amps = zip(*valid_i)
                ax2.plot(times_i, amps, 'r-', linewidth=1)
                ax2.set_ylabel('Current (A)')
                ax2.set_title(f'{device_name.title()} - Current')
                ax2.grid(True, alpha=0.3)
            
            # Plot power
            valid_p = [(t, p) for t, p in zip(relative_times, powers) if p is not None]
            if valid_p:
                times_p, watts = zip(*valid_p)
                ax3.plot(times_p, watts, 'g-', linewidth=1)
                ax3.set_ylabel('Power (W)')
                ax3.set_title(f'{device_name.title()} - Power')
                ax3.grid(True, alpha=0.3)
            
            # Set x-label for bottom row
            if i == num_devices - 1:
                ax1.set_xlabel('Time (s)')
                ax2.set_xlabel('Time (s)')
                ax3.set_xlabel('Time (s)')
        
        fig.tight_layout()
        
        # Add canvas to window
        canvas = FigureCanvasTkAgg(fig, plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        try:
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            toolbar = NavigationToolbar2Tk(canvas, plot_window)
            toolbar.update()
        except ImportError:
            pass  # Toolbar not available
        
        print(f"Plot created with {len(relative_times)} data points for {len(device_names)} device(s)")