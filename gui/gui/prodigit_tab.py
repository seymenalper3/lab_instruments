#!/usr/bin/env python3
"""
Prodigit 34205A Electronic Load device tab
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.device_tab import DeviceTab
from models.device_config import DEVICE_SPECS, DeviceType
from controllers.prodigit_controller import ProdigitController


class ProdigitTab(DeviceTab):
    """Prodigit 34205A control tab"""

    def __init__(self, parent):
        self.mode_labels = {
            "CC": "Current (A):",
            "CV": "Voltage (V):",
            "CP": "Power (W):",
            "CR": "Resistance (Ω):"
        }
        super().__init__(parent, DEVICE_SPECS[DeviceType.PRODIGIT_34205A], ProdigitController)
        self.is_load_on = False

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
            messagebox.showinfo("Success", result)

    def load_on(self):
        """Turn load on and start monitoring."""
        def _task():
            self.controller.load_on()
            return "Load turned ON. Monitoring started."

        result = self.safe_execute(_task)
        if result:
            # Don't show a messagebox here as it can be annoying.
            # The visual feedback from measurements is enough.
            self.status_bar.config(text=result, style="Success.TLabel")
            self.is_load_on = True
            self._update_measurements()

    def load_off(self):
        """Turn load off and stop monitoring."""
        def _task():
            self.controller.load_off()
            return "Load turned OFF. Monitoring stopped."

        result = self.safe_execute(_task)
        if result:
            self.status_bar.config(text=result, style="Success.TLabel")
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
            self.status_bar.config(text=f"Measurement Error: {e}", style="Error.TLabel")
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
            self.status_bar.config(text=f"Status update failed: {e}", style="Error.TLabel")


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

    def on_successful_connect(self):
        super().on_successful_connect()
        self._set_ui_state(True)

    def on_successful_disconnect(self):
        super().on_successful_disconnect()
        self.is_load_on = False  # Ensure monitoring stops
        self._set_ui_state(False)
        self._reset_measurement_labels()