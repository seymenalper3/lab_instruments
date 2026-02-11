#!/usr/bin/env python3
"""
Data logging and monitoring utilities
"""
import csv
import queue
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from models.device_config import MeasurementData

logger = logging.getLogger(__name__)


class DataLogger:
    """Data logging and monitoring system"""
    
    # Maximum number of data points to keep in memory (prevents memory leak)
    # 12 hours at 1s interval = 43,200 points, so 100k is a safe limit
    MAX_DATA_POINTS = 100000
    
    def __init__(self):
        self.monitoring = False
        self.monitoring_thread = None
        self.data_queue = queue.Queue()
        self.measurement_data = []
        self.devices = {}
        self.devices_lock = threading.Lock()  # Thread safety for device dict access
        self.sample_interval = 1.0
        self.callbacks = []
        
    def add_device(self, name: str, controller):
        """Add a device controller for monitoring"""
        with self.devices_lock:
            self.devices[name] = controller
        
    def remove_device(self, name: str):
        """Remove a device from monitoring"""
        with self.devices_lock:
            if name in self.devices:
                del self.devices[name]
            
    def set_sample_interval(self, interval: float):
        """Set monitoring sample interval in seconds"""
        self.sample_interval = max(0.1, interval)
        
    def add_callback(self, callback: Callable):
        """Add callback function to be called when new data is available"""
        self.callbacks.append(callback)
        
    def start_monitoring(self):
        """Start monitoring all connected devices"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_worker)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
            
    def _monitoring_worker(self):
        """Worker thread for monitoring devices"""
        while self.monitoring:
            try:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                data_point = {'timestamp': timestamp}
                
                # Collect measurements from all connected devices
                # Create a copy of devices dict to avoid threading issues
                with self.devices_lock:
                    devices_copy = dict(self.devices)
                for device_name, controller in devices_copy.items():
                    if controller and controller.is_connected():
                        # Skip busy devices to avoid interference with special operations
                        if controller.is_busy():
                            data_point[f'{device_name}_voltage'] = None
                            data_point[f'{device_name}_current'] = None
                            data_point[f'{device_name}_power'] = None
                            data_point[f'{device_name}_busy'] = True
                        else:
                            try:
                                # Get measurements with timeout protection
                                measurements = controller.get_measurements()
                                
                                # Validate measurements
                                voltage = measurements.voltage if measurements.voltage is not None else None
                                current = measurements.current if measurements.current is not None else None
                                power = measurements.power if measurements.power is not None else None
                                
                                # Additional validation: P should be approximately V * I
                                # This helps catch data corruption issues
                                if voltage is not None and current is not None and power is not None:
                                    expected_power = voltage * current
                                    tolerance = abs(expected_power * 0.05)  # 5% tolerance
                                    if abs(power - expected_power) > max(tolerance, 0.1):
                                        # Power doesn't match, recalculate
                                        power = expected_power
                                        logger.warning(
                                            f"Data validation: Corrected power for {device_name} "
                                            f"(V={voltage:.2f}V, I={current:.3f}A, P_corrected={power:.2f}W)"
                                        )
                                
                                data_point[f'{device_name}_voltage'] = voltage
                                data_point[f'{device_name}_current'] = current
                                data_point[f'{device_name}_power'] = power
                                data_point[f'{device_name}_busy'] = False
                                
                                # Add device mode info if available
                                if hasattr(controller, 'current_mode'):
                                    data_point[f'{device_name}_mode'] = controller.current_mode
                                
                                # Debug output for successful measurements  
                                if voltage is not None or current is not None:
                                    mode_info = f" ({controller.current_mode})" if hasattr(controller, 'current_mode') and controller.current_mode else ""
                                    # Only print occasionally to avoid spam
                                    if int(time.time()) % 5 == 0:  # Every 5 seconds
                                        print(f"Monitoring {device_name}{mode_info}: V={voltage:.3f}V I={current:.3f}A" if voltage and current else f"Monitoring {device_name}{mode_info}: Getting measurements...")
                                        
                            except Exception as e:
                                print(f"Error reading from {device_name}: {e}")
                                data_point[f'{device_name}_voltage'] = None
                                data_point[f'{device_name}_current'] = None
                                data_point[f'{device_name}_power'] = None
                                data_point[f'{device_name}_busy'] = False
                
                # Queue data for processing
                self.data_queue.put(data_point)
                
                time.sleep(self.sample_interval)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(1)
                
    def get_new_data(self) -> List[Dict]:
        """Get new data points from queue"""
        new_data = []
        try:
            while True:
                data_point = self.data_queue.get_nowait()
                self.measurement_data.append(data_point)
                new_data.append(data_point)
                
                # Prevent memory leak: remove old data if limit exceeded
                if len(self.measurement_data) >= self.MAX_DATA_POINTS:
                    # Remove oldest 50% of data (FIFO)
                    remove_count = self.MAX_DATA_POINTS // 2
                    self.measurement_data = self.measurement_data[remove_count:]
                    logger.warning(
                        f"Measurement data buffer limit ({self.MAX_DATA_POINTS}) reached, "
                        f"removed {remove_count} oldest data points"
                    )
                
                # Call callbacks with new data
                for callback in self.callbacks:
                    try:
                        callback(data_point)
                    except Exception as e:
                        print(f"Callback error: {e}")
                        
        except queue.Empty:
            pass
            
        return new_data
        
    def clear_data(self):
        """Clear all measurement data"""
        self.measurement_data.clear()
        # Clear any remaining data in queue
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break
                
    def save_to_csv(self, filename: str) -> bool:
        """Save measurement data to CSV file"""
        if not self.measurement_data:
            return False
            
        try:
            # Determine all possible field names
            fieldnames = set(['timestamp'])
            for data_point in self.measurement_data:
                fieldnames.update(data_point.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for data_point in self.measurement_data:
                    writer.writerow(data_point)
                    
            return True
            
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return False
    
    def save_to_excel(self, filename: str) -> bool:
        """Save measurement data to Excel file"""
        try:
            if not self.measurement_data:
                return False
            
            # Lazy import
            try:
                import pandas as pd
                import openpyxl
            except ImportError as e:
                print(f"Error: Required library not installed. Install: pip install pandas openpyxl")
                print(f"Details: {e}")
                return False

            # Create DataFrame from data
            df = pd.DataFrame(self.measurement_data)
            
            # Save to Excel (simple format for speed)
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"Data saved to {filename}")
            return True
            
        except Exception as e:
            print(f"Error saving Excel data: {e}")
            return False
            
    def get_data_count(self) -> int:
        """Get number of stored data points"""
        return len(self.measurement_data)
        
    def get_latest_data(self, device_name: str) -> Optional[Dict]:
        """Get latest measurements for a specific device"""
        if not self.measurement_data:
            return None
            
        latest = self.measurement_data[-1]
        return {
            'voltage': latest.get(f'{device_name}_voltage'),
            'current': latest.get(f'{device_name}_current'),
            'power': latest.get(f'{device_name}_power'),
            'timestamp': latest.get('timestamp')
        }