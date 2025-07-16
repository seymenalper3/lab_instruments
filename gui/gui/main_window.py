#!/usr/bin/env python3
"""
Main application window
"""
import tkinter as tk
from tkinter import ttk
import sys
import platform
from gui.sorensen_tab import SorensenTab
from gui.keithley_tab import KeithleyTab
from gui.prodigit_tab import ProdigitTab
from gui.monitoring_tab import MonitoringTab


class MainWindow:
    """Main application window"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Device Test Controller (Modular)")
        self.root.geometry("1200x800")
        
        # Device tabs
        self.device_tabs = {}
        
        # Create GUI
        self.create_gui()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Center window
        self.center_window()
        
    def create_gui(self):
        """Create the main GUI"""
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create device tabs
        self.create_device_tabs()
        
        # Create monitoring tab
        self.create_monitoring_tab()
        
    def create_device_tabs(self):
        """Create all device tabs"""
        # Sorensen SGX400-12 tab
        self.device_tabs['sorensen'] = SorensenTab(self.notebook)
        self.notebook.add(self.device_tabs['sorensen'].frame, text="Sorensen SGX400-12")
        
        # Keithley 2281S tab
        self.device_tabs['keithley'] = KeithleyTab(self.notebook)
        self.notebook.add(self.device_tabs['keithley'].frame, text="Keithley 2281S")
        
        # Prodigit 34205A tab
        self.device_tabs['prodigit'] = ProdigitTab(self.notebook)
        self.notebook.add(self.device_tabs['prodigit'].frame, text="Prodigit 34205A")
        
    def create_monitoring_tab(self):
        """Create monitoring tab"""
        self.monitoring_tab = MonitoringTab(self.notebook)
        self.monitoring_tab.main_window = self  # Set reference to main window
        self.notebook.add(self.monitoring_tab.frame, text="Monitoring & Logging")
        
        # Register device controllers with monitoring
        for name, tab in self.device_tabs.items():
            # Add callback to register devices when they connect
            original_on_connect = tab.on_connect
            
            def create_connect_wrapper(device_name, original_func):
                def wrapper(config):
                    result = original_func(config)
                    # Add device to monitoring after successful connection
                    if tab.is_connected():
                        self.monitoring_tab.add_device(device_name, tab.get_controller())
                    return result
                return wrapper
            
            tab.on_connect = create_connect_wrapper(name, original_on_connect)
            
            # Add callback to unregister devices when they disconnect
            original_on_disconnect = tab.on_disconnect
            
            def create_disconnect_wrapper(device_name, original_func):
                def wrapper():
                    result = original_func()
                    # Remove device from monitoring after disconnect
                    self.monitoring_tab.remove_device(device_name)
                    return result
                return wrapper
            
            tab.on_disconnect = create_disconnect_wrapper(name, original_on_disconnect)
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def on_closing(self):
        """Handle application closing"""
        # Stop monitoring
        if hasattr(self, 'monitoring_tab'):
            self.monitoring_tab.stop_monitoring()
        
        # Disconnect all devices
        for tab in self.device_tabs.values():
            if tab.is_connected():
                try:
                    tab.on_disconnect()
                except:
                    pass
                    
        self.root.destroy()
        
    def run(self):
        """Run the application"""
        # Check Python version
        if sys.version_info < (3, 6):
            print("This application requires Python 3.6 or later")
            sys.exit(1)
            
        print(f"Multi-Device Test GUI (Modular) started on {platform.system()}")
        
        try:
            import pyvisa
            print("PyVISA available - USB and GPIB support enabled")
        except ImportError:
            print("PyVISA not available - USB and GPIB support limited")
            
        self.root.mainloop()