#!/usr/bin/env python3
"""
Main application window
"""
import tkinter as tk
from tkinter import ttk
import sys
import platform
import os
from PIL import Image, ImageTk
from utils.app_logger import get_logger, get_app_logger
from gui.sorensen_tab import SorensenTab
from gui.keithley_tab import KeithleyTab
from gui.prodigit_tab import ProdigitTab
from gui.monitoring_tab import MonitoringTab
from gui.debug_console_tab import DebugConsoleTab

logger = get_logger(__name__)


class MainWindow:
    """Main application window"""
    
    def __init__(self):
        logger.info("Initializing main window...")

        self.root = tk.Tk()
        self.root.title("Multi-Device Test Controller (Modular)")
        self.root.geometry("1200x800")

        # Device tabs
        self.device_tabs = {}

        # Get app logger for debug console
        self.app_logger = get_app_logger()

        # Create GUI
        self.create_gui()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Center window
        self.center_window()

        logger.info("Main window initialized successfully")
        
    def create_gui(self):
        """Create the main GUI"""
        logger.debug("Creating GUI components...")

        # Create compact header with logo
        self.create_header()

        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Create device tabs
        self.create_device_tabs()

        # Create monitoring tab
        self.create_monitoring_tab()

        # Create debug console tab
        self.create_debug_console_tab()

        logger.debug("GUI components created successfully")

    def create_header(self):
        """Create compact professional header with logo and title"""
        logger.debug("Creating compact header...")

        # Header frame - light gray background
        header_frame = tk.Frame(self.root, bg='#f0f0f0', height=120)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)  # Prevent frame from shrinking

        try:
            # Get the path to logo
            current_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(current_dir, '..', 'assets', 'logo.png')

            # Load and resize logo (larger, more visible)
            logo_image = Image.open(logo_path)
            aspect_ratio = logo_image.width / logo_image.height
            new_height = 100
            new_width = int(new_height * aspect_ratio)
            logo_image = logo_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            self.logo_photo = ImageTk.PhotoImage(logo_image)

            # Create label with logo (left side)
            logo_label = tk.Label(header_frame, image=self.logo_photo, bg='#f0f0f0')
            logo_label.pack(side='left', padx=15, pady=10)

            # Create title label (next to logo)
            title_label = tk.Label(
                header_frame,
                text="Multi-Device Test Controller",
                font=('Arial', 16, 'bold'),
                bg='#f0f0f0',
                fg='#2c3e50'
            )
            title_label.pack(side='left', padx=10, pady=10)

            # Also set as window icon
            icon_image = Image.open(logo_path)
            icon_image = icon_image.resize((64, 64), Image.Resampling.LANCZOS)
            self.icon_photo = ImageTk.PhotoImage(icon_image)
            self.root.iconphoto(True, self.icon_photo)

            logger.debug("Header created successfully")

        except Exception as e:
            logger.warning(f"Could not load logo: {e}")
            # Fallback: just show title
            fallback_label = tk.Label(
                header_frame,
                text="Multi-Device Test Controller",
                font=('Arial', 16, 'bold'),
                bg='#f0f0f0',
                fg='#2c3e50'
            )
            fallback_label.pack(side='left', padx=20, pady=10)

    def create_device_tabs(self):
        """Create all device tabs"""
        logger.debug("Creating device tabs...")

        # Sorensen SGX400-12 tab
        self.device_tabs['sorensen'] = SorensenTab(self.notebook)
        self.notebook.add(self.device_tabs['sorensen'].frame, text="Sorensen SGX400-12")
        logger.debug("Sorensen tab created")

        # Keithley 2281S tab
        self.device_tabs['keithley'] = KeithleyTab(self.notebook)
        self.notebook.add(self.device_tabs['keithley'].frame, text="Keithley 2281S")
        logger.debug("Keithley tab created")

        # Prodigit 34205A tab
        self.device_tabs['prodigit'] = ProdigitTab(self.notebook)
        self.notebook.add(self.device_tabs['prodigit'].frame, text="Prodigit 34205A")
        logger.debug("Prodigit tab created")
        
    def create_monitoring_tab(self):
        """Create monitoring tab"""
        logger.debug("Creating monitoring tab...")

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
                        logger.info(f"Device '{device_name}' connected and registered for monitoring")
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
                    logger.info(f"Device '{device_name}' disconnected and removed from monitoring")
                    return result
                return wrapper

            tab.on_disconnect = create_disconnect_wrapper(name, original_on_disconnect)

        logger.debug("Monitoring tab created")

    def create_debug_console_tab(self):
        """Create debug console tab"""
        logger.debug("Creating debug console tab...")

        # Get the log queue from app logger
        log_queue = self.app_logger.get_gui_queue()

        # Create debug console tab
        self.debug_console = DebugConsoleTab(self.notebook, log_queue)
        self.notebook.add(self.debug_console.frame, text="Debug Console")

        logger.debug("Debug console tab created")

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
        logger.info("Application closing...")

        # Stop debug console
        if hasattr(self, 'debug_console'):
            try:
                self.debug_console.stop_monitoring()
                logger.debug("Debug console stopped")
            except Exception as e:
                logger.error(f"Error stopping debug console: {e}")

        # Stop monitoring
        if hasattr(self, 'monitoring_tab'):
            try:
                self.monitoring_tab.stop_monitoring()
                logger.debug("Monitoring stopped")
            except Exception as e:
                logger.error(f"Error stopping monitoring: {e}")

        # Disconnect all devices
        for name, tab in self.device_tabs.items():
            if tab.is_connected():
                try:
                    logger.info(f"Disconnecting {name}...")
                    tab.on_disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting {name}: {e}")

        logger.info("All cleanup completed, closing window")
        self.root.destroy()
        
    def run(self):
        """Run the application"""
        # Check Python version
        if sys.version_info < (3, 6):
            error_msg = "This application requires Python 3.6 or later"
            logger.critical(error_msg)
            print(error_msg)
            sys.exit(1)

        logger.info(f"Multi-Device Test GUI started on {platform.system()}")
        print(f"Multi-Device Test GUI (Modular) started on {platform.system()}")

        try:
            import pyvisa
            logger.info("PyVISA available - USB and GPIB support enabled")
            print("PyVISA available - USB and GPIB support enabled")
        except ImportError:
            logger.warning("PyVISA not available - USB and GPIB support limited")
            print("PyVISA not available - USB and GPIB support limited")

        logger.info("Starting main event loop")
        self.root.mainloop()
        logger.info("Main event loop ended")