#!/usr/bin/env python3
"""
Keithley Logger - Structured logging for Keithley operations
Based on patterns from auto_mode_profile.py reference script
"""
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class KeithleyLogger:
    """Structured logging for Keithley operations based on reference script"""
    
    def __init__(self):
        self.log: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.current_mode: Optional[str] = None
        
    def start_timer(self):
        """Start the timer for elapsed time tracking"""
        self.start_time = time.time()
        
    def elapsed(self) -> float:
        """Get elapsed time since timer start"""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time
    
    def log_segment(self, step: int, mode: str, set_current: float, 
                   measured_v: float, measured_i: float, elapsed: float, 
                   status: str):
        """
        Log a measurement segment - matches reference script format
        
        Args:
            step: Step number
            mode: Operation mode ('charge' or 'discharge')
            set_current: Set current value (A)
            measured_v: Measured voltage (V)
            measured_i: Measured current (A)
            elapsed: Elapsed time (s)
            status: Status ('OK', 'ERROR', etc.)
        """
        self.log.append({
            'step': step,
            'mode': mode,
            'set_current_a': set_current,
            'measured_voltage_v': measured_v,
            'measured_current_a': measured_i,
            'elapsed_time_s': elapsed,
            'status': status
        })
    
    def log_measurement(self, timestamp: str, voltage: Optional[float], 
                       current: Optional[float], mode: str = 'manual', 
                       status: str = 'OK'):
        """
        Log a general measurement
        
        Args:
            timestamp: Timestamp string
            voltage: Measured voltage (V)
            current: Measured current (A)
            mode: Operation mode
            status: Status string
        """
        self.log.append({
            'timestamp': timestamp,
            'mode': mode,
            'measured_voltage_v': voltage,
            'measured_current_a': current,
            'elapsed_time_s': self.elapsed(),
            'status': status
        })
    
    def log_error(self, step: int, mode: str, error_msg: str):
        """Log an error event"""
        self.log.append({
            'step': step,
            'mode': mode,
            'set_current_a': 'ERROR',
            'measured_voltage_v': 'ERROR',
            'measured_current_a': 'ERROR',
            'elapsed_time_s': self.elapsed(),
            'status': f'ERROR: {error_msg}'
        })
    
    def save_log_csv(self, filename: Optional[str] = None) -> str:
        """
        Save log to CSV file - matches reference script format
        
        Args:
            filename: Optional filename, if None generates timestamp-based name
            
        Returns:
            Path to saved file
        """
        if not self.log:
            raise ValueError("No log data to save")
            
        if filename is None:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'keithley_log_{ts}.csv'
        
        # Ensure logs directory exists
        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)
        filepath = log_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(self.log[0].keys()))
            writer.writeheader()
            for row in self.log:
                writer.writerow(row)
                
        return str(filepath)
    
    def clear_log(self):
        """Clear the log data"""
        self.log.clear()
        self.start_time = None
    
    def get_log_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the log"""
        if not self.log:
            return {'total_entries': 0}
            
        summary = {
            'total_entries': len(self.log),
            'modes': {},
            'errors': 0,
            'success': 0,
            'elapsed_time_s': self.elapsed() if self.start_time else 0
        }
        
        for entry in self.log:
            mode = entry.get('mode', 'unknown')
            summary['modes'][mode] = summary['modes'].get(mode, 0) + 1
            
            status = entry.get('status', '')
            if 'ERROR' in str(status).upper():
                summary['errors'] += 1
            elif status == 'OK':
                summary['success'] += 1
                
        return summary
    
    def export_for_analysis(self, filename: Optional[str] = None) -> str:
        """
        Export log data in format suitable for analysis
        
        Args:
            filename: Optional filename
            
        Returns:
            Path to exported file
        """
        if not self.log:
            raise ValueError("No log data to export")
            
        if filename is None:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'keithley_analysis_{ts}.csv'
        
        # Ensure analysis directory exists
        analysis_dir = Path('./analysis_data')
        analysis_dir.mkdir(exist_ok=True)
        filepath = analysis_dir / filename
        
        # Enhanced export with calculated fields
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['timestamp', 'step', 'mode', 'set_current_a', 
                         'measured_voltage_v', 'measured_current_a', 
                         'calculated_power_w', 'elapsed_time_s', 'status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in self.log:
                # Calculate power if voltage and current are available
                power = None
                try:
                    v = entry.get('measured_voltage_v')
                    i = entry.get('measured_current_a')
                    if v is not None and i is not None and v != 'ERROR' and i != 'ERROR':
                        power = float(v) * float(i)
                except (ValueError, TypeError):
                    power = None
                
                export_entry = {
                    'timestamp': entry.get('timestamp', datetime.now().isoformat()),
                    'step': entry.get('step', ''),
                    'mode': entry.get('mode', ''),
                    'set_current_a': entry.get('set_current_a', ''),
                    'measured_voltage_v': entry.get('measured_voltage_v', ''),
                    'measured_current_a': entry.get('measured_current_a', ''),
                    'calculated_power_w': power if power is not None else '',
                    'elapsed_time_s': entry.get('elapsed_time_s', ''),
                    'status': entry.get('status', '')
                }
                writer.writerow(export_entry)
                
        return str(filepath)
    
    def __len__(self) -> int:
        """Return number of log entries"""
        return len(self.log)
    
    def __str__(self) -> str:
        """String representation of logger status"""
        summary = self.get_log_summary()
        return f"KeithleyLogger: {summary['total_entries']} entries, {summary.get('errors', 0)} errors"