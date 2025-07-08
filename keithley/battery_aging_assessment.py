#!/usr/bin/env python3
"""
Keithley 2281S Battery Aging Assessment Tool
Measures battery health parameters before and after current profile tests
"""

import time
import csv
import pyvisa
import logging
import json
from datetime import datetime
from pathlib import Path
import sys
import warnings

# Suppress PyVISA warnings
warnings.filterwarnings("ignore")
logging.getLogger('pyvisa').setLevel(logging.CRITICAL)
logging.getLogger('pyvisa_py').setLevel(logging.CRITICAL)

# Configuration
RESOURCE_ADDR = 'USB0::1510::8833::4587429::0::INSTR'
RESULTS_DIR = Path('./aging_results')

class BatteryAgingAssessment:
    """Battery aging assessment using multiple health indicators"""
    
    def __init__(self, resource_addr=RESOURCE_ADDR):
        self.resource_addr = resource_addr
        self.inst = None
        self.rm = None
        self.test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup directories
        RESULTS_DIR.mkdir(exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging"""
        log_file = RESULTS_DIR / f"aging_assessment_{self.test_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def connect(self):
        """Connect to Keithley 2281S"""
        try:
            try:
                self.rm = pyvisa.ResourceManager()
            except:
                self.rm = pyvisa.ResourceManager('@py')
                
            self.inst = self.rm.open_resource(self.resource_addr)
            self.inst.read_termination = '\n'
            self.inst.write_termination = '\n'
            self.inst.timeout = 10000  # 10 second timeout for measurements
            
            # Clear any errors
            self.inst.write('*CLS')
            time.sleep(0.5)
            
            # Get device info
            idn = self.inst.query('*IDN?').strip()
            self.logger.info(f"Connected to: {idn}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def measure_baseline_health(self):
        """Comprehensive battery health measurement"""
        self.logger.info("\n" + "="*60)
        self.logger.info("BATARYA SAĞLIK ÖLÇÜMLERİ BAŞLIYOR")
        self.logger.info("="*60)
        
        measurements = {
            'timestamp': datetime.now().isoformat(),
            'test_id': self.test_id
        }
        
        try:
            # 1. Güvenli başlangıç - tüm çıkışları kapat
            self.logger.info("Cihaz hazırlanıyor...")
            self.inst.write(':OUTP OFF')
            self.inst.write(':BATT:OUTP OFF')
            time.sleep(2)
            
            # 2. Battery test moduna geç
            self.inst.write('*CLS')
            self.inst.write('SYST:REM')
            self.inst.write(':FUNC TEST')
            time.sleep(1)
            
            # 3. ESR ve Voc ölçümü (EN ÖNEMLİ)
            self.logger.info("\n1. ESR ve Voc ölçümü yapılıyor...")
            self.inst.write(':BATT:TEST:MODE DIS')
            self.inst.write(':BATT:TEST:SENS:EVOC:DELA 1.0')  # 1 saniye stabilization
            
            time.sleep(2)
            result = self.inst.query(':BATT:TEST:MEAS:EVOC?').strip()
            
            if result and ',' in result:
                values = result.split(',')
                measurements['voc'] = float(values[0])  # Open Circuit Voltage
                measurements['esr'] = float(values[1])  # Internal Resistance
                
                self.logger.info(f"✓ Voc (Açık Devre Voltajı): {measurements['voc']:.4f} V")
                self.logger.info(f"✓ ESR (İç Direnç): {measurements['esr']:.4f} Ω")
            else:
                self.logger.warning(f"EVOC ölçümü başarısız: {result}")
                measurements['voc'] = None
                measurements['esr'] = None
            
            # 4. Pulse test - Voltage drop analysis
            self.logger.info("\n2. Pulse test yapılıyor...")
            
            # Düşük akım pulse (100mA)
            self.inst.write(':BATT:TEST:MODE DIS')
            self.inst.write(':BATT:TEST:CURR 0.1')  # 100mA test
            self.inst.write(':BATT:OUTP ON')
            
            time.sleep(3)  # 3 saniye pulse
            v_loaded_low = float(self.inst.query(':MEAS:VOLT?'))
            
            self.inst.write(':BATT:OUTP OFF')
            time.sleep(2)
            
            # Recovery voltage
            v_recovery_low = float(self.inst.query(':MEAS:VOLT?'))
            
            # Yüksek akım pulse (500mA)
            self.inst.write(':BATT:TEST:CURR 0.5')  # 500mA test
            self.inst.write(':BATT:OUTP ON')
            
            time.sleep(3)  # 3 saniye pulse
            v_loaded_high = float(self.inst.query(':MEAS:VOLT?'))
            
            self.inst.write(':BATT:OUTP OFF')
            time.sleep(2)
            
            # Recovery voltage
            v_recovery_high = float(self.inst.query(':MEAS:VOLT?'))
            
            # Pulse test sonuçları
            measurements.update({
                'voltage_loaded_100mA': v_loaded_low,
                'voltage_drop_100mA': measurements.get('voc', 0) - v_loaded_low,
                'voltage_recovery_100mA': v_recovery_low,
                'voltage_loaded_500mA': v_loaded_high,
                'voltage_drop_500mA': measurements.get('voc', 0) - v_loaded_high,
                'voltage_recovery_500mA': v_recovery_high
            })
            
            self.logger.info(f"✓ 100mA yüklü voltaj: {v_loaded_low:.4f} V")
            self.logger.info(f"✓ 100mA voltaj düşümü: {measurements['voltage_drop_100mA']:.4f} V")
            self.logger.info(f"✓ 500mA yüklü voltaj: {v_loaded_high:.4f} V")
            self.logger.info(f"✓ 500mA voltaj düşümü: {measurements['voltage_drop_500mA']:.4f} V")
            
            # 5. Kapasitans test (kısa süreli)
            self.logger.info("\n3. Kısa kapasitans testi...")
            
            # 200mA ile 30 saniye deşarj
            self.inst.write(':BATT:TEST:MODE DIS')
            self.inst.write(':BATT:TEST:CURR 0.2')
            self.inst.write(':BATT:OUTP ON')
            
            start_voltage = float(self.inst.query(':MEAS:VOLT?'))
            time.sleep(30)  # 30 saniye deşarj
            end_voltage = float(self.inst.query(':MEAS:VOLT?'))
            
            self.inst.write(':BATT:OUTP OFF')
            
            voltage_decline_rate = (start_voltage - end_voltage) / 30  # V/s
            measurements.update({
                'capacity_test_start_v': start_voltage,
                'capacity_test_end_v': end_voltage,
                'voltage_decline_rate': voltage_decline_rate
            })
            
            self.logger.info(f"✓ 30s deşarj başlangıç: {start_voltage:.4f} V")
            self.logger.info(f"✓ 30s deşarj bitiş: {end_voltage:.4f} V")
            self.logger.info(f"✓ Voltaj düşüş hızı: {voltage_decline_rate*1000:.2f} mV/s")
            
            # 6. Sıcaklık ölçümü (varsa)
            try:
                temperature = float(self.inst.query(':SENS:TEMP?'))
                measurements['temperature'] = temperature
                self.logger.info(f"✓ Sıcaklık: {temperature:.1f}°C")
            except:
                measurements['temperature'] = None
                self.logger.info("⚠ Sıcaklık sensörü mevcut değil")
            
            # 7. Buffer durumu
            try:
                buffer_points = int(self.inst.query(':TRACe:POINts:ACTual?'))
                measurements['buffer_points'] = buffer_points
                self.logger.info(f"✓ Buffer veri noktası: {buffer_points}")
            except:
                measurements['buffer_points'] = 0
                
        except Exception as e:
            self.logger.error(f"Ölçüm hatası: {e}")
            
        finally:
            # Power supply moduna geri dön
            try:
                self.inst.write(':OUTP OFF')
                self.inst.write(':BATT:OUTP OFF')
                self.inst.write(':FUNC PS')
            except:
                pass
        
        self.logger.info("\n" + "="*60)
        self.logger.info("SAĞLIK ÖLÇÜMLERİ TAMAMLANDI")
        self.logger.info("="*60)
        
        return measurements
    
    def calculate_aging_indicators(self, baseline, current):
        """Calculate aging indicators between two measurements"""
        if not baseline or not current:
            return None
            
        indicators = {
            'test_interval': current['timestamp'],
            'baseline_timestamp': baseline['timestamp']
        }
        
        try:
            # ESR değişimi (en kritik)
            if baseline.get('esr') and current.get('esr'):
                esr_change = current['esr'] - baseline['esr']
                esr_change_percent = (esr_change / baseline['esr']) * 100
                indicators.update({
                    'esr_baseline': baseline['esr'],
                    'esr_current': current['esr'],
                    'esr_change_ohm': esr_change,
                    'esr_change_percent': esr_change_percent
                })
                
            # Voc değişimi
            if baseline.get('voc') and current.get('voc'):
                voc_change = current['voc'] - baseline['voc']
                voc_change_percent = (voc_change / baseline['voc']) * 100
                indicators.update({
                    'voc_baseline': baseline['voc'],
                    'voc_current': current['voc'],
                    'voc_change_v': voc_change,
                    'voc_change_percent': voc_change_percent
                })
                
            # Voltage drop değişimi
            for current_level in ['100mA', '500mA']:
                drop_key = f'voltage_drop_{current_level}'
                if baseline.get(drop_key) and current.get(drop_key):
                    drop_change = current[drop_key] - baseline[drop_key]
                    indicators[f'{drop_key}_change'] = drop_change
                    
            # Kapasite göstergesi
            if baseline.get('voltage_decline_rate') and current.get('voltage_decline_rate'):
                rate_change = current['voltage_decline_rate'] - baseline['voltage_decline_rate']
                indicators['capacity_degradation'] = rate_change
                
            # Genel değerlendirme
            aging_score = 0
            issues = []
            
            # ESR artışı kontrolü
            esr_change_pct = indicators.get('esr_change_percent', 0)
            if esr_change_pct > 25:
                aging_score += 5
                issues.append(f"Kritik ESR artışı (%{esr_change_pct:.1f})")
            elif esr_change_pct > 15:
                aging_score += 3
                issues.append(f"Yüksek ESR artışı (%{esr_change_pct:.1f})")
            elif esr_change_pct > 8:
                aging_score += 2
                issues.append(f"Orta ESR artışı (%{esr_change_pct:.1f})")
            elif esr_change_pct > 3:
                aging_score += 1
                issues.append(f"Hafif ESR artışı (%{esr_change_pct:.1f})")
                
            # Voc kaybı kontrolü
            voc_change_pct = indicators.get('voc_change_percent', 0)
            if voc_change_pct < -8:
                aging_score += 4
                issues.append(f"Kritik Voc kaybı (%{abs(voc_change_pct):.1f})")
            elif voc_change_pct < -5:
                aging_score += 3
                issues.append(f"Yüksek Voc kaybı (%{abs(voc_change_pct):.1f})")
            elif voc_change_pct < -2:
                aging_score += 2
                issues.append(f"Orta Voc kaybı (%{abs(voc_change_pct):.1f})")
                
            # Voltage drop artışı
            drop_500_change = indicators.get('voltage_drop_500mA_change', 0)
            if drop_500_change > 0.1:
                aging_score += 2
                issues.append(f"Yüksek yük altında performans kaybı")
                
            # Genel değerlendirme
            if aging_score >= 7:
                assessment = "KRİTİK - Batarya acil değişim gerektirir"
                color = "🔴"
            elif aging_score >= 5:
                assessment = "YÜKSEK - Batarya yakında değişmeli"
                color = "🟠"
            elif aging_score >= 3:
                assessment = "ORTA - İzleme gerekli"
                color = "🟡"
            elif aging_score >= 1:
                assessment = "DÜŞÜK - Normal yaşlanma"
                color = "🟢"
            else:
                assessment = "MINIMAL - Batarya sağlıklı"
                color = "🟢"
                
            indicators.update({
                'aging_score': aging_score,
                'assessment': assessment,
                'color_indicator': color,
                'issues': issues
            })
            
        except Exception as e:
            self.logger.error(f"Aging calculation error: {e}")
            
        return indicators
    
    def save_results(self, measurements, filename_suffix=""):
        """Save measurement results to JSON and CSV"""
        try:
            # JSON file
            json_file = RESULTS_DIR / f"battery_health_{self.test_id}{filename_suffix}.json"
            with open(json_file, 'w') as f:
                json.dump(measurements, f, indent=2)
            
            # CSV file
            csv_file = RESULTS_DIR / f"battery_health_{self.test_id}{filename_suffix}.csv"
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Parameter', 'Value', 'Unit'])
                
                for key, value in measurements.items():
                    if key == 'timestamp':
                        writer.writerow([key, value, ''])
                    elif 'voltage' in key.lower():
                        writer.writerow([key, f'{value:.4f}' if value else 'N/A', 'V'])
                    elif 'esr' in key.lower() or 'resistance' in key.lower():
                        writer.writerow([key, f'{value:.4f}' if value else 'N/A', 'Ω'])
                    elif 'current' in key.lower():
                        writer.writerow([key, f'{value:.3f}' if value else 'N/A', 'A'])
                    elif 'temperature' in key.lower():
                        writer.writerow([key, f'{value:.1f}' if value else 'N/A', '°C'])
                    else:
                        writer.writerow([key, str(value) if value is not None else 'N/A', ''])
            
            self.logger.info(f"Sonuçlar kaydedildi:")
            self.logger.info(f"  JSON: {json_file}")
            self.logger.info(f"  CSV: {csv_file}")
            
            return json_file, csv_file
            
        except Exception as e:
            self.logger.error(f"Save error: {e}")
            return None, None
    
    def print_summary(self, measurements):
        """Print measurement summary"""
        print("\n" + "="*60)
        print("BATARYA SAĞLIK ÖZETİ")
        print("="*60)
        
        if measurements.get('voc'):
            print(f"🔋 Açık Devre Voltajı (Voc): {measurements['voc']:.3f} V")
        if measurements.get('esr'):
            print(f"⚡ İç Direnç (ESR): {measurements['esr']:.3f} Ω")
        if measurements.get('voltage_drop_100mA'):
            print(f"📉 100mA Voltaj Düşümü: {measurements['voltage_drop_100mA']:.3f} V")
        if measurements.get('voltage_drop_500mA'):
            print(f"📉 500mA Voltaj Düşümü: {measurements['voltage_drop_500mA']:.3f} V")
        if measurements.get('voltage_decline_rate'):
            print(f"📊 Voltaj Düşüş Hızı: {measurements['voltage_decline_rate']*1000:.2f} mV/s")
        if measurements.get('temperature'):
            print(f"🌡️ Sıcaklık: {measurements['temperature']:.1f}°C")
        
        print("="*60)
    
    def disconnect(self):
        """Disconnect from instrument"""
        if self.inst:
            try:
                self.inst.write(':OUTP OFF')
                self.inst.write(':BATT:OUTP OFF')
                self.inst.write('SYST:LOC')
                self.inst.close()
            except:
                pass
                
        if self.rm:
            self.rm.close()
            
        self.logger.info("Disconnected from instrument")

def main():
    """Main function"""
    print("🔋 Keithley 2281S Battery Aging Assessment Tool")
    print("=" * 60)
    
    # Kullanım seçenekleri
    print("\nKullanım Seçenekleri:")
    print("1. Yeni baseline ölçümü yap")
    print("2. Mevcut ölçümle karşılaştır")
    print("3. Sadece mevcut durum ölçümü")
    
    choice = input("\nSeçiminiz (1-3): ").strip()
    
    assessor = BatteryAgingAssessment()
    
    try:
        if not assessor.connect():
            print("❌ Cihaza bağlanılamadı!")
            return
            
        print("\n⚠️  DİKKAT: Bataryayı bağlayın ve bağlantıları kontrol edin")
        input("Devam etmek için ENTER...")
        
        if choice == "1":
            # Baseline ölçümü
            print("\n📏 Baseline ölçümü yapılıyor...")
            measurements = assessor.measure_baseline_health()
            assessor.save_results(measurements, "_baseline")
            assessor.print_summary(measurements)
            print("\n✅ Baseline ölçümü tamamlandı!")
            print("💡 Bu ölçümü current profile testinden ÖNCE kaydedin")
            
        elif choice == "2":
            # Karşılaştırmalı ölçüm
            baseline_file = input("\nBaseline JSON dosya yolu: ").strip()
            if not Path(baseline_file).exists():
                print("❌ Baseline dosyası bulunamadı!")
                return
                
            with open(baseline_file, 'r') as f:
                baseline = json.load(f)
                
            print("\n📏 Mevcut durum ölçümü yapılıyor...")
            current = assessor.measure_baseline_health()
            assessor.save_results(current, "_current")
            
            print("\n📊 Yaşlanma analizi yapılıyor...")
            indicators = assessor.calculate_aging_indicators(baseline, current)
            
            if indicators:
                assessor.save_results(indicators, "_aging_analysis")
                
                print(f"\n{indicators['color_indicator']} YAŞLANMA DEĞERLENDİRMESİ:")
                print(f"Durum: {indicators['assessment']}")
                print(f"Yaşlanma Skoru: {indicators['aging_score']}/10")
                
                if indicators.get('issues'):
                    print("\nTespit Edilen Sorunlar:")
                    for issue in indicators['issues']:
                        print(f"  • {issue}")
                        
                if indicators.get('esr_change_percent'):
                    print(f"\n📈 ESR Değişimi: %{indicators['esr_change_percent']:.2f}")
                if indicators.get('voc_change_percent'):
                    print(f"📉 Voc Değişimi: %{indicators['voc_change_percent']:.2f}")
            
        else:
            # Sadece mevcut ölçüm
            print("\n📏 Mevcut durum ölçümü yapılıyor...")
            measurements = assessor.measure_baseline_health()
            assessor.save_results(measurements)
            assessor.print_summary(measurements)
            
        print("\n✅ Tüm işlemler tamamlandı!")
        
    except KeyboardInterrupt:
        print("\n⏹️ İşlem kullanıcı tarafından durduruldu")
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        
    finally:
        assessor.disconnect()

if __name__ == "__main__":
    main() 