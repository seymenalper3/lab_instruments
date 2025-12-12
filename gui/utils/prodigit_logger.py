#!/usr/bin/env python3
"""
Structured logging for Prodigit CC profile execution.
Creates per-second CSV entries with setpoint and measured values.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _format_number(value: Optional[float], precision: int = 3) -> Optional[str]:
    """Return a formatted string for numeric values or None."""
    if value is None:
        return None
    return f"{value:.{precision}f}"


@dataclass
class ProdigitProfileLogger:
    """Helper for logging Prodigit CC runs to ./logs."""

    rows: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    filename: Optional[str] = None

    def start(self, csv_path: Path, sample_period: float, segment_count: int, total_duration: float):
        """Initialize a logging session."""
        self.metadata = {
            'csv_path': str(csv_path),
            'sample_period_s': float(sample_period),
            'segment_count': int(segment_count),
            'total_duration_s': float(total_duration),
            'started_at': datetime.now().isoformat()
        }
        self.rows.clear()
        self.filename = f"prodigit_cc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    def log_sample(
        self,
        *,
        segment_index: int,
        set_current: float,
        measured_voltage: Optional[float],
        measured_current: Optional[float],
        measured_power: Optional[float],
        elapsed_segment_s: float,
        elapsed_total_s: float,
        status: str
    ):
        """Append a single measurement/sample entry."""
        if not self.metadata:
            raise RuntimeError("Logger must be started before logging samples.")

        self.rows.append({
            'timestamp': datetime.now().isoformat(),
            'segment_index': segment_index,
            'set_current_a': _format_number(set_current),
            'measured_voltage_v': _format_number(measured_voltage),
            'measured_current_a': _format_number(measured_current, precision=4),
            'measured_power_w': _format_number(measured_power),
            'elapsed_segment_s': _format_number(elapsed_segment_s, precision=2),
            'elapsed_total_s': _format_number(elapsed_total_s, precision=2),
            'status': status,
            'profile_path': self.metadata.get('csv_path'),
            'sample_period_s': _format_number(self.metadata.get('sample_period_s'), precision=2),
        })

    def finalize(self, outcome: str, error_message: Optional[str] = None, output_format: str = 'csv') -> list:
        """
        Persist the log to disk in selected format(s).
        
        Args:
            outcome: Status of the profile execution
            error_message: Optional error message
            output_format: 'csv', 'xlsx', or 'both'
            
        Returns:
            List of saved file paths
        """
        if not self.rows:
            raise ValueError("No samples recorded for Prodigit CC profile.")

        summary_row = {
            'timestamp': datetime.now().isoformat(),
            'segment_index': 'SUMMARY',
            'set_current_a': str(self.metadata.get('segment_count')),
            'measured_voltage_v': None,
            'measured_current_a': None,
            'measured_power_w': None,
            'elapsed_segment_s': _format_number(self.metadata.get('total_duration_s'), precision=2),
            'elapsed_total_s': _format_number(self.metadata.get('total_duration_s'), precision=2),
            'status': outcome,
            'profile_path': self.metadata.get('csv_path'),
            'sample_period_s': _format_number(self.metadata.get('sample_period_s'), precision=2),
        }

        if error_message:
            summary_row['measured_voltage_v'] = error_message

        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)
        base_filename = self.filename or f"prodigit_cc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Remove extension if present
        base_filename = Path(base_filename).stem

        fieldnames = [
            'timestamp',
            'segment_index',
            'set_current_a',
            'measured_voltage_v',
            'measured_current_a',
            'measured_power_w',
            'elapsed_segment_s',
            'elapsed_total_s',
            'status',
            'profile_path',
            'sample_period_s'
        ]
        
        saved_files = []
        
        # Save CSV
        if output_format in ['csv', 'both']:
            csv_filepath = log_dir / f"{base_filename}.csv"
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in self.rows:
                    writer.writerow(row)
                writer.writerow(summary_row)
            saved_files.append(str(csv_filepath))
            print(f"CSV saved: {csv_filepath}")
        
        # Save Excel
        if output_format in ['xlsx', 'both']:
            try:
                import pandas as pd
                import openpyxl
                
                xlsx_filepath = log_dir / f"{base_filename}.xlsx"
                
                # Convert to DataFrame
                df = pd.DataFrame(self.rows + [summary_row])
                df.to_excel(xlsx_filepath, index=False, engine='openpyxl')
                
                saved_files.append(str(xlsx_filepath))
                print(f"Excel saved: {xlsx_filepath}")
            except Exception as e:
                print(f"Excel save failed: {e}")
                if output_format == 'xlsx':  # Only xlsx requested but failed
                    raise

        return saved_files

