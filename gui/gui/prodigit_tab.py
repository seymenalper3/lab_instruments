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

        # Control buttons
        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=10)

        self.set_params_btn = ttk.Button(btn_frame, text="Set Parameters", command=self.set_parameters)
        self.set_params_btn.pack(side='left', padx=5)
        
        self.load_on_btn = ttk.Button(btn_frame, text="Load ON", command=self.load_on)
        self.load_on_btn.pack(side='left', padx=5)

        self.load_off_btn = ttk.Button(btn_frame, text="Load OFF", command=self.load_off)
        self.load_off_btn.pack(side='left', padx=5)

        # Status display section
        status_frame = ttk.Frame(self.control_frame)
        status_frame.grid(row=2, column=0, columnspan=4, pady=(10, 5), sticky='w')
        self.mode_status_label = ttk.Label(status_frame, text="Mode: --", font=("TkDefaultFont", 9, "italic"))
        self.mode_status_label.pack(side='left', padx=5)
        self.load_status_label = ttk.Label(status_frame, text="Load: --", font=("TkDefaultFont", 9, "italic"))
        self.load_status_label.pack(side='left', padx=5)

        # CSV profile controls
        self._create_profile_controls()

    def _on_mode_change(self, event=None):
        """Update value label when mode changes."""
        mode = self.mode_combo.get()
        self.value_label.config(text=self.mode_labels[mode])

    def set_parameters(self):
        """Set the appropriate parameter based on the selected mode."""
        def _set_params():
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
        """Turn load on and start monitoring."""
        def _task():
            self.controller.load_on()
            return "Load turned ON. Monitoring started."

        result = self.safe_execute(_task)
        if result:
            # Don't show a messagebox here as it can be annoying.
            # The visual feedback from measurements is enough.
            self._show_success(result, use_statusbar=True, show_popup=False)
            self.is_load_on = True
            self._update_measurements()

    def load_off(self):
        """Turn load off and stop monitoring."""
        def _task():
            self.controller.load_off()
            return "Load turned OFF. Monitoring stopped."

        result = self.safe_execute(_task)
        if result:
            self._show_success(result, use_statusbar=True, show_popup=False)
            self.is_load_on = False
            # Reset labels after a short delay to allow the last update to clear
            self.frame.after(100, self._reset_measurement_labels)

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
        profile_frame.grid(row=3, column=0, columnspan=4, pady=(15, 5), sticky='ew')
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
        """Select a CSV profile file."""
        path = filedialog.askopenfilename(
            title="Select Prodigit CSV profile",
            filetypes=[("CSV Files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.profile_path_var.set(path)

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

        self.profile_running = True
        self._update_profile_control_state(enabled=False)
        self.stop_profile_btn.config(state='normal')
        self.profile_status_var.set("Running profile...")
        self._show_success("Prodigit profile running...", use_statusbar=True, show_popup=False)
        self._set_ui_state(False)

        def worker():
            try:
                log_path = self.controller.run_cc_profile(profile_path, sample_period=sample_period)
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