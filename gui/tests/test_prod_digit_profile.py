#!/usr/bin/env python3
"""
Tests and helper CLI for Prodigit CSV profile execution.
"""
import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.prodigit_controller import ProdigitController
from models.device_config import DEVICE_SPECS, DeviceType


class DummyInterface:
    """Minimal interface stub for testing without hardware."""

    def __init__(self):
        self.connected = True
        self.commands = []

    def connect(self):
        self.connected = True

    def disconnect(self):
        self.connected = False

    def is_connected(self):
        return self.connected

    def write(self, command: str):
        self.commands.append(command)

    def query(self, command: str):
        self.commands.append(command)
        defaults = DEVICE_SPECS[DeviceType.PRODIGIT_34205A].default_commands
        if command == defaults['query_mode']:
            return "CC"
        if command == defaults['query_load']:
            return "STAT:LOAD ON"
        if command == defaults['query_error']:
            return "0,No error"
        return "0"


class MockProdigitController(ProdigitController):
    """Controller override that feeds deterministic measurements."""

    def __init__(self):
        super().__init__(DummyInterface())
        self.connected = True
        self._sleep_fn = lambda _: None  # Skip real sleeping for fast tests

    def measure_voltage(self):
        return 48.0

    def measure_current(self):
        return self._last_set_current

    def measure_power(self):
        return self._last_set_current * 48.0


class ProdigitProfileTests(unittest.TestCase):
    """Validate profile parsing and execution logic."""

    def _write_csv(self, rows):
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.writer(tmp)
        writer.writerow(['time_s', 'current_a'])
        writer.writerows(rows)
        tmp.close()
        return tmp.name

    def test_load_current_profile_applies_guardrails(self):
        controller = ProdigitController(DummyInterface())
        csv_path = self._write_csv([
            (0, 5),
            (10, 8),
            (20, 10)
        ])
        df = controller.load_current_profile(csv_path)
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 3)
        self.assertTrue((df['duration_s'] >= controller.PROFILE_MIN_DWELL_S).all())
        summary = controller.get_cached_profile_summary()
        self.assertEqual(summary['segments'], 3)
        Path(csv_path).unlink(missing_ok=True)

    def test_run_cc_profile_generates_log(self):
        controller = MockProdigitController()
        csv_path = self._write_csv([
            (0, 2.5),
            (2, 3.0)
        ])

        log_path = controller.run_cc_profile(csv_path, sample_period=0.5)
        self.assertTrue(Path(log_path).exists())
        self.assertFalse(controller.is_busy())

        # Clean up artifacts
        Path(csv_path).unlink(missing_ok=True)
        Path(log_path).unlink(missing_ok=True)

    def test_abort_mechanism(self):
        """Test that abort mechanism works correctly."""
        import time

        # Use a real sleep function for this test to ensure timing works
        controller = MockProdigitController()
        controller._sleep_fn = time.sleep  # Override to use real sleep

        csv_path = self._write_csv([
            (0, 2.0),
            (3, 3.0),
            (6, 4.0)
        ])

        # Start profile in a separate thread
        import threading
        error_occurred = []
        log_files = []

        def worker():
            try:
                log_path = controller.run_cc_profile(csv_path, sample_period=1.0)
                log_files.append(log_path)
            except InterruptedError as e:
                error_occurred.append(str(e))

        thread = threading.Thread(target=worker)
        thread.start()

        # Wait for first sample to be logged, then request abort
        time.sleep(1.5)  # Enough time for at least one sample
        controller.request_profile_abort()
        thread.join(timeout=5.0)

        # Verify abort was handled
        self.assertTrue(len(error_occurred) > 0, "Expected InterruptedError to be raised")
        self.assertIn("aborted", error_occurred[0].lower())
        self.assertFalse(controller.is_busy())

        # Clean up
        Path(csv_path).unlink(missing_ok=True)
        for log_file in log_files:
            Path(log_file).unlink(missing_ok=True)

    def test_file_not_found(self):
        """Test error handling when CSV file doesn't exist."""
        controller = ProdigitController(DummyInterface())
        df = controller.load_current_profile("nonexistent_file.csv")
        self.assertIsNone(df)
        self.assertIsNone(controller.get_cached_profile_summary())

    def test_invalid_csv_format(self):
        """Test error handling for invalid CSV content."""
        controller = ProdigitController(DummyInterface())

        # Create CSV with wrong columns
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        tmp.write("wrong,columns\n1,2\n3,4\n")
        tmp.close()

        df = controller.load_current_profile(tmp.name)
        self.assertIsNone(df)

        Path(tmp.name).unlink(missing_ok=True)

    def test_negative_current_rejected(self):
        """Test that negative currents are rejected."""
        controller = ProdigitController(DummyInterface())
        csv_path = self._write_csv([
            (0, 5.0),
            (10, -2.0),  # Negative current
            (20, 3.0)
        ])

        with self.assertRaises(ValueError) as context:
            controller.load_current_profile(csv_path)

        self.assertIn("negative", str(context.exception).lower())
        Path(csv_path).unlink(missing_ok=True)

    def test_exceeds_duration_guardrail(self):
        """Test that profiles exceeding max duration are rejected."""
        controller = ProdigitController(DummyInterface())
        csv_path = self._write_csv([
            (0, 5.0),
            (3700, 3.0),  # Exceeds 3600s guardrail
        ])

        with self.assertRaises(ValueError) as context:
            controller.load_current_profile(csv_path)

        self.assertIn("duration", str(context.exception).lower())
        Path(csv_path).unlink(missing_ok=True)

    def test_exceeds_current_guardrail(self):
        """Test that currents exceeding safe limit are rejected."""
        controller = ProdigitController(DummyInterface())
        csv_path = self._write_csv([
            (0, 5.0),
            (10, 150.0),  # Exceeds 120A guardrail
        ])

        with self.assertRaises(ValueError) as context:
            controller.load_current_profile(csv_path)

        self.assertIn("current", str(context.exception).lower())
        self.assertIn("guardrail", str(context.exception).lower())
        Path(csv_path).unlink(missing_ok=True)

    def test_empty_profile(self):
        """Test error handling for empty profiles."""
        controller = ProdigitController(DummyInterface())

        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        tmp.write("time_s,current_a\n")  # Headers only
        tmp.close()

        df = controller.load_current_profile(tmp.name)
        self.assertIsNone(df)

        Path(tmp.name).unlink(missing_ok=True)

    def test_single_row_profile(self):
        """Test that single-row profiles are handled correctly."""
        controller = ProdigitController(DummyInterface())
        csv_path = self._write_csv([
            (0, 5.0)
        ])

        df = controller.load_current_profile(csv_path)
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 1)
        # Duration should be filled with fallback
        self.assertGreaterEqual(df['duration_s'].iloc[0], controller.PROFILE_MIN_DWELL_S)

        Path(csv_path).unlink(missing_ok=True)

    def test_cache_invalidation(self):
        """Test that cache is properly invalidated."""
        controller = MockProdigitController()

        # Load first profile
        csv_path1 = self._write_csv([
            (0, 5.0),
            (10, 8.0)
        ])
        df1 = controller.load_current_profile(csv_path1)
        summary1 = controller.get_cached_profile_summary()
        self.assertEqual(summary1['segments'], 2)

        # Load second profile - cache should be invalidated
        csv_path2 = self._write_csv([
            (0, 3.0),
            (5, 4.0),
            (10, 6.0)
        ])
        df2 = controller.load_current_profile(csv_path2)
        summary2 = controller.get_cached_profile_summary()
        self.assertEqual(summary2['segments'], 3)

        # Clean up
        Path(csv_path1).unlink(missing_ok=True)
        Path(csv_path2).unlink(missing_ok=True)

    def test_cache_path_validation(self):
        """Test that run_cc_profile validates cached path."""
        controller = MockProdigitController()

        # Load profile A
        csv_path_a = self._write_csv([
            (0, 5.0),
            (5, 8.0)
        ])
        controller.load_current_profile(csv_path_a)

        # Try to run profile B without loading it first
        csv_path_b = self._write_csv([
            (0, 3.0),
            (3, 4.0)
        ])

        # Should reload profile B automatically
        log_path = controller.run_cc_profile(csv_path_b, sample_period=0.5)
        self.assertTrue(Path(log_path).exists())

        # Verify summary matches profile B
        summary = controller.get_cached_profile_summary()
        self.assertEqual(summary['segments'], 2)

        # Clean up
        Path(csv_path_a).unlink(missing_ok=True)
        Path(csv_path_b).unlink(missing_ok=True)
        Path(log_path).unlink(missing_ok=True)


def simulate_profile(csv_path: str, sample_period: float = 1.0):
    """Helper CLI to simulate a Prodigit profile run with the mock controller."""
    controller = MockProdigitController()
    log_path = controller.run_cc_profile(csv_path, sample_period=sample_period)
    print(f"Simulation complete. Log written to {log_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Simulate a Prodigit CC profile without hardware.")
    parser.add_argument("csv", help="Path to CSV file with time_s/current_a columns.")
    parser.add_argument("--sample-period", type=float, default=1.0, help="Sampling period in seconds.")
    args = parser.parse_args()

    simulate_profile(args.csv, sample_period=args.sample_period)

