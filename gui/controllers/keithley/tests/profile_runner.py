#!/usr/bin/env python3
"""
Keithley Profile Runner - Extract from main controller  
Executes current profiles with automatic mode switching
"""
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class KeithleyProfileRunner:
    """
    Keithley Current Profile Runner
    
    Executes current profiles with automatic switching between charge and discharge modes.
    Requires USB or GPIB connection (NOT Ethernet).
    """
    
    def __init__(self, controller):
        """
        Initialize profile runner
        
        Args:
            controller: Parent KeithleyController instance
        """
        self.controller = controller
    
    def run(self, profile_path: str, discharge_current: float = 1.0,
            charge_voltage: float = 4.2, protection_voltage: float = 4.3,
            sample_period: float = 1.0, output_format: str = 'csv') -> Optional[str]:
        """
        Execute current profile with automatic mode switching between charge and discharge.

        **IMPORTANT - Connection Requirement:**
        This function REQUIRES a USB connection. Ethernet connections are NOT supported
        due to discharge measurement limitations with buffered data over TCP sockets.
        The function will raise an exception if called over Ethernet.

        **Platform Compatibility:**
        - Linux: Fully supported (USB/GPIB via VISA)
        - Windows: Fully supported (USB/GPIB via NI-VISA driver)
        - Connection: USB or GPIB ONLY (NOT Ethernet)

        **How it Works:**
        - Reads current profile from CSV or Excel (columns: time_s, current_a)
        - Automatically switches between Power Supply mode (charge) and Battery Test mode (discharge)
        - Positive currents: Power Supply mode at specified voltage
        - Negative currents: Battery Test mode at specified discharge current
        - Takes measurements at regular intervals (sample_period) during execution
        - Logs all measurements to output file

        Args:
            profile_path: Path to profile file (CSV or Excel) with 'time_s' and 'current_a' columns
            discharge_current: Constant discharge current in amperes (for negative segments)
            charge_voltage: Charging voltage limit in volts
            protection_voltage: Over-voltage protection limit in volts
            sample_period: Measurement interval in seconds (default: 1.0s)
            output_format: Output format ('csv', 'xlsx', or 'both')

        Returns:
            Path to log file if successful, None if failed

        Raises:
            Exception: If device not connected, busy, or using Ethernet connection
            Exception: If profile file cannot be loaded

        Note:
            During execution, the device is marked as BUSY and monitoring is disabled.
            Log file is saved to ./logs/keithley_log_YYYYMMDD_HHMMSS.{csv|xlsx}
        """
        print(f"\n--- Starting current profile execution...")
        print(f"Profile: {profile_path}")
        print(f"Parameters: discharge={discharge_current}A, charge={charge_voltage}V, sample_period={sample_period}s")
        print(f"Output format: {output_format.upper()}")

        # Pre-flight checks
        if self.controller.is_busy():
            error_msg = "Device is busy with another operation"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)

        if not self.controller.connected:
            error_msg = "Device not connected"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)

        if self.controller.is_ethernet_connection():
            raise Exception(
                "Current profile execution is not supported over Ethernet due to discharge measurement limitations. "
                "Please use a USB connection for this test."
            )
            
        # Test communication
        print("Testing device communication...")
        try:
            idn = self.controller.query_command('*IDN?')
            if idn:
                print(f"Device responds: {idn.strip()[:50]}...")
            else:
                raise Exception("Device not responding to *IDN?")
        except Exception as e:
            error_msg = f"Communication test failed: {e}"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)
            
        # Load profile
        print("Loading current profile...")
        profile_df = self.controller.load_current_profile(profile_path)
        if profile_df is None:
            error_msg = "Failed to load current profile"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)

        # Set device as busy
        self.controller.set_busy(True)
        print("Device marked as BUSY - monitoring disabled during profile execution")
        
        # Initialize logger
        self.controller.logger.clear_log()
        self.controller.logger.start_timer()

        print(f"\n--- Starting profile execution with AUTOMATIC mode switching...")
        print(f"Total segments: {len(profile_df)}")
        print(f"Mode switch delay: {self.controller.mode_switch_delay}s")
        print(f"Sample period: {sample_period}s (measurements taken every {sample_period}s)")

        try:
            # Execute profile with mode chunking
            self._execute_profile(profile_df, discharge_current, charge_voltage, 
                                protection_voltage, sample_period)
            
            # Save log with selected format
            log_files = self.controller.logger.save_log(format=output_format)
            log_file = log_files[0] if log_files else None
            
            if len(log_files) > 1:
                print(f"\n[OK] Profile execution completed. Logs saved:")
                for f in log_files:
                    print(f"  - {f}")
            else:
                print(f"\n[OK] Profile execution completed. Log saved to: {log_file}")
            
            return log_file
            
        except KeyboardInterrupt:
            print("\n\n[WARN] Script interrupted by user (Ctrl+C)")
            return None
        except Exception as e:
            print(f"\n\n[ERROR] Unexpected error: {e}")
            print("Attempting device recovery...")
            self._recovery()
            return None
        finally:
            # Always clear busy state and clean up
            print("Cleaning up after profile execution...")
            self.controller.current_mode = None
            self.controller.set_busy(False)
            print("Device no longer BUSY - monitoring re-enabled")
            try:
                self.controller.send_command(':OUTP OFF')
                self.controller.send_command(':BATT:OUTP OFF')
                print("Device cleanup completed - outputs turned off")
            except Exception as cleanup_error:
                print(f"Cleanup error (non-critical): {cleanup_error}")
    
    def _execute_profile(self, profile_df, discharge_current, charge_voltage,
                        protection_voltage, sample_period):
        """Execute profile with mode switching"""
        import pandas as pd

        last_mode = None
        segment_chunk = []
        step_offset = 0

        # Add a dummy row at the end to ensure the last chunk is processed
        sentinel = pd.DataFrame([{'current_a': 999, 'duration_s': 0}], index=[len(profile_df)])
        processing_df = pd.concat([profile_df, sentinel])

        for index, row in processing_df.iterrows():
            current = row['current_a']
            current_mode = 'charge' if current >= 0 else 'discharge'

            # Process chunk when mode changes
            if current_mode != last_mode and last_mode is not None:
                print(f"\n>>> Mode change detected: {last_mode.upper()} → {current_mode.upper()}")
                print(f"    Processing {len(segment_chunk)} segments in {last_mode.upper()} mode.")
                
                if last_mode == 'charge':
                    success = self.controller.run_charge_segments(
                        segment_chunk, step_offset, 
                        charge_voltage, protection_voltage, sample_period
                    )
                else:
                    success = self.controller.run_discharge_segments(
                        segment_chunk, step_offset, 
                        discharge_current, sample_period
                    )
                
                if not success:
                    print(f"Failed to execute {last_mode} segments")
                    raise Exception(f"Segment execution failed in {last_mode} mode")
                
                step_offset += len(segment_chunk)
                segment_chunk = []

            # Add current segment to chunk (skip sentinel)
            if index < len(profile_df):
                segment_chunk.append(row)
            
            last_mode = current_mode
        
        # After processing all rows, there may be a remaining chunk (e.g. profile
        # with only charge or only discharge segments). Process it here.
        if segment_chunk and last_mode is not None:
            print(f"\n>>> Final chunk detected: {len(segment_chunk)} segments in {last_mode.upper()} mode.")
            if last_mode == 'charge':
                success = self.controller.run_charge_segments(
                    segment_chunk, step_offset,
                    charge_voltage, protection_voltage, sample_period
                )
            else:
                success = self.controller.run_discharge_segments(
                    segment_chunk, step_offset,
                    discharge_current, sample_period
                )

            if not success:
                print(f"Failed to execute final {last_mode} segments")
                raise Exception(f"Final segment execution failed in {last_mode} mode")
    
    def _recovery(self):
        """Attempt device recovery"""
        try:
            self.controller.send_command('*RST')
            time.sleep(1)
            self.controller.send_command(':OUTP OFF')
            self.controller.send_command(':BATT:OUTP OFF')
            print("Device recovery attempted")
        except Exception as e:
            logger.error(f"Device recovery failed: {e}")
            print(f"Device recovery failed: {e}")

