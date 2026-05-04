#!/usr/bin/env python3
"""
Base device controller class
"""
import time
import threading
import logging
import socket
from abc import ABC, abstractmethod
from typing import Optional
from models.device_config import DeviceSpec, MeasurementData
from interfaces.base_interface import DeviceInterface

logger = logging.getLogger(__name__)


class BaseDeviceController(ABC):
    """Abstract base class for device controllers"""
    
    def __init__(self, interface: DeviceInterface, device_spec: DeviceSpec):
        self.interface = interface
        self.device_spec = device_spec
        self.model = ""
        self.connected = False
        self.busy = False  # Flag to indicate device is busy with special operations
        self._busy_lock = threading.Lock()  # Thread safety for busy flag
        # Serializes every write/read against the underlying interface so that
        # concurrent threads (worker + monitoring + GUI poll) cannot interleave
        # SCPI traffic on a single serial/USB-CDC line. RLock allows the same
        # thread to re-enter (e.g. _handle_timeout calling load_off mid-query).
        self._io_lock = threading.RLock()
        
    def connect(self) -> bool:
        """Connect to the device"""
        try:
            self.interface.connect()
            self.connected = True
            self.identify()
            # Set to remote mode if available
            if hasattr(self, 'remote_mode'):
                self.remote_mode()
            return True
        except Exception as e:
            self.connected = False
            raise e
            
    def disconnect(self):
        """Disconnect from the device with improved safety"""
        # Try to turn off output with retry mechanism
        output_closed = False
        for attempt in range(3):
            try:
                if hasattr(self, 'output_off'):
                    self.output_off()
                    output_closed = True
                    logger.debug("Output turned off during disconnect")
                    break
                if hasattr(self, 'load_off'):
                    self.load_off()
                    output_closed = True
                    logger.debug("Load turned off during disconnect")
                    break
            except Exception as e:
                if attempt == 2:  # Last attempt
                    logger.error(f"Failed to turn off output during disconnect after 3 attempts: {e}")
                else:
                    time.sleep(0.1)  # Short delay before retry
        
        # Set to local mode if available
        try:
            if hasattr(self, 'local_mode'):
                self.local_mode()
                logger.debug("Device set to local mode")
        except Exception as e:
            logger.warning(f"Could not set device to local mode: {e}")
        
        # Disconnect interface
        try:
            self.interface.disconnect()
            self.connected = False
            logger.debug("Device disconnected successfully")
        except Exception as e:
            logger.error(f"Error during interface disconnect: {e}")
            self.connected = False
        
    def identify(self):
        """Identify the device"""
        try:
            identify_cmd = self.device_spec.default_commands.get('identify', '*IDN?')
            self.model = self.interface.query(identify_cmd)
        except Exception:
            self.model = "Unknown"
            
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.connected and self.interface.is_connected()
        
    def set_busy(self, busy: bool):
        """Set device busy state (thread-safe)"""
        with self._busy_lock:
            self.busy = busy
        
    def is_busy(self) -> bool:
        """Check if device is busy with special operations (thread-safe)"""
        with self._busy_lock:
            return self.busy
        
    def is_available_for_monitoring(self) -> bool:
        """Check if device is available for monitoring"""
        return self.is_connected() and not self.is_busy()

    def is_ethernet_connection(self) -> bool:
        """Check if the connection is using Ethernet interface"""
        from interfaces.ethernet_interface import EthernetInterface
        return isinstance(self.interface, EthernetInterface)

    @abstractmethod
    def measure_voltage(self) -> Optional[float]:
        """Read voltage measurement"""
        pass
        
    @abstractmethod
    def measure_current(self) -> Optional[float]:
        """Read current measurement"""
        pass
        
    def measure_power(self) -> Optional[float]:
        """Read power measurement (if supported)"""
        return None
        
    def get_measurements(self) -> MeasurementData:
        """Get all measurements as structured data"""
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        return MeasurementData(
            timestamp=timestamp,
            voltage=self.measure_voltage(),
            current=self.measure_current(),
            power=self.measure_power()
        )
        
    def _check_device_errors(self):
        """Check for device errors after command execution"""
        try:
            # Try standard SCPI error query command
            error_cmd = self.device_spec.default_commands.get('query_error', 'SYST:ERR?')
            error_response = self.query_command(error_cmd)
            
            if error_response:
                # Parse error response (format: "0,No error" or error code)
                error_parts = error_response.split(',')
                if len(error_parts) >= 1:
                    error_code = error_parts[0].strip()
                    # Error code 0 means no error
                    if error_code != '0' and error_code.upper() != 'NO ERROR':
                        error_msg = error_response if len(error_parts) == 1 else ','.join(error_parts[1:])
                        logger.warning(f"Device error detected: {error_response}")
                        # Don't raise exception, just log - let caller decide
                        return error_response
        except Exception as e:
            # Error checking failed - don't block operation
            logger.debug(f"Could not check device errors: {e}")
        
        return None
    
    def _handle_timeout(self, operation: str):
        """Handle timeout exception by attempting to turn off outputs for safety.

        IMPORTANT: when the device is busy with a long-running test (profile
        run, pulse test, battery model, etc.) we MUST NOT auto-shutdown on a
        single transient timeout — that would abort the test. The caller still
        sees the exception and can decide whether to retry. Auto-shutdown is
        only appropriate for one-shot manual operations.
        """
        if self.is_busy():
            logger.warning(
                f"Timeout during {operation} while device is busy - "
                "leaving output untouched and propagating error"
            )
            return

        logger.warning(f"Timeout occurred during {operation} - attempting safe shutdown")
        try:
            # Check if measurement is in process - don't try to turn off output if it is
            # This prevents "Not permitted while measurement is in process" errors
            measurement_active = False
            try:
                if hasattr(self, 'current_mode') and self.current_mode == 'test':
                    # In Battery Test mode, check if measurement is active
                    # Use short timeout to avoid another timeout
                    original_timeout = getattr(self.interface.connection, 'timeout', 5000)
                    if hasattr(self.interface.connection, 'timeout'):
                        self.interface.connection.timeout = 2000  # 2 second timeout for status check
                    try:
                        cond = int(self.query_command(':STAT:OPER:INST:ISUM:COND?'))
                        measuring = bool(cond & 0x10)
                        if measuring:
                            measurement_active = True
                            logger.warning("Measurement in process - skipping output shutdown to avoid error")
                    finally:
                        if hasattr(self.interface.connection, 'timeout'):
                            self.interface.connection.timeout = original_timeout
            except Exception:
                pass  # If status check fails, proceed with shutdown attempt
            
            if measurement_active:
                return  # Don't try to turn off output during active measurement
            
            if hasattr(self, 'output_off'):
                self.output_off()
                logger.info("Output turned off after timeout")
            if hasattr(self, 'load_off'):
                self.load_off()
                logger.info("Load turned off after timeout")
        except Exception as e:
            # Don't log as error if it's "not permitted" error during measurement
            error_str = str(e).lower()
            if 'not permitted' in error_str or 'measurement' in error_str or '720' in str(e):
                logger.warning(f"Could not turn off outputs (measurement may be active): {e}")
            else:
                logger.error(f"Failed to turn off outputs after timeout: {e}")
    
    def send_command(self, command: str, check_errors: bool = False):
        """Send command to device
        
        Args:
            command: Command string to send
            check_errors: If True, check for device errors after sending (default: False for performance)
        """
        if not self.connected:
            raise Exception("Device not connected")

        with self._io_lock:
            try:
                self.interface.write(command)
            except Exception as e:
                # Check if it's a timeout exception
                error_str = str(e).lower()
                if 'timeout' in error_str or isinstance(e, (TimeoutError, socket.timeout)):
                    self._handle_timeout(f"send_command('{command}')")
                raise

            # Optionally check for errors (disabled by default for performance)
            if check_errors:
                error = self._check_device_errors()
                if error:
                    logger.warning(f"Device error after command '{command}': {error}")

    def query_command(self, command: str, check_errors: bool = False) -> str:
        """Send command and get response
        
        Args:
            command: Query command string
            check_errors: If True, check for device errors after query (default: False for performance)
        """
        if not self.connected:
            raise Exception("Device not connected")

        with self._io_lock:
            try:
                response = self.interface.query(command)
            except Exception as e:
                # Check if it's a timeout exception
                error_str = str(e).lower()
                if 'timeout' in error_str or isinstance(e, (TimeoutError, socket.timeout)):
                    self._handle_timeout(f"query_command('{command}')")
                raise

            # Optionally check for errors (disabled by default for performance)
            if check_errors:
                error = self._check_device_errors()
                if error:
                    logger.warning(f"Device error after query '{command}': {error}")

            return response