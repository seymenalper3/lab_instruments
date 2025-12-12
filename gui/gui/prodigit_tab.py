#!/usr/bin/env python3
"""
Prodigit 34205A Electronic Load device tab
"""
import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from controllers.prodigit_controller import ProdigitController
from gui.device_tab import DeviceTab
from models.device_config import DEVICE_SPECS, DeviceType

logger = logging.getLogger(__name__)


class ProdigitTab(DeviceTab):
    """Prodigit 34205A control tab"""

    def __init__(self, parent):
        # Mode labels will be updated after device_spec is available
        self.mode_labels = {
            "CC": "Current (A):",
            "CV": "Voltage (V):",
            "CP": "Power (W):",
            "CR": "Resistance (Ω):"
        }
        self.profile_thread = None
        self.profile_running = False
        self.profile_path_var = None
        self.sample_period_var = None
        self.profile_summary_vars = None
        self.profile_status_var = None
        super().__init__(parent, DEVICE_SPECS[DeviceType.PRODIGIT_34205A], ProdigitController)
        self.is_load_on = False
        
        # Update mode labels with device limits
        self.mode_labels = {
            "CC": f"Current (A, max: {self.device_spec.max_current:.1f}):",
            "CV": f"Voltage (V, max: {self.device_spec.max_voltage:.0f}):",
            "CP": f"Power (W, max: {self.device_spec.max_power:.0f}):",
            "CR": "Resistance (Ω, max: 1.0 MΩ):"
        }

    def _show_error(self, title: str, message: str, use_statusbar: bool = False):
        """Standardized error display."""
        logger.error(f"{title}: {message}")
        if use_statusbar:
            self.status_bar.config(text=message, style="Error.TLabel")
        else:
            messagebox.showerror(title, message)

    def _show_success(self, message: str, use_statusbar: bool = True, show_popup: bool = False):
        """Standardized success display."""
        logger.info(message)
        if use_statusbar:
            self.status_bar.config(text=message, style="Success.TLabel")
        if show_popup:
            messagebox.showinfo("Success", message)

    def create_controls(self):
        """Create Prodigit-specific controls"""
        # Mode selection
        ttk.Label(self.control_frame, text="Mode:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.mode_combo = ttk.Combobox(self.control_frame,
                                       values=list(self.mode_labels.keys()),
                                       state="readonly",
                                       width=8)
        self.mode_combo.grid(row=0, column=1, padx=5, pady=2)
        self.mode_combo.set("CC")
        self.mode_combo.bind('<<ComboboxSelected>>', self._on_mode_change)

        # Value setting
        self.value_label = ttk.Label(self.control_frame, text=self.mode_labels["CC"])
        self.value_label.grid(row=0, column=2, sticky='w', padx=5, pady=2)
        
        self.value_entry = ttk.Entry(self.control_frame, width=10)
        self.value_entry.grid(row=0, column=3, padx=5, pady=2)
        self.value_entry.insert(0, "0.0")

        # Load status indicator
        load_status_frame = ttk.Frame(self.control_frame)
        load_status_frame.grid(row=1, column=0, columnspan=4, pady=5)
        ttk.Label(load_status_frame, text="Load Status:").pack(side='left', padx=5)
        
        # LED-like indicator using canvas
        self.load_status_canvas = tk.Canvas(load_status_frame, width=20, height=20, highlightthickness=0)
        self.load_status_canvas.pack(side='left', padx=5)
        self.load_status_label_text = ttk.Label(load_status_frame, text="OFF", font=('Arial', 9))
        self.load_status_label_text.pack(side='left', padx=5)
        self._update_load_status_indicator(False)
        
        # Control buttons
        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)

        self.set_params_btn = ttk.Button(btn_frame, text="Set Parameters", command=self.set_parameters)
        self.set_params_btn.pack(side='left', padx=5)
        
        self.load_on_btn = ttk.Button(btn_frame, text="Load ON", command=self.load_on)
        self.load_on_btn.pack(side='left', padx=5)

        self.load_off_btn = ttk.Button(btn_frame, text="Load OFF", command=self.load_off)
        self.load_off_btn.pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="❓ Help", command=self.show_help).pack(side='left', padx=15)
        
        # Status display section
        status_frame = ttk.Frame(self.control_frame)
        status_frame.grid(row=3, column=0, columnspan=4, pady=(10, 5), sticky='w')
        self.mode_status_label = ttk.Label(status_frame, text="Mode: --", font=("TkDefaultFont", 9, "italic"))
        self.mode_status_label.pack(side='left', padx=5)
        self.load_status_label = ttk.Label(status_frame, text="Load: --", font=("TkDefaultFont", 9, "italic"))
        self.load_status_label.pack(side='left', padx=5)
        
        # Output format selection
        format_frame = ttk.Frame(self.control_frame)
        format_frame.grid(row=4, column=0, columnspan=4, sticky='w', padx=5, pady=2)
        
        ttk.Label(format_frame, text="Profile Output Format:").pack(side='left', padx=5)
        self.output_format_var = tk.StringVar(value="csv")
        ttk.Radiobutton(format_frame, text="CSV (Fast)", 
                       variable=self.output_format_var, value="csv").pack(side='left', padx=2)
        ttk.Radiobutton(format_frame, text="Excel", 
                       variable=self.output_format_var, value="xlsx").pack(side='left', padx=2)
        ttk.Radiobutton(format_frame, text="Both", 
                       variable=self.output_format_var, value="both").pack(side='left', padx=2)

        # CSV profile controls
        self._create_profile_controls()
    
    def _update_load_status_indicator(self, is_on: bool):
        """Update load status LED indicator"""
        self.load_status_canvas.delete("all")
        color = "#00ff00" if is_on else "#808080"  # Green if ON, Gray if OFF
        self.load_status_canvas.create_oval(2, 2, 18, 18, fill=color, outline="black", width=1)
        self.load_status_label_text.config(text="ON" if is_on else "OFF", 
                                          foreground="green" if is_on else "gray")

    def _on_mode_change(self, event=None):
        """Update value label when mode changes."""
        mode = self.mode_combo.get()
        # Update label with limit information
        if mode in self.mode_labels:
            self.value_label.config(text=self.mode_labels[mode])

    def set_parameters(self):
        """Set the appropriate parameter based on the selected mode."""
        def _set_params():
            # Safety check: Cannot set parameters while profile is running
            if self.controller.is_busy():
                raise RuntimeError(
                    "Cannot set parameters while profile is running. "
                    "Please stop the profile first."
                )
            
            mode = self.mode_combo.get()
            value = float(self.value_entry.get())

            if mode == "CC":
                self.controller.set_mode_cc()
                self.controller.set_current(value)
            elif mode == "CV":
                self.controller.set_mode_cv()
                self.controller.set_voltage(value)
            elif mode == "CP":
                self.controller.set_mode_cp()
                self.controller.set_power(value)
            elif mode == "CR":
                self.controller.set_mode_cr()
                self.controller.set_resistance(value)
            
            return f"Mode set to {mode} with value {value}"

        result = self.safe_execute(_set_params)
        if result:
            self._show_success(result, use_statusbar=True, show_popup=True)

    def load_on(self):
        """Turn load on and start monitoring with safety checks."""
        def _task():
            # Safety check: Cannot enable load while profile is running
            if self.controller.is_busy():
                raise RuntimeError(
                    "Cannot enable load while profile is running. "
                    "Please stop the profile first."
                )
            
            mode = self.mode_combo.get()
            value = float(self.value_entry.get())
            
            # Safety check: Cannot enable load with zero value
            if value == 0.0:
                raise ValueError(
                    "Cannot enable load with zero value. Please set parameters first using 'Set Parameters' button."
                )
            
            # Validate value based on mode and device limits
            if mode == "CC":
                if value < 0 or value > self.device_spec.max_current:
                    raise ValueError(f"Current ({value}A) out of range: 0-{self.device_spec.max_current}A")
            elif mode == "CV":
                if value < 0 or value > self.device_spec.max_voltage:
                    raise ValueError(f"Voltage ({value}V) out of range: 0-{self.device_spec.max_voltage}V")
            elif mode == "CP":
                if value < 0 or value > self.device_spec.max_power:
                    raise ValueError(f"Power ({value}W) out of range: 0-{self.device_spec.max_power}W")
            elif mode == "CR":
                if value <= 0:
                    raise ValueError("Resistance must be a positive value")
            
            # Safety confirmation for high values
            needs_confirmation = False
            confirm_msg = ""
            
            if mode == "CC":
                HIGH_CURRENT_THRESHOLD = self.device_spec.max_current * 0.8
                if value >= HIGH_CURRENT_THRESHOLD:
                    needs_confirmation = True
                    confirm_msg = f"⚠️ HIGH CURRENT WARNING ⚠️\n\n"
                    confirm_msg += f"You are about to enable load with:\n"
                    confirm_msg += f"  Current: {value}A (max: {self.device_spec.max_current}A)\n"
            elif mode == "CV":
                HIGH_VOLTAGE_THRESHOLD = self.device_spec.max_voltage * 0.8
                if value >= HIGH_VOLTAGE_THRESHOLD:
                    needs_confirmation = True
                    confirm_msg = f"⚠️ HIGH VOLTAGE WARNING ⚠️\n\n"
                    confirm_msg += f"You are about to enable load with:\n"
                    confirm_msg += f"  Voltage: {value}V (max: {self.device_spec.max_voltage}V)\n"
            elif mode == "CP":
                HIGH_POWER_THRESHOLD = self.device_spec.max_power * 0.8
                if value >= HIGH_POWER_THRESHOLD:
                    needs_confirmation = True
                    confirm_msg = f"⚠️ HIGH POWER WARNING ⚠️\n\n"
                    confirm_msg += f"You are about to enable load with:\n"
                    confirm_msg += f"  Power: {value}W (max: {self.device_spec.max_power}W)\n"
            
            if needs_confirmation:
                confirm_msg += f"\nThis value is near the device limit.\n"
                confirm_msg += f"Are you sure you want to proceed?"
                
                from tkinter import messagebox
                if not messagebox.askyesno("High Value Confirmation", confirm_msg, icon='warning'):
                    return None  # User cancelled
            
            # Ensure mode and value are set before enabling load
            if mode == "CC":
                self.controller.set_mode_cc()
                self.controller.set_current(value)
            elif mode == "CV":
                self.controller.set_mode_cv()
                self.controller.set_voltage(value)
            elif mode == "CP":
                self.controller.set_mode_cp()
                self.controller.set_power(value)
            elif mode == "CR":
                self.controller.set_mode_cr()
                self.controller.set_resistance(value)
            
            self.controller.load_on()
            self._update_load_status_indicator(True)
            return "Load turned ON. Monitoring started."

        result = self.safe_execute(_task)
        if result:
            # Don't show a messagebox here as it can be annoying.
            # The visual feedback from measurements is enough.
            self._show_success(result, use_statusbar=True, show_popup=False)
            self.is_load_on = True
            self._update_measurements()
        else:
            self._update_load_status_indicator(False)

    def load_off(self):
        """Turn load off and stop monitoring."""
        def _task():
            # Note: load_off is allowed even during profile (for emergency stop)
            # But we log it if profile is running
            if self.controller.is_busy():
                logger.warning("Load turned OFF while profile is running")
            
            self.controller.load_off()
            self._update_load_status_indicator(False)
            return "Load turned OFF. Monitoring stopped."

        result = self.safe_execute(_task)
        if result:
            self._show_success(result, use_statusbar=True, show_popup=False)
            self.is_load_on = False
            # Reset labels after a short delay to allow the last update to clear
            self.frame.after(100, self._reset_measurement_labels)
        else:
            self._update_load_status_indicator(False)

    def _update_measurements(self):
        """Periodically update measurement readings from the device."""
        if not self.is_load_on or not self.is_connected():
            self._reset_measurement_labels()
            self.is_load_on = False
            return

        try:
            # Update measurements
            measurements = self.controller.get_measurements()
            v = measurements.voltage
            i = measurements.current
            p = measurements.power
            
            self.voltage_label.config(text=f"Voltage: {v:.3f} V" if v is not None else "Voltage: -- V")
            self.current_label.config(text=f"Current: {i:.3f} A" if i is not None else "Current: -- A")
            self.power_label.config(text=f"Power: {p:.3f} W" if p is not None else "Power: -- W")

            # Update status
            self._update_status()

        except Exception as e:
            self.is_load_on = False
            self._show_error("Measurement Error", str(e), use_statusbar=True)
            self._reset_measurement_labels()
            return

        # If still active, reschedule the next update
        if self.is_load_on:
            self.frame.after(1000, self._update_measurements)

    def _update_status(self):
        """Query and update the mode and load status labels."""
        try:
            mode = self.controller.query_mode()
            load_status = self.controller.query_load_status()

            if mode:
                self.mode_status_label.config(text=f"Mode: {mode}")
            if load_status:
                self.load_status_label.config(text=f"Load: {load_status}", 
                                             foreground="green" if "ON" in load_status else "red")
        except Exception as e:
            # Don't show a popup, just log to status bar
            self._show_error("Status Update", f"Status update failed: {e}", use_statusbar=True)


    def _reset_measurement_labels(self):
        """Reset measurement labels to default state."""
        self.voltage_label.config(text="Voltage: -- V")
        self.current_label.config(text="Current: -- A")
        self.power_label.config(text="Power: -- W")
        self.mode_status_label.config(text="Mode: --")
        self.load_status_label.config(text="Load: --", foreground="black")

    def _set_ui_state(self, enabled: bool):
        """Enable or disable UI controls."""
        state = 'normal' if enabled else 'disabled'
        self.set_params_btn.config(state=state)
        self.load_on_btn.config(state=state)
        self.load_off_btn.config(state=state)
        self.mode_combo.config(state='readonly' if enabled else 'disabled')
        self.value_entry.config(state=state)
        self._update_profile_control_state(enabled=enabled)

    def on_successful_connect(self):
        super().on_successful_connect()
        self._set_ui_state(True)

    def on_successful_disconnect(self):
        super().on_successful_disconnect()
        self.is_load_on = False  # Ensure monitoring stops
        self._set_ui_state(False)
        self._reset_measurement_labels()
        self._update_profile_summary_labels(None)

    def _create_profile_controls(self):
        """Create CSV profile runner controls."""
        profile_frame = ttk.LabelFrame(self.control_frame, text="CSV CC Profile")
        profile_frame.grid(row=5, column=0, columnspan=4, pady=(15, 5), sticky='ew')
        profile_frame.columnconfigure(1, weight=1)

        self.profile_path_var = tk.StringVar()
        ttk.Label(profile_frame, text="Profile CSV:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.profile_path_entry = ttk.Entry(profile_frame, textvariable=self.profile_path_var, width=40)
        self.profile_path_entry.grid(row=0, column=1, padx=5, pady=2, sticky='ew')

        self.browse_profile_btn = ttk.Button(profile_frame, text="Browse", command=self._browse_profile)
        self.browse_profile_btn.grid(row=0, column=2, padx=5, pady=2)

        self.sample_period_var = tk.StringVar(value="1.0")
        ttk.Label(profile_frame, text="Sample period (s):").grid(row=1, column=0, padx=5, pady=2, sticky='w')
        self.sample_period_entry = ttk.Entry(profile_frame, textvariable=self.sample_period_var, width=8)
        self.sample_period_entry.grid(row=1, column=1, padx=5, pady=2, sticky='w')

        btn_frame = ttk.Frame(profile_frame)
        btn_frame.grid(row=1, column=2, padx=5, pady=2, sticky='e')
        self.load_profile_btn = ttk.Button(btn_frame, text="Load Profile", command=self._load_profile_summary)
        self.load_profile_btn.pack(side='left', padx=2)
        self.start_profile_btn = ttk.Button(btn_frame, text="Start", state='disabled', command=self._start_profile)
        self.start_profile_btn.pack(side='left', padx=2)
        self.stop_profile_btn = ttk.Button(btn_frame, text="Stop", state='disabled', command=self._stop_profile)
        self.stop_profile_btn.pack(side='left', padx=2)

        summary_frame = ttk.Frame(profile_frame)
        summary_frame.grid(row=2, column=0, columnspan=3, pady=(8, 2), sticky='ew')
        self.profile_summary_vars = {
            'segments': tk.StringVar(value="--"),
            'duration': tk.StringVar(value="--"),
            'current': tk.StringVar(value="--")
        }
        ttk.Label(summary_frame, text="Segments:").grid(row=0, column=0, sticky='w', padx=5)
        ttk.Label(summary_frame, textvariable=self.profile_summary_vars['segments']).grid(row=0, column=1, sticky='w')
        ttk.Label(summary_frame, text="Duration (s):").grid(row=0, column=2, sticky='w', padx=5)
        ttk.Label(summary_frame, textvariable=self.profile_summary_vars['duration']).grid(row=0, column=3, sticky='w')
        ttk.Label(summary_frame, text="Current (A):").grid(row=0, column=4, sticky='w', padx=5)
        ttk.Label(summary_frame, textvariable=self.profile_summary_vars['current']).grid(row=0, column=5, sticky='w')

        self.profile_status_var = tk.StringVar(value="Idle")
        ttk.Label(profile_frame, textvariable=self.profile_status_var, font=("TkDefaultFont", 9, "italic")).grid(
            row=3, column=0, columnspan=3, padx=5, pady=(4, 0), sticky='w'
        )

    def _browse_profile(self):
        """Select a profile file (CSV or Excel)."""
        # Show format info first
        info = ("📄 CC Profile Format\n\n"
                "Supported formats: CSV (.csv) or Excel (.xlsx)\n\n"
                "Required columns:\n"
                "  • time_s: Time in seconds (start time of segment)\n"
                "  • current_a: Current in Amperes\n\n"
                "Duration is calculated automatically from time differences\n\n"
                "Example:\n"
                "  time_s | current_a\n"
                "  0      | 5.0        (5A for 10s)\n"
                "  10     | 10.0       (10A for 20s)\n"
                "  30     | 2.5        (2.5A for 30s)\n"
                "  60     | 0.0        (0A - end)\n\n"
                "Note: CSV loads faster (~4x) than Excel\n"
                "For large profiles (>10K rows), prefer CSV\n\n"
                "Output Files:\n"
                "  logs/prodigit_cc_profile_YYYYMMDD_HHMMSS.csv/.xlsx")
        messagebox.showinfo("Profile Format Info", info)
        
        path = filedialog.askopenfilename(
            title="Select Prodigit Profile File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ]
        )
        if path:
            self.profile_path_var.set(path)
    
    def show_help(self):
        """Show Prodigit help guide"""
        help_window = tk.Toplevel(self.frame)
        help_window.title("Prodigit 34205A Help Guide")
        help_window.geometry("750x600")
        
        from tkinter import scrolledtext
        
        help_text = """
PRODIGIT 34205A ELECTRONIC LOAD HELP GUIDE

═══════════════════════════════════════════════════════════

⚡ OPERATING MODES

The Prodigit can operate in four constant modes:

CC - Constant Current:
  Load draws specified current regardless of voltage
  Use for: Battery discharge testing, power supply loading

CV - Constant Voltage:
  Load maintains specified voltage
  Use for: Voltage regulation testing

CP - Constant Power:
  Load maintains specified power (P = V × I)
  Use for: Power supply testing under constant power

CR - Constant Resistance:
  Load simulates specified resistance (R = V / I)
  Use for: Resistive load simulation

═══════════════════════════════════════════════════════════

🔧 BASIC OPERATIONS

1. Set Parameters:
   • Select mode (CC, CV, CP, or CR)
   • Enter value for selected mode
   • Click "Set Parameters" to apply

2. Load ON:
   • Applies the load to connected device
   • Real-time measurements appear in the tab
   • Use "Monitoring & Logging" to record data

3. Load OFF:
   • Disconnects load from device
   • Safe to adjust parameters when OFF

═══════════════════════════════════════════════════════════

📊 CC PROFILE TEST

Executes a time-based current profile automatically.

CSV Format:
  time_s,current_a
  0,5.0          # 5A starting at 0s
  10,10.0        # 10A starting at 10s
  30,2.5         # 2.5A starting at 30s

Parameters:
  • Profile CSV: File with time_s and current_a columns
  • Sample Period: Measurement interval (default: 1s)

Steps:
  1. Click "Browse" and select CSV file
  2. Click "Load Profile" to validate
  3. Review summary (segments, duration, current range)
  4. Click "Start" to begin
  5. Click "Stop" to abort if needed

Output File:
  • logs/prodigit_cc_profile_YYYYMMDD_HHMMSS.csv

Features:
  ✓ Automatic CSV logging
  ✓ Real-time measurements
  ✓ Continuous sampling during profile
  ✓ Device shows [BUSY] in monitoring during test

═══════════════════════════════════════════════════════════

📊 LOGGING BEHAVIOR

CC Profile Test:
  ✓ Creates automatic CSV log
  ✗ Monitoring tab shows [BUSY] (can't measure during test)
  ✓ Check logs/ folder after test completes

Manual Operations (Set Parameters, Load ON/OFF):
  ✗ No automatic logging
  ✓ Real-time display in tab (voltage, current, power)
  ✓ Use "Monitoring & Logging" tab to record:
    - Click "Start Monitoring"
    - Click "Save Data" when done

═══════════════════════════════════════════════════════════

⚠️ SAFETY NOTES

• Do not exceed device ratings:
  - Max Current: 120A
  - Max Voltage: 150V
  - Max Power: 1200W

• Always start with low values and increase gradually
• Monitor temperature during high-power tests
• Use appropriate current ratings for cables and connections

═══════════════════════════════════════════════════════════

💡 TIPS

• Load ON shows real-time measurements in the tab
• Profile test logs automatically - no manual monitoring needed
• For manual tests, start Monitoring & Logging before Load ON
• Check logs/ folder for profile test results
        """
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=('Courier', 9))
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        text_widget.insert('1.0', help_text)
        text_widget.config(state='disabled')
        
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)

    def _load_profile_summary(self):
        """Load profile metadata for display."""
        if not self.is_connected():
            self._show_error("Prodigit", "Connect to the Prodigit before loading a profile.")
            return

        path = self.profile_path_var.get().strip()
        if not path:
            self._browse_profile()
            path = self.profile_path_var.get().strip()
            if not path:
                return

        def _task():
            df = self.controller.load_current_profile(path)
            if df is None:
                raise ValueError("Unable to load the selected profile.")
            return self.controller.get_cached_profile_summary()

        summary = self.safe_execute(_task)
        if summary:
            self._update_profile_summary_labels(summary)
            self.start_profile_btn.config(state='normal')
            self.profile_status_var.set(f"Ready: {Path(summary['file']).name}")

    def _update_profile_summary_labels(self, summary: Optional[dict]):
        """Update the profile summary display."""
        if not summary:
            self.profile_summary_vars['segments'].set("--")
            self.profile_summary_vars['duration'].set("--")
            self.profile_summary_vars['current'].set("--")
            self.profile_status_var.set("Idle")
            return

        self.profile_summary_vars['segments'].set(str(summary.get('segments', '--')))
        self.profile_summary_vars['duration'].set(f"{summary.get('total_duration_s', 0):.1f}")
        min_i = summary.get('min_current_a', 0.0)
        max_i = summary.get('max_current_a', 0.0)
        self.profile_summary_vars['current'].set(f"{min_i:.2f} – {max_i:.2f}")

    def _start_profile(self):
        """Start running the loaded profile on a worker thread."""
        if not self.is_connected():
            self._show_error("Prodigit", "Connect to the Prodigit before starting a profile.")
            return
        if self.profile_running:
            return

        try:
            sample_period = float(self.sample_period_var.get())
        except ValueError:
            self._show_error("Prodigit", "Sample period must be a numeric value.")
            return

        # Validate sample period range
        if sample_period <= 0:
            self._show_error("Prodigit", "Sample period must be greater than 0 seconds.")
            return
        if sample_period > 60.0:
            self._show_error("Prodigit", "Sample period must be 60 seconds or less.")
            return

        profile_path = self.profile_path_var.get().strip()
        if not profile_path:
            self._show_error("Prodigit", "Select a CSV profile first.")
            return

        # Get output format
        output_format = self.output_format_var.get()
        
        self.profile_running = True
        self._update_profile_control_state(enabled=False)
        self.stop_profile_btn.config(state='normal')
        self.profile_status_var.set("Running profile...")
        self._show_success("Prodigit profile running...", use_statusbar=True, show_popup=False)
        self._set_ui_state(False)

        def worker():
            try:
                log_path = self.controller.run_cc_profile(profile_path, sample_period=sample_period, output_format=output_format)
                self._handle_profile_result(success=True, log_path=log_path)
            except Exception as exc:
                self._handle_profile_result(success=False, error=str(exc))

        self.profile_thread = threading.Thread(target=worker, daemon=True)
        self.profile_thread.start()

    def _stop_profile(self):
        """Abort the running profile."""
        if not self.profile_running or not self.controller:
            return
        self.controller.request_profile_abort()
        self.stop_profile_btn.config(state='disabled')
        self.profile_status_var.set("Stopping...")

    def _handle_profile_result(self, success: bool, log_path: Optional[str] = None, error: Optional[str] = None):
        """Marshal worker results back to the GUI thread."""
        def _update():
            self.profile_running = False
            self._set_ui_state(True)
            self._update_profile_control_state(enabled=True)
            self.stop_profile_btn.config(state='disabled')
            if success:
                msg = f"Prodigit profile finished. Log: {log_path}" if log_path else "Prodigit profile finished."
                self.profile_status_var.set(msg)
                self._show_success(msg, use_statusbar=True, show_popup=True)
            else:
                err = error or "Prodigit profile failed."
                self.profile_status_var.set(err)
                self._show_error("Prodigit", err, use_statusbar=True)
                # Also show popup for profile errors as they're important
                messagebox.showerror("Prodigit", err)

        self.frame.after(0, _update)

    def _update_profile_control_state(self, enabled: bool):
        """Enable/disable profile controls depending on device state."""
        state = 'normal' if enabled and self.is_connected() and not self.profile_running else 'disabled'
        self.profile_path_entry.config(state=state)
        self.browse_profile_btn.config(state=state)
        self.load_profile_btn.config(state=state)
        self.sample_period_entry.config(state=state)
        start_state = 'normal' if state == 'normal' and self.profile_summary_vars['segments'].get() != "--" else 'disabled'
        self.start_profile_btn.config(state=start_state)
        if self.profile_running:
            self.stop_profile_btn.config(state='normal')
        else:
            self.stop_profile_btn.config(state='disabled')