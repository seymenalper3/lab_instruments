#!/usr/bin/env python3
"""
Prodigit 34205A Electronic Load Controller
"""
from pathlib import Path
from typing import Optional, Dict, Any
import threading
import logging

import time

from controllers.base_controller import BaseDeviceController
from models.device_config import DEVICE_SPECS, DeviceType
from utils.prodigit_logger import ProdigitProfileLogger

logger = logging.getLogger(__name__)


class ProdigitController(BaseDeviceController):
    """Prodigit 34205A Electronic Load Controller"""

    PROFILE_MIN_DWELL_S = 1.0
    PROFILE_MAX_DURATION_S = 14400.0  # Guardrail for ~4 hour runs
    PROFILE_SAFE_CURRENT_A = 120.0  # Conservative continuous current limit
    PROFILE_MAX_SEGMENTS = 100000  # Support up to 100k segments (4h @ 5Hz)

    def __init__(self, interface):
        super().__init__(interface, DEVICE_SPECS[DeviceType.PRODIGIT_34205A])
        self.current_mode = None
        self._sleep_fn = time.sleep
        self._profile_abort_event = threading.Event()
        self._cached_profile_summary: Optional[Dict[str, Any]] = None
        self._cached_profile_path: Optional[str] = None
        self._cached_profile_df = None  # Optional[pd.DataFrame]
        self._last_set_current = 0.0

    def send_command(self, command: str, check_errors: bool = False):
        """
        Override send_command to add a delay for Prodigit devices.
        
        Note: Prodigit devices don't support SYST:ERR? command, so we skip
        error checking even if check_errors=True to avoid timeouts.
        """
        # Prodigit doesn't support SYST:ERR?, so skip error checking
        # but still send the command with delay
        if not self.connected:
            raise Exception("Device not connected")
        
        try:
            self.interface.write(command)
        except Exception as e:
            raise
        
        # Delay from manual spec (50ms min between measurement instructions + safety margin)
        delay = self.device_spec.timing.send_delay_s if self.device_spec.timing else 0.1
        time.sleep(delay)
    
    def query_command(self, command: str, check_errors: bool = False) -> str:
        """
        Override query_command to add delays for Prodigit devices.
        
        Prodigit devices require delays between commands to avoid response confusion.
        Using write() + read() instead of query() to have better control over timing.
        
        Optimized: Only clear buffer if not already cleared (e.g., by get_measurements()).
        """
        if not self.connected:
            raise Exception("Device not connected")
        
        try:
            # Clear buffer for standalone queries to prevent response mixing
            # Note: get_measurements() also clears buffer, but standalone queries
            # (like query_mode(), query_load_status()) need their own clearing
            try:
                self.interface.connection.clear()
            except Exception:
                pass  # Ignore if clear() fails (e.g., not a VISA connection)
            
            # Send command with delay from manual spec
            self.interface.write(command)
            write_delay = self.device_spec.timing.query_write_delay_s if self.device_spec.timing else 0.08
            time.sleep(write_delay)

            # Read response
            response = self.interface.read()
            read_delay = self.device_spec.timing.query_read_delay_s if self.device_spec.timing else 0.03
            time.sleep(read_delay)
            
            return response.strip()
        except Exception as e:
            # Check if it's a timeout exception
            error_str = str(e).lower()
            if 'timeout' in error_str:
                self._handle_timeout(f"query_command('{command}')")
            raise

    def _set_mode(self, mode_cmd: str, mode_name: str):
        """Helper to set the device mode."""
        self.send_command(mode_cmd)
        self.current_mode = mode_name
        # time.sleep(0.2) # Delay is now in send_command

    def set_mode_cc(self):
        """Set Constant Current mode."""
        cmd = self.device_spec.default_commands['set_mode_cc']
        self._set_mode(cmd, 'CC')

    def set_mode_cv(self):
        """Set Constant Voltage mode."""
        cmd = self.device_spec.default_commands['set_mode_cv']
        self._set_mode(cmd, 'CV')

    def set_mode_cp(self):
        """Set Constant Power mode."""
        cmd = self.device_spec.default_commands['set_mode_cp']
        self._set_mode(cmd, 'CP')

    def set_mode_cr(self):
        """Set Constant Resistance mode."""
        cmd = self.device_spec.default_commands['set_mode_cr']
        self._set_mode(cmd, 'CR')

    def set_current(self, current: float):
        """Set current in Amperes (for CC mode)."""
        if self.is_busy():
            raise RuntimeError("Cannot set current while profile is running. Stop profile first.")
        
        if current < 0:
            raise ValueError("Constant current profiles must use non-negative values")
        if current > self.device_spec.max_current:
            raise ValueError(f"Current must be between 0 and {self.device_spec.max_current}A")
        cmd = self.device_spec.default_commands['set_current'].format(current)
        self.send_command(cmd)
        self._last_set_current = current

    def set_voltage(self, voltage: float):
        """Set voltage in Volts (for CV mode)."""
        if self.is_busy():
            raise RuntimeError("Cannot set voltage while profile is running. Stop profile first.")
        
        if not 0 <= voltage <= self.device_spec.max_voltage:
            raise ValueError(f"Voltage must be between 0 and {self.device_spec.max_voltage}V")
        cmd = self.device_spec.default_commands['set_voltage'].format(voltage)
        self.send_command(cmd)

    def set_power(self, power: float):
        """Set power in Watts (for CP mode)."""
        if self.is_busy():
            raise RuntimeError("Cannot set power while profile is running. Stop profile first.")
        
        if not 0 <= power <= self.device_spec.max_power:
            raise ValueError(f"Power must be between 0 and {self.device_spec.max_power}W")
        cmd = self.device_spec.default_commands['set_power'].format(power)
        self.send_command(cmd)

    def set_resistance(self, resistance: float):
        """Set resistance in Ohms (for CR mode)."""
        if self.is_busy():
            raise RuntimeError("Cannot set resistance while profile is running. Stop profile first.")
        
        # Safety: Add upper limit for resistance (1 MΩ = 1,000,000 Ω)
        MAX_RESISTANCE_OHMS = 1_000_000.0
        if not 0 < resistance <= MAX_RESISTANCE_OHMS:
            raise ValueError(
                f"Resistance must be between 0 and {MAX_RESISTANCE_OHMS/1_000_000:.1f} MΩ "
                f"(0 and {MAX_RESISTANCE_OHMS:.0f} Ω)"
            )
        cmd = self.device_spec.default_commands['set_resistance'].format(resistance)
        self.send_command(cmd)

    def load_on(self):
        """Turn load on."""
        logger.warning("Turning load ON - safety critical operation")
        cmd = self.device_spec.default_commands['load_on']
        self.send_command(cmd, check_errors=True)
        logger.info("Load turned ON successfully")

    def load_off(self):
        """Turn load off."""
        logger.info("Turning load OFF")
        cmd = self.device_spec.default_commands['load_off']
        self.send_command(cmd, check_errors=True)
        logger.info("Load turned OFF successfully")

    def measure_voltage(self) -> Optional[float]:
        """Read voltage measurement."""
        try:
            cmd = self.device_spec.default_commands['measure_voltage']
            response = self.query_command(cmd)
            return float(response)
        except (ValueError, TypeError):
            return None

    def measure_current(self) -> Optional[float]:
        """Read current measurement."""
        try:
            cmd = self.device_spec.default_commands['measure_current']
            response = self.query_command(cmd)
            return float(response)
        except (ValueError, TypeError):
            return None

    def measure_power(self) -> Optional[float]:
        """Read power measurement."""
        try:
            cmd = self.device_spec.default_commands['measure_power']
            response = self.query_command(cmd)
            return float(response)
        except (ValueError, TypeError):
            return None

    def get_measurements(self):
        """
        Override get_measurements to ensure proper buffer management and data validation.
        This ensures all three measurements (voltage, current, power) are read atomically
        with proper buffer clearing to prevent response mixing.
        
        Optimized for monitoring: single buffer clear at start, minimal delays.
        """
        from datetime import datetime
        from models.device_config import MeasurementData
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Clear buffer once at the start to prevent mixing
        try:
            self.interface.connection.clear()
        except Exception:
            pass
        
        # Read measurements with proper error handling
        # Note: Each measure_* method will do its own query_command with delays,
        # but we've already cleared the buffer once at the start
        voltage = None
        current = None
        power = None
        
        try:
            # Measure voltage
            voltage = self.measure_voltage()
        except Exception as e:
            logger.debug(f"Error measuring voltage: {e}")
        
        try:
            # Measure current
            current = self.measure_current()
        except Exception as e:
            logger.debug(f"Error measuring current: {e}")
        
        try:
            # Measure power
            power = self.measure_power()
        except Exception as e:
            logger.debug(f"Error measuring power: {e}")
        
        # Validate data consistency: P should be approximately V * I
        # Allow 5% tolerance for measurement errors
        if voltage is not None and current is not None and power is not None:
            expected_power = voltage * current
            tolerance = abs(expected_power * 0.05)  # 5% tolerance
            if abs(power - expected_power) > max(tolerance, 0.1):  # At least 0.1W tolerance
                # If power doesn't match, recalculate it from V*I
                logger.warning(
                    f"Power mismatch detected: measured={power:.2f}W, "
                    f"expected={expected_power:.2f}W (V={voltage:.2f}V, I={current:.3f}A). "
                    f"Using calculated power."
                )
                power = expected_power
        
        return MeasurementData(
            timestamp=timestamp,
            voltage=voltage,
            current=current,
            power=power
        )

    # Manual: MODE? returns 0:CC, 1:CR, 2:CV, 3:CP
    _MODE_MAP = {'0': 'CC', '1': 'CR', '2': 'CV', '3': 'CP'}
    # Manual: LOAD? returns 0:OFF, 1:ON
    _LOAD_MAP = {'0': 'OFF', '1': 'ON'}

    def query_mode(self) -> Optional[str]:
        """Query the current operating mode. Returns CC/CR/CV/CP."""
        try:
            cmd = self.device_spec.default_commands['query_mode']
            raw = self.query_command(cmd).strip()
            return self._MODE_MAP.get(raw, raw)
        except Exception:
            return None

    def query_load_status(self) -> Optional[str]:
        """Query the load status. Returns ON/OFF."""
        try:
            cmd = self.device_spec.default_commands['query_load']
            raw = self.query_command(cmd).strip()
            return self._LOAD_MAP.get(raw, raw)
        except Exception:
            return None

    def query_error(self) -> Optional[str]:
        """Query for errors."""
        try:
            cmd = self.device_spec.default_commands['query_error']
            return self.query_command(cmd)
        except Exception:
            return None

    def output_on(self):
        """Wrapper for load_on to match base controller expectations."""
        self.load_on()

    def output_off(self):
        """Wrapper for load_off to match base controller expectations."""
        self.load_off()

    def load_current_profile(self, csv_path: str):
        """
        Load and validate a current profile from CSV or Excel file for CC operation.
        Supports: .csv, .xlsx
        Expected columns: time_s, current_a

        Returns:
            pandas.DataFrame or None
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas paketi gerekli: pip install pandas")

        # Clear cache at start - will be repopulated if successful
        self._clear_profile_cache()

        path = Path(csv_path).expanduser()
        if not path.exists():
            logger.error(f"Profile file not found: {csv_path}")
            return None

        try:
            start_time = time.time()

            # Read file based on extension (optimized)
            if str(path).endswith('.xlsx') or str(path).endswith('.xls'):
                try:
                    import openpyxl  # Lazy import
                    df = pd.read_excel(path, engine='openpyxl')
                    logger.info(f"Excel profile loaded in {time.time() - start_time:.2f}s")
                except ImportError:
                    raise Exception("Excel support requires openpyxl. Install: pip install openpyxl")
            else:
                df = pd.read_csv(path)
                logger.info(f"CSV profile loaded in {time.time() - start_time:.2f}s")
        except Exception as exc:
            logger.error(f"Failed to read profile {csv_path}: {exc}")
            return None

        if 'time_s' not in df.columns or 'current_a' not in df.columns:
            logger.error("Profile CSV must contain 'time_s' and 'current_a' columns.")
            return None

        df = df.copy()
        df['time_s'] = pd.to_numeric(df['time_s'], errors='coerce')
        df['current_a'] = pd.to_numeric(df['current_a'], errors='coerce')
        df = df.dropna(subset=['time_s', 'current_a'])
        if df.empty:
            logger.error("Profile CSV does not contain any valid rows.")
            return None

        if (df['current_a'] < 0).any():
            raise ValueError("Prodigit CC profiles do not support negative current setpoints.")

        df = df.sort_values('time_s').reset_index(drop=True)
        df['duration_s'] = df['time_s'].shift(-1) - df['time_s']
        median_duration = df['duration_s'].median()
        fallback_duration = median_duration if pd.notna(median_duration) and median_duration > 0 else self.PROFILE_MIN_DWELL_S
        df['duration_s'] = df['duration_s'].fillna(fallback_duration)
        df.loc[df['duration_s'] <= 0, 'duration_s'] = fallback_duration
        df['duration_s'] = df['duration_s'].clip(lower=self.PROFILE_MIN_DWELL_S)

        if len(df) > self.PROFILE_MAX_SEGMENTS:
            raise ValueError(f"Profile contains {len(df)} segments; maximum supported is {self.PROFILE_MAX_SEGMENTS}.")

        total_duration = float(df['duration_s'].sum())
        if total_duration > self.PROFILE_MAX_DURATION_S:
            raise ValueError(
                f"Profile duration {total_duration:.1f}s exceeds safe guardrail of {self.PROFILE_MAX_DURATION_S:.0f}s."
            )

        max_current = float(df['current_a'].max())
        safe_limit = min(self.device_spec.max_current, self.PROFILE_SAFE_CURRENT_A)
        if max_current > safe_limit:
            raise ValueError(
                f"Profile current {max_current:.1f}A exceeds the continuous guardrail of {safe_limit:.1f}A."
            )

        self._cached_profile_summary = {
            'segments': len(df),
            'total_duration_s': total_duration,
            'min_current_a': float(df['current_a'].min()),
            'max_current_a': max_current,
            'file': str(path)
        }
        self._cached_profile_path = str(path)
        self._cached_profile_df = df.copy()
        logger.info(
            f"Profile loaded: {len(df)} segments, "
            f"{df['duration_s'].sum():.1f}s, "
            f"{df['current_a'].min():.2f}-{df['current_a'].max():.2f} A"
        )
        return df

    def get_cached_profile_summary(self) -> Optional[Dict[str, Any]]:
        """Return the most recent profile summary generated by load_current_profile."""
        return self._cached_profile_summary

    def _clear_profile_cache(self):
        """Clear all cached profile data."""
        self._cached_profile_summary = None
        self._cached_profile_path = None
        self._cached_profile_df = None

    def request_profile_abort(self):
        """Signal an ongoing profile run to abort at the next safe checkpoint."""
        if self.is_busy():
            self._profile_abort_event.set()

    def run_cc_profile(self, profile_path: str, sample_period: float = 1.0, output_format: str = 'csv') -> Optional[str]:
        """
        Execute a constant-current profile defined in a CSV file.

        Args:
            profile_path: Path to CSV with columns (time_s, current_a).
            sample_period: Interval in seconds between measurements/log entries.
            output_format: Output format ('csv', 'xlsx', or 'both')
        Returns:
            Path to the generated log file (first file if multiple).
        """
        if sample_period <= 0:
            raise ValueError("Sample period must be greater than 0.")

        if self.is_busy():
            raise RuntimeError("Prodigit is busy running another operation.")

        if not self.is_connected():
            raise RuntimeError("Prodigit must be connected before running a profile.")

        # Validate cache or reload profile
        normalized_path = str(Path(profile_path).expanduser().resolve())
        if (self._cached_profile_df is None or
            self._cached_profile_path is None or
            str(Path(self._cached_profile_path).resolve()) != normalized_path):
            # Cache miss or path mismatch - reload profile
            profile_df = self.load_current_profile(profile_path)
            if profile_df is None:
                raise RuntimeError("Failed to load current profile.")
        else:
            # Use cached profile
            profile_df = self._cached_profile_df.copy()

        profile_logger = ProdigitProfileLogger()
        profile_logger.start(
            csv_path=Path(profile_path),
            sample_period=sample_period,
            segment_count=len(profile_df),
            total_duration=float(profile_df['duration_s'].sum())
        )

        self.set_busy(True)
        self._profile_abort_event.clear()
        total_elapsed = 0.0
        log_path: Optional[str] = None

        try:
            self.set_mode_cc()
            # start with a safe default current, then enable the load
            self.set_current(0.0)
            self.load_on()

            for index, row in profile_df.iterrows():
                if self._profile_abort_event.is_set():
                    raise InterruptedError("Profile aborted by user request.")

                target_current = float(row['current_a'])
                duration = float(row['duration_s'])
                segment_elapsed = 0.0

                self.set_current(target_current)
                measurements = self.get_measurements()
                profile_logger.log_sample(
                    segment_index=index + 1,
                    set_current=target_current,
                    measured_voltage=measurements.voltage,
                    measured_current=measurements.current,
                    measured_power=measurements.power,
                    elapsed_segment_s=segment_elapsed,
                    elapsed_total_s=total_elapsed,
                    status='SET'
                )

                while segment_elapsed < duration:
                    remaining = duration - segment_elapsed
                    sleep_window = min(sample_period, remaining)
                    if sleep_window > 0:
                        self._sleep_fn(sleep_window)
                        segment_elapsed += sleep_window
                        total_elapsed += sleep_window

                    if self._profile_abort_event.is_set():
                        raise InterruptedError("Profile aborted by user request.")

                    measurements = self.get_measurements()
                    profile_logger.log_sample(
                        segment_index=index + 1,
                        set_current=target_current,
                        measured_voltage=measurements.voltage,
                        measured_current=measurements.current,
                        measured_power=measurements.power,
                        elapsed_segment_s=segment_elapsed,
                        elapsed_total_s=total_elapsed,
                        status='RUN'
                    )

            log_paths = profile_logger.finalize(outcome='COMPLETED', output_format=output_format)
            log_path = log_paths[0] if log_paths else None
            return log_path

        except InterruptedError as abort_exc:
            log_paths = profile_logger.finalize(outcome='ABORTED', error_message=str(abort_exc), output_format=output_format)
            log_path = log_paths[0] if log_paths else None
            raise
        except Exception as exc:
            log_paths = profile_logger.finalize(outcome='ERROR', error_message=str(exc), output_format=output_format)
            log_path = log_paths[0] if log_paths else None
            raise
        finally:
            # Attempt cleanup with multiple retries
            cleanup_success = False
            cleanup_error = None
            for attempt in range(3):
                try:
                    self.load_off()
                    cleanup_success = True
                    break
                except Exception as exc:
                    cleanup_error = exc
                    if attempt < 2:  # Don't sleep on last attempt
                        time.sleep(0.5)

            if not cleanup_success:
                error_msg = f"Failed to turn off load after 3 attempts: {cleanup_error}"
                logger.error(f"WARNING: {error_msg}")
                # Store error for GUI to potentially display
                if log_path:
                    try:
                        with open(log_path, 'a') as f:
                            f.write(f"\nWARNING: {error_msg}\n")
                    except Exception:
                        pass

            self.set_busy(False)
            self._profile_abort_event.clear()

            if log_path:
                logger.info(f"Prodigit CC profile log saved to: {log_path}")