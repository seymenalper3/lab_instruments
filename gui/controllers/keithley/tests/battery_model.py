#!/usr/bin/env python3
"""
Keithley Battery Model Test - Extract from main controller
Complete battery model generation with discharge, charge, and characterization
"""
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Dict


class KeithleyBatteryModel:
    """
    Keithley Battery Model Generator
    
    Runs complete battery model generation test following Keithley 2281S procedure.
    Includes discharge, charge with A-H measurement, model generation, and CSV export.
    """
    
    def __init__(self, controller):
        """
        Initialize battery model test runner
        
        Args:
            controller: Parent KeithleyController instance
        """
        self.controller = controller
    
    def run(self,
            discharge_voltage: float = 3.0,
            discharge_current_end: float = 0.4,
            charge_vfull: float = 4.20,
            charge_ilimit: float = 1.00,
            esr_interval: int = 30,
            model_slot: int = 4,
            v_min: float = 2.5,
            v_max: float = 4.2,
            export_csv: bool = True) -> Dict:
        """
        Run complete battery model generation test

        This function follows the procedure from Keithley 2281S manual.
        It will wait indefinitely until discharge and charge phases complete.
        Total duration can be several hours depending on battery capacity.

        Args:
            discharge_voltage: End voltage for discharge (V)
            discharge_current_end: End current for discharge (A)
            charge_vfull: Full charge voltage (V)
            charge_ilimit: Charge current limit (A)
            esr_interval: ESR measurement interval (s)
            model_slot: Internal memory slot (1-9)
            v_min: Model voltage range minimum
            v_max: Model voltage range maximum
            export_csv: Whether to export model to CSV

        Returns:
            Dictionary with test results and file paths

        Note:
            No timeout limits - test will run until battery reaches end conditions.
            Progress is displayed every 30 seconds.
        """
        # Pre-flight checks
        if not self.controller.connected:
            raise Exception("Device not connected")
        
        if self.controller.busy:
            raise Exception("Device is busy with another operation")
        
        # Validate parameters
        self._validate_parameters(discharge_voltage, discharge_current_end,
                                 charge_vfull, charge_ilimit, model_slot, esr_interval)
        
        # Set device as busy
        self.controller.set_busy(True)
        
        test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            'test_id': test_id,
            'model_slot': model_slot,
            'start_time': datetime.now().isoformat(),
            'model_file': None,
            'data_file': None,
            'success': False
        }
        
        try:
            print(f"Starting battery model generation test {test_id}")
            
            # 1) Initialize
            self._initialize_device()
            
            # 2) Discharge phase
            self._discharge_phase(discharge_voltage, discharge_current_end)
            
            # 3) Charge and characterization
            self._charge_and_characterize(charge_vfull, charge_ilimit, esr_interval)
            
            # 4) Generate and save model
            self._generate_and_save_model(model_slot, v_min, v_max)
            
            # 5) Export model to CSV
            if export_csv:
                model_file = self._export_model_csv(model_slot, test_id)
                results['model_file'] = model_file
            
            # 6) Export measurement data
            data_file = self._export_measurement_data(test_id)
            if data_file:
                results['data_file'] = data_file
            
            results['success'] = True
            results['end_time'] = datetime.now().isoformat()
            print("=== BATTERY MODEL TEST COMPLETED SUCCESSFULLY ===")
            
            return results
            
        except Exception as e:
            print(f"Battery model test failed: {e}")
            results['error'] = str(e)
            results['end_time'] = datetime.now().isoformat()
            raise
            
        finally:
            # Cleanup
            try:
                self.controller.send_command(':BATT:OUTP OFF')
            except:
                pass
            self.controller.set_busy(False)
    
    def _validate_parameters(self, discharge_voltage, discharge_current_end,
                            charge_vfull, charge_ilimit, model_slot, esr_interval):
        """Validate test parameters"""
        if discharge_voltage < 2.0 or discharge_voltage > 4.5:
            raise ValueError("Discharge voltage must be between 2.0 and 4.5V")
        if discharge_current_end < 0.1 or discharge_current_end > 2.0:
            raise ValueError("Discharge end current must be between 0.1 and 2.0A")
        if charge_vfull < 3.0 or charge_vfull > 4.5:
            raise ValueError("Charge voltage must be between 3.0 and 4.5V")
        if charge_ilimit < 0.1 or charge_ilimit > self.controller.device_spec.max_current:
            raise ValueError(f"Charge current must be between 0.1 and {self.controller.device_spec.max_current}A")
        if model_slot < 1 or model_slot > 9:
            raise ValueError("Model slot must be between 1 and 9")
        if esr_interval < 1 or esr_interval > 300:
            raise ValueError("ESR interval must be between 1 and 300 seconds")
    
    def _initialize_device(self):
        """Clear and initialize device"""
        print("Clearing buffers and initializing...")
        self.controller.send_command('*CLS')
        self.controller.send_command(':BATT1:DATA:CLE')
        self.controller.send_command(':BATT:DATA:CLE')
        self.controller.send_command(':TRACe:CLEar')
    
    def _discharge_phase(self, discharge_voltage, discharge_current_end):
        """Execute discharge phase"""
        print("=== STARTING BATTERY DISCHARGE ===")
        print(f"Discharge to {discharge_voltage}V, end current {discharge_current_end}A")
        
        self.controller.send_command(':BATT:TEST:MODE DIS')
        self.controller.send_command(f':BATT:TEST:VOLT {discharge_voltage}')
        self.controller.send_command(f':BATT:TEST:CURR:END {discharge_current_end}')
        self.controller.send_command(':BATT:OUTP ON')
        
        # Wait for discharge to complete (no timeout)
        start_time = time.time()
        
        while True:
            try:
                cond = int(self.controller.query_command(':STAT:OPER:INST:ISUM:COND?'))
                measuring = bool(cond & 0x10)
                
                # Progress update
                try:
                    voltage = float(self.controller.query_command(':BATT:VOLT?'))
                    current = float(self.controller.query_command(':BATT:CURR?'))
                    elapsed = time.time() - start_time
                    print(f"Discharge progress: {elapsed/60:.1f} min | V: {voltage:.3f}V | I: {current:.3f}A")
                except:
                    pass
                
                if not measuring:
                    print(f"Discharge completed in {(time.time() - start_time)/60:.1f} minutes")
                    break
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Status check error: {e}")
                time.sleep(5)
        
        self.controller.send_command(':BATT:OUTP OFF')
        print("=== DISCHARGE COMPLETED ===")
    
    def _charge_and_characterize(self, charge_vfull, charge_ilimit, esr_interval):
        """Execute charge and characterization phase"""
        print("=== STARTING CHARGE & CHARACTERIZATION ===")
        print(f"Charge to {charge_vfull}V, current limit {charge_ilimit}A, ESR interval {esr_interval}s")
        
        self.controller.send_command(f':BATT:TEST:SENS:AH:VFUL {charge_vfull}')
        self.controller.send_command(f':BATT:TEST:SENS:AH:ILIM {charge_ilimit}')
        self.controller.send_command(f':BATT:TEST:SENS:AH:ESRI S{esr_interval}')
        self.controller.send_command(':TRACe:CLEar:AUTO ON')
        self.controller.send_command(':TRACe:FEED:CONT ALW')
        
        # Start A-H measurement
        self.controller.send_command(':BATT:OUTP ON')
        self.controller.send_command(':BATT:TEST:SENS:AH:EXEC STAR')
        
        # Wait for charge to complete (no timeout)
        start_time = time.time()
        
        while True:
            try:
                cond = int(self.controller.query_command(':STAT:OPER:INST:ISUM:COND?'))
                measuring = bool(cond & 0x10)
                
                # Progress update
                try:
                    voltage = float(self.controller.query_command(':BATT:VOLT?'))
                    current = float(self.controller.query_command(':BATT:CURR?'))
                    elapsed = time.time() - start_time
                    print(f"Charge progress: {elapsed/60:.1f} min | V: {voltage:.3f}V | I: {current:.3f}A")
                except:
                    pass
                
                if not measuring:
                    print(f"Charge completed in {(time.time() - start_time)/60:.1f} minutes")
                    break
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Status check error: {e}")
                time.sleep(5)
        
        print("=== CHARGE & CHARACTERIZATION COMPLETED ===")
    
    def _generate_and_save_model(self, model_slot, v_min, v_max):
        """Generate and save battery model"""
        print("=== GENERATING BATTERY MODEL ===")
        self.controller.send_command(f':BATT:TEST:SENS:AH:GMOD:RANG {v_min},{v_max}')
        self.controller.send_command(f':BATT:TEST:SENS:AH:GMOD:SAVE:INT {model_slot}')
        
        # Wait for model generation
        time.sleep(2)
        self.controller.query_command('*OPC?')  # Wait for operation complete
        
        # Verify save
        slots = self.controller.query_command(':BATT:TEST:SENS:AH:GMOD:CAT?')
        print(f"Model saved to slot {model_slot}. Available slots: {slots}")
    
    def _export_model_csv(self, model_slot, test_id):
        """Export battery model to CSV"""
        print("=== EXPORTING MODEL TO CSV ===")
        
        # Recall model
        self.controller.send_command(f':BATT:MOD:RCL {model_slot}')
        time.sleep(1)
        
        # Prepare CSV file
        data_dir = Path('./battery_models')
        data_dir.mkdir(exist_ok=True)
        csv_file = data_dir / f'battery_model_slot{model_slot}_{test_id}.csv'
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['SOC (%)', 'Voc (V)', 'ESR (Ω)', 'Timestamp'])
            
            # Read model data (101 points for complete model)
            rows_written = 0
            for i in range(101):
                try:
                    resp = self.controller.query_command(f':BATT:MOD{model_slot}:ROW{i}?')
                    if resp and ',' in resp:
                        parts = resp.strip().split(',')
                        if len(parts) >= 2:
                            voc = float(parts[0])
                            esr = float(parts[1])
                            soc = i  # 0-100%
                            timestamp = datetime.now().isoformat()
                            writer.writerow([f'{soc}', f'{voc:.4f}', f'{esr:.4f}', timestamp])
                            rows_written += 1
                except Exception as e:
                    print(f"Error reading row {i}: {e}")
        
        print(f"Model exported to: {csv_file} ({rows_written} rows)")
        return str(csv_file)
    
    def _export_measurement_data(self, test_id):
        """Export measurement data to CSV"""
        try:
            print("=== EXPORTING MEASUREMENT DATA ===")
            points_str = self.controller.query_command(':TRACe:POINts:ACTual?')
            points = int(points_str) if points_str else 0
            
            if points > 0:
                print(f"Buffer contains {points} data points")
                data_dir = Path('./battery_models')
                data_dir.mkdir(exist_ok=True)
                data_file = data_dir / f'battery_measurements_{test_id}.csv'
                
                with open(data_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Time (s)', 'Voltage (V)', 'Current (A)', 'Capacity (Ah)', 'ESR (Ω)'])
                    
                    # Read data in chunks
                    chunk_size = 100
                    total_rows = 0
                    
                    for start in range(1, points + 1, chunk_size):
                        end = min(start + chunk_size - 1, points)
                        
                        try:
                            data = self.controller.query_command(
                                f':BATT1:DATA:DATA:SEL? {start},{end},"VOLT,CURR,AH,RES,REL"'
                            )
                            
                            if data:
                                rows = [r.split(',') for r in data.split(';') if r]
                                for row in rows:
                                    if len(row) >= 5:
                                        writer.writerow(row)
                                        total_rows += 1
                        except Exception as e:
                            print(f"Failed to read chunk {start}-{end}: {e}")
                
                print(f"Measurement data exported to: {data_file} ({total_rows} rows)")
                return str(data_file)
                
        except Exception as e:
            print(f"Failed to export measurement data: {e}")
            return None

