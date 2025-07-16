#!/usr/bin/env python3
"""
Professional Battery Model Generator for Keithley 2281S
Fully compliant with reference manual specifications
"""

import time
import csv
import pyvisa
import logging
from datetime import datetime
from pathlib import Path
import json
import sys

# Configuration
RESOURCE_ADDR = 'USB0::1510::8833::4587429::0::INSTR'
LOG_DIR = Path('./logs')
DATA_DIR = Path('./data')

# Test Parameters (Customize these based on battery specs)
CONFIG = {
    'discharge': {
        'voltage': 3.0,      # V-empty (discharge end voltage)
        'current_end': 0.4,  # End current for discharge (A)
    },
    'charge': {
        'v_full': 4.20,      # Full charge voltage (V)
        'i_limit': 1.00,     # Max charging current (A)
        'esr_interval': 30,  # ESR measurement interval (s)
    },
    'model': {
        'v_min': 2.5,        # Model voltage range minimum
        'v_max': 4.2,        # Model voltage range maximum
        'slot': 4,           # Internal memory slot (1-9)
    },
    'timeouts': {
        'discharge_max_hours': 4,
        'charge_max_hours': 8,
        'poll_interval': 30,  # Status check interval (s)
    }
}

class BatteryModelGenerator:
    """Professional battery model generator with full error handling"""
    
    def __init__(self, resource_addr=RESOURCE_ADDR):
        self.resource_addr = resource_addr
        self.inst = None
        self.rm = None
        self.start_time = None
        self.test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup directories
        LOG_DIR.mkdir(exist_ok=True)
        DATA_DIR.mkdir(exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging with both file and console output"""
        log_file = LOG_DIR / f"battery_test_{self.test_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def connect(self):
        """Establish connection to instrument with error handling"""
        try:
            self.rm = pyvisa.ResourceManager('@py')
            self.inst = self.rm.open_resource(self.resource_addr)
            self.inst.read_termination = '\n'
            self.inst.write_termination = '\n'
            self.inst.timeout = 5000
            
            # Verify connection
            idn = self.query('*IDN?')
            self.logger.info(f"Connected to: {idn}")
            
            # Initialize instrument
            self.write('*CLS')
            self.write('SYST:REM')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
            
    def write(self, cmd):
        """Write command with logging"""
        self.inst.write(cmd)
        self.logger.debug(f"[W] {cmd}")
        
    def query(self, cmd):
        """Query command with logging"""
        response = self.inst.query(cmd).strip()
        self.logger.debug(f"[Q] {cmd} => {response}")
        return response
        
    def wait_opc(self, timeout_ms=300000, note="Operation"):
        """Wait for operation complete with timeout"""
        old_timeout = self.inst.timeout
        self.inst.timeout = timeout_ms
        try:
            result = self.query('*OPC?')
            if result != '1':
                raise TimeoutError(f"{note} failed to complete")
        finally:
            self.inst.timeout = old_timeout
            
    def get_measurement_status(self):
        """Get detailed measurement status"""
        try:
            # Operation status
            cond = int(self.query(':STAT:OPER:INST:ISUM:COND?'))
            measuring = bool(cond & 0x10)
            
            # Current readings
            voltage = float(self.query(':BATT:VOLT?'))
            current = float(self.query(':BATT:CURR?'))
            
            # Output state
            output = self.query(':OUTP?') == '1'
            
            return {
                'measuring': measuring,
                'voltage': voltage,
                'current': current,
                'output': output,
                'status_code': cond
            }
        except Exception as e:
            self.logger.error(f"Failed to get status: {e}")
            return None
            
    def wait_measurement_complete(self, max_hours, poll_interval=30):
        """Wait for measurement with progress monitoring"""
        max_seconds = max_hours * 3600
        start_time = time.time()
        
        self.logger.info(f"Waiting for measurement (max {max_hours} hours)...")
        
        while True:
            status = self.get_measurement_status()
            if not status:
                raise Exception("Failed to get measurement status")
                
            # Log progress
            elapsed = time.time() - start_time
            self.logger.info(
                f"Progress: {elapsed/60:.1f} min | "
                f"V: {status['voltage']:.3f}V | "
                f"I: {status['current']:.3f}A | "
                f"Measuring: {status['measuring']}"
            )
            
            # Check if complete
            if not status['measuring']:
                self.logger.info(f"Measurement completed in {elapsed/60:.1f} minutes")
                return
                
            # Check timeout
            if elapsed > max_seconds:
                raise TimeoutError(f"Measurement exceeded {max_hours} hours")
                
            time.sleep(poll_interval)
            
    def discharge_battery(self):
        """Perform complete battery discharge"""
        self.logger.info("=== STARTING BATTERY DISCHARGE ===")
        
        # Clear buffers
        self.write(':BATT1:DATA:CLE')
        self.write(':TRACe:CLEar')
        
        # Configure discharge
        self.write(':BATT:TEST:MODE DIS')
        self.write(f':BATT:TEST:VOLT {CONFIG["discharge"]["voltage"]}')
        self.write(f':BATT:TEST:CURR:END {CONFIG["discharge"]["current_end"]}')
        
        # Start discharge
        self.write(':BATT:OUTP ON')
        
        # Wait for completion
        self.wait_measurement_complete(
            CONFIG['timeouts']['discharge_max_hours'],
            CONFIG['timeouts']['poll_interval']
        )
        
        # Turn off output
        self.write(':BATT:OUTP OFF')
        self.logger.info("=== DISCHARGE COMPLETED ===")
        
    def charge_and_characterize(self):
        """Perform charging with A-H and ESR measurement"""
        self.logger.info("=== STARTING CHARGE & CHARACTERIZATION ===")
        
        # Configure A-H measurement
        self.write(f':BATT:TEST:SENS:AH:VFUL {CONFIG["charge"]["v_full"]}')
        self.write(f':BATT:TEST:SENS:AH:ILIM {CONFIG["charge"]["i_limit"]}')
        self.write(f':BATT:TEST:SENS:AH:ESRI S{CONFIG["charge"]["esr_interval"]}')
        
        # Configure buffer
        self.write(':TRACe:CLEar:AUTO ON')
        
        # Start measurement
        self.write(':BATT:OUTP ON')
        self.write(':BATT:TEST:SENS:AH:EXEC STAR')
        
        # Wait for completion
        self.wait_measurement_complete(
            CONFIG['timeouts']['charge_max_hours'],
            CONFIG['timeouts']['poll_interval']
        )
        
        self.logger.info("=== CHARGE & CHARACTERIZATION COMPLETED ===")
        
    def generate_and_save_model(self):
        """Generate battery model and save to internal memory"""
        self.logger.info("=== GENERATING BATTERY MODEL ===")
        
        # Set model range
        v_min = CONFIG['model']['v_min']
        v_max = CONFIG['model']['v_max']
        self.write(f':BATT:TEST:SENS:AH:GMOD:RANG {v_min},{v_max}')
        
        # Save to internal memory
        slot = CONFIG['model']['slot']
        self.write(f':BATT:TEST:SENS:AH:GMOD:SAVE:INT {slot}')
        self.wait_opc(timeout_ms=60000, note="Model generation")
        
        # Verify save
        slots = self.query(':BATT:TEST:SENS:AH:GMOD:CAT?')
        self.logger.info(f"Model saved to slot {slot}. Available slots: {slots}")
        
        return slot
        
    def export_model_to_csv(self, slot):
        """Export battery model to CSV file"""
        self.logger.info("=== EXPORTING MODEL TO CSV ===")
        
        # Recall model
        self.write(f':BATT:MOD:RCL {slot}')
        
        # Get buffer points
        points = int(self.query(':TRACe:POINts:ACTual?'))
        self.logger.info(f"Model contains {points} data points")
        
        # Prepare CSV file
        csv_file = DATA_DIR / f'battery_model_{slot}_{self.test_id}.csv'
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['SOC (%)', 'Voc (V)', 'ESR (Ω)', 'Timestamp'])
            
            # Read model data
            for i in range(min(points, 101)):  # Models have max 101 points
                try:
                    resp = self.query(f':BATT:MOD{slot}:ROW{i}?')
                    if resp:
                        voc, esr = map(float, resp.split(','))
                        soc = i * 100.0 / 100  # 0-100%
                        timestamp = datetime.now().isoformat()
                        writer.writerow([f'{soc:.1f}', f'{voc:.4f}', f'{esr:.4f}', timestamp])
                except Exception as e:
                    self.logger.error(f"Error reading row {i}: {e}")
                    
        self.logger.info(f"Model exported to: {csv_file}")
        return csv_file
        
    def export_measurement_data(self):
        """Export raw measurement data from buffer"""
        self.logger.info("=== EXPORTING MEASUREMENT DATA ===")
        
        try:
            # Get buffer size
            points = int(self.query(':TRACe:POINts:ACTual?'))
            if points == 0:
                self.logger.warning("No data in buffer")
                return None
                
            csv_file = DATA_DIR / f'battery_measurements_{self.test_id}.csv'
            
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Time (s)', 'Voltage (V)', 'Current (A)', 'Capacity (Ah)', 'ESR (Ω)'])
                
                # Read data in chunks (100 points at a time)
                chunk_size = 100
                for start in range(1, points + 1, chunk_size):
                    end = min(start + chunk_size - 1, points)
                    
                    # Query data
                    data = self.query(
                        f':BATT1:DATA:DATA:SEL? {start},{end},"VOLT,CURR,AH,RES,REL"'
                    )
                    
                    if data:
                        # Parse response
                        rows = [r.split(',') for r in data.split(';') if r]
                        for row in rows:
                            if len(row) >= 5:
                                writer.writerow(row)
                                
            self.logger.info(f"Measurement data exported to: {csv_file}")
            return csv_file
            
        except Exception as e:
            self.logger.error(f"Failed to export measurement data: {e}")
            return None
            
    def save_test_summary(self, model_slot, model_file, data_file):
        """Save test summary in JSON format"""
        summary = {
            'test_id': self.test_id,
            'timestamp': datetime.now().isoformat(),
            'configuration': CONFIG,
            'results': {
                'model_slot': model_slot,
                'model_file': str(model_file) if model_file else None,
                'data_file': str(data_file) if data_file else None,
            },
            'instrument': {
                'address': self.resource_addr,
                'identity': self.query('*IDN?') if self.inst else 'Unknown'
            }
        }
        
        summary_file = DATA_DIR / f'test_summary_{self.test_id}.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        self.logger.info(f"Test summary saved to: {summary_file}")
        
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.inst:
                self.write(':BATT:OUTP OFF')
                self.write('SYST:LOC')
                self.inst.close()
            if self.rm:
                self.rm.close()
            self.logger.info("Cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
            
    def run_complete_test(self):
        """Run complete battery characterization test"""
        try:
            # Connect to instrument
            if not self.connect():
                raise Exception("Failed to connect to instrument")
                
            # Run test sequence
            self.discharge_battery()
            self.charge_and_characterize()
            
            # Generate and save model
            model_slot = self.generate_and_save_model()
            
            # Export data
            model_file = self.export_model_to_csv(model_slot)
            data_file = self.export_measurement_data()
            
            # Save summary
            self.save_test_summary(model_slot, model_file, data_file)
            
            self.logger.info("=== TEST COMPLETED SUCCESSFULLY ===")
            
        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            raise
            
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    print("Battery Model Generator for Keithley 2281S")
    print("==========================================")
    
    # Create generator instance
    generator = BatteryModelGenerator()
    
    # Run test
    try:
        generator.run_complete_test()
        print("\nTest completed successfully!")
        print(f"Check the 'data' directory for results")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        generator.cleanup()
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
