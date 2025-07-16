#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keithley 2281S Batarya Yaşlanma Test Scripti
CSV akım profili uygulama + ESR/Voc ölçümleri
"""

import pyvisa
import pandas as pd
import time
import csv
import json
from datetime import datetime
from pathlib import Path
import sys
import re

# Test Parametreleri
CONFIG = {
    'evoc_delay': 0.05,      # ESR ölçüm gecikmesi (s)
    'sample_interval': 0.04,  # Örnekleme aralığı (s)
    'voltage_limits': {
        'min': 2.5,          # Minimum voltaj limiti (V)
        'max': 4.5           # Maksimum voltaj limiti (V)
    },
    'current_limits': {
        'max_charge': 1.2,   # Maksimum şarj akımı (A)
        'max_discharge': 1.2 # Maksimum deşarj akımı (A)
    },
    'safety': {
        'temp_limit': 45.0,  # Sıcaklık limiti (°C) - eğer destekleniyorsa
        'timeout': 7200      # Maksimum test süresi (s)
    }
}

class BatteryAgingTest:
    def __init__(self, csv_file='keithley_hücre_test2.csv'):
        self.csv_file = csv_file
        self.inst = None
        self.rm = None
        self.test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = Path('./results')
        self.results_dir.mkdir(exist_ok=True)
        
        # Sayısal değer ayıklama için regex
        self.num = re.compile(r'[-+0-9.E]+')
        
    def connect(self):
        """Keithley 2281S'e bağlan"""
        try:
            self.rm = pyvisa.ResourceManager('@py')
            
            # USB cihazını bul
            resources = self.rm.list_resources()
            keithley = None
            for r in resources:
                if '1510' in r and '8833' in r:  # Keithley vendor/product ID
                    keithley = r
                    break
            
            if not keithley:
                raise Exception("Keithley 2281S bulunamadı!")
            
            print(f"Cihaz bulundu: {keithley}")
            
            # Bağlan
            self.inst = self.rm.open_resource(keithley)
            self.inst.read_termination = '\n'
            self.inst.write_termination = '\n'
            self.inst.timeout = 10000
            
            # Temizle ve kimlik kontrol et
            self.write('*CLS')
            idn = self.query('*IDN?')
            print(f"Bağlandı: {idn}")
            
            # Uzaktan kontrol moduna geç
            self.write('SYST:REM')
            
            return True
            
        except Exception as e:
            print(f"Bağlantı hatası: {e}")
            return False
    
    def write(self, cmd):
        """Komut gönder ve logla"""
        self.inst.write(cmd)
        print(f'[W] {cmd}')
    
    def query(self, cmd):
        """Sorgu gönder ve logla"""
        response = self.inst.query(cmd).strip()
        print(f'[Q] {cmd} => {response}')
        return response
    
    def configure_battery_test(self):
        """Battery test modunu yapılandır"""
        print("\n=== CİHAZ YAPILANDIRILIYOR ===")
        
        # Battery test moduna geç
        self.write(':FUNC TEST')
        self.write(':BATT:TEST:MODE DIS')
        
        # Örnekleme ve ölçüm ayarları
        self.write(f':BATT:TEST:SENS:SAMP:INT {CONFIG["sample_interval"]}')
        self.write(f':BATT:TEST:SENS:EVOC:DELA {CONFIG["evoc_delay"]}')
        
        # Voltaj limitleri
        self.write(f':BATT:DIS:VLIM {CONFIG["voltage_limits"]["max"]}')
        self.write(f':BATT:DIS:VLOW {CONFIG["voltage_limits"]["min"]}')
        
        # Format ayarları
        self.write(':FORM:UNITS OFF')
        self.write(':SYST:AZER OFF')
        
        # Data logger'ı başlat
        self.write(':BATT:DATA:CLE')
        self.write(':BATT:DATA:STAT ON')
        self.write(':BATT:TEST:EXEC STAR')
        
        print("Yapılandırma tamamlandı.")
    
    def measure_evoc(self, label=""):
        """ESR ve Voc ölçümü yap"""
        print(f"\n=== {label} ESR/Voc ÖLÇÜMÜ ===")
        
        # Çıkışı kapat
        self.write(':BATT:OUTP OFF')
        time.sleep(1)
        
        # EVOC ölçümü
        try:
            result = self.query(':BATT:TEST:MEAS:EVOC?')
            values = result.split(',')
            
            if len(values) >= 2:
                voc = float(values[0])
                esr = float(values[1])
                
                print(f"Voc (Açık Devre Voltajı): {voc:.4f} V")
                print(f"ESR (İç Direnç): {esr:.4f} Ω")
                
                return {'voc': voc, 'esr': esr, 'timestamp': datetime.now().isoformat()}
            else:
                print(f"Beklenmeyen ölçüm formatı: {result}")
                return None
                
        except Exception as e:
            print(f"EVOC ölçüm hatası: {e}")
            return None
    
    def get_battery_health_metrics(self):
        """Batarya sağlık metrikleri (ek ölçümler)"""
        metrics = {}
        
        try:
            # Mevcut voltaj ve akım
            voltage = float(self.query(':MEAS:VOLT?'))
            current = float(self.query(':MEAS:CURR?'))
            
            metrics['voltage'] = voltage
            metrics['current'] = current
            
            # Buffer'dan istatistikler (eğer varsa)
            try:
                points = int(self.query(':TRACe:POINts:ACTual?'))
                if points > 0:
                    # Son dakika ortalamaları
                    data = self.query(':BATT:DATA:DATA:SEL? -60,0,"VOLT,CURR"')
                    if data:
                        values = [float(x) for x in data.split(',')]
                        if len(values) >= 2:
                            metrics['avg_voltage_1min'] = sum(values[::2]) / len(values[::2])
                            metrics['avg_current_1min'] = sum(values[1::2]) / len(values[1::2])
            except:
                pass
                
        except Exception as e:
            print(f"Metrik okuma hatası: {e}")
            
        return metrics
    
    def load_current_profile(self):
        """CSV dosyasından akım profilini yükle"""
        try:
            df = pd.read_csv(self.csv_file)
            
            # Sütun isimlerini düzelt
            if 'current' in df.columns and 'time' in df.columns:
                # Zaten doğru isimler
                pass
            elif '0' in df.columns and 'time' in df.columns:
                df = df.rename(columns={'0': 'current'})
            else:
                # İlk iki sütunu kullan
                df.columns = ['current', 'time'][:len(df.columns)]
            
            print(f"\nCSV Profili:")
            print(f"  Toplam adım: {len(df)}")
            print(f"  Süre: {df['time'].max()} saniye ({df['time'].max()/60:.1f} dakika)")
            print(f"  Akım aralığı: {df['current'].min():.3f} A ~ {df['current'].max():.3f} A")
            print(f"  Şarj adımları: {(df['current'] > 0).sum()}")
            print(f"  Deşarj adımları: {(df['current'] < 0).sum()}")
            
            return df
            
        except Exception as e:
            print(f"CSV okuma hatası: {e}")
            return None
    
    def apply_current_profile(self, df):
        """Akım profilini uygula"""
        print(f"\n=== AKIM PROFİLİ UYGULANMAYA BAŞLANIYOR ===")
        
        # Log dosyası
        log_file = self.results_dir / f'current_profile_{self.test_id}.csv'
        
        with open(log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['elapsed_s', 'target_s', 'set_current_A', 
                           'measured_V', 'measured_A', 'mode'])
        
        start_time = time.time()
        last_mode = None
        
        try:
            for idx, row in df.iterrows():
                target_current = row['current']
                target_time = row['time']
                
                # Mod kontrolü
                if target_current >= 0:
                    mode = 'CHARGE'
                    self.write(':BATT:TEST:MODE CHG')
                    self.write(f':BATT:CHG:CURR {abs(target_current)}')
                else:
                    mode = 'DISCHARGE'
                    self.write(':BATT:TEST:MODE DIS')
                    self.write(f':BATT:DIS:CURR {abs(target_current)}')
                
                # Mod değişimi bildirimi
                if mode != last_mode:
                    print(f"\n[{target_time}s] Mod: {mode}")
                    last_mode = mode
                
                # Çıkışı aç
                self.write(':BATT:OUTP ON')
                
                # Hedef zamana kadar bekle
                while (time.time() - start_time) < target_time:
                    time.sleep(0.01)
                
                # Ölçüm al
                try:
                    voltage = float(self.query(':MEAS:VOLT?'))
                    current = float(self.query(':MEAS:CURR?'))
                except:
                    voltage, current = 0.0, 0.0
                
                elapsed = time.time() - start_time
                
                # Kaydet
                with open(log_file, 'a') as f:
                    writer = csv.writer(f)
                    writer.writerow([f'{elapsed:.3f}', target_time, f'{target_current:.6f}',
                                   f'{voltage:.4f}', f'{current:.6f}', mode])
                
                # İlerleme göster (her 10 adımda)
                if idx % 10 == 0:
                    print(f"[{elapsed:6.1f}s] Adım {idx+1}/{len(df)} | "
                          f"Hedef: {target_current:7.3f}A | "
                          f"Ölçüm: {voltage:6.3f}V {current:7.3f}A")
                
                # Güvenlik kontrolü
                if voltage > CONFIG['voltage_limits']['max'] or voltage < CONFIG['voltage_limits']['min']:
                    print(f"\n⚠️ Voltaj limiti aşıldı: {voltage:.3f}V")
                    break
                    
                if elapsed > CONFIG['safety']['timeout']:
                    print(f"\n⚠️ Zaman aşımı: {elapsed:.1f}s")
                    break
            
            print(f"\n=== AKIM PROFİLİ TAMAMLANDI ===")
            print(f"Log dosyası: {log_file}")
            
        except KeyboardInterrupt:
            print("\n\nTest kullanıcı tarafından durduruldu.")
        except Exception as e:
            print(f"\n\nTest hatası: {e}")
        finally:
            self.write(':BATT:OUTP OFF')
    
    def export_buffer_data(self):
        """Buffer'daki tüm veriyi dışa aktar"""
        try:
            points = int(self.query(':TRACe:POINts:ACTual?'))
            if points == 0:
                print("Buffer'da veri yok")
                return None
            
            print(f"\nBuffer'dan {points} veri noktası dışa aktarılıyor...")
            
            csv_file = self.results_dir / f'buffer_data_{self.test_id}.csv'
            
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['time_s', 'voltage_V', 'current_A'])
                
                # Veriyi parçalar halinde oku
                chunk_size = 100
                for start in range(1, points + 1, chunk_size):
                    end = min(start + chunk_size - 1, points)
                    
                    try:
                        data = self.query(f':BATT:DATA:DATA:SEL? {start},{end},"VOLT,CURR,REL"')
                        if data:
                            values = data.split(',')
                            # Her 3 değer bir satır (volt, curr, rel_time)
                            for i in range(0, len(values), 3):
                                if i + 2 < len(values):
                                    writer.writerow([values[i+2], values[i], values[i+1]])
                    except:
                        continue
            
            print(f"Buffer verisi kaydedildi: {csv_file}")
            return csv_file
            
        except Exception as e:
            print(f"Buffer dışa aktarma hatası: {e}")
            return None
    
    def save_test_report(self, initial_evoc, final_evoc, health_before, health_after):
        """Test raporunu kaydet"""
        report = {
            'test_id': self.test_id,
            'test_date': datetime.now().isoformat(),
            'csv_profile': self.csv_file,
            'configuration': CONFIG,
            'results': {
                'initial_measurements': initial_evoc,
                'final_measurements': final_evoc,
                'health_metrics_before': health_before,
                'health_metrics_after': health_after,
                'aging_indicators': {}
            }
        }
        
        # Yaşlanma göstergeleri hesapla
        if initial_evoc and final_evoc:
            esr_change = final_evoc['esr'] - initial_evoc['esr']
            esr_change_pct = (esr_change / initial_evoc['esr']) * 100
            
            voc_change = final_evoc['voc'] - initial_evoc['voc']
            voc_change_pct = (voc_change / initial_evoc['voc']) * 100
            
            report['results']['aging_indicators'] = {
                'esr_change_ohm': esr_change,
                'esr_change_percent': esr_change_pct,
                'voc_change_v': voc_change,
                'voc_change_percent': voc_change_pct,
                'assessment': self._assess_aging(esr_change_pct, voc_change_pct)
            }
        
        # JSON olarak kaydet
        report_file = self.results_dir / f'test_report_{self.test_id}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nTest raporu kaydedildi: {report_file}")
        
        # Özet yazdır
        self._print_summary(report)
        
        return report_file
    
    def _assess_aging(self, esr_change_pct, voc_change_pct):
        """Batarya yaşlanma durumunu değerlendir"""
        if esr_change_pct > 50:
            return "Kritik yaşlanma - Batarya değişimi önerilir"
        elif esr_change_pct > 25:
            return "Önemli yaşlanma - Yakın takip gerekli"
        elif esr_change_pct > 10:
            return "Orta düzeyde yaşlanma - Normal"
        else:
            return "Düşük yaşlanma - Batarya sağlıklı"
    
    def _print_summary(self, report):
        """Test özeti yazdır"""
        print("\n" + "="*60)
        print("TEST ÖZETİ")
        print("="*60)
        
        res = report['results']
        
        if res['initial_measurements'] and res['final_measurements']:
            print(f"\nBaşlangıç Değerleri:")
            print(f"  Voc: {res['initial_measurements']['voc']:.4f} V")
            print(f"  ESR: {res['initial_measurements']['esr']:.4f} Ω")
            
            print(f"\nBitiş Değerleri:")
            print(f"  Voc: {res['final_measurements']['voc']:.4f} V")
            print(f"  ESR: {res['final_measurements']['esr']:.4f} Ω")
            
            if 'aging_indicators' in res and res['aging_indicators']:
                ind = res['aging_indicators']
                print(f"\nYaşlanma Göstergeleri:")
                print(f"  ESR Değişimi: {ind['esr_change_ohm']:.4f} Ω ({ind['esr_change_percent']:+.1f}%)")
                print(f"  Voc Değişimi: {ind['voc_change_v']:.4f} V ({ind['voc_change_percent']:+.1f}%)")
                print(f"  Değerlendirme: {ind['assessment']}")
        
        print("="*60)
    
    def cleanup(self):
        """Temizlik ve bağlantı kapatma"""
        try:
            if self.inst:
                self.write(':BATT:OUTP OFF')
                self.write(':BATT:DATA:STAT OFF')
                self.write('SYST:LOC')
                self.inst.close()
            if self.rm:
                self.rm.close()
            print("\nBağlantı kapatıldı.")
        except:
            pass
    
    def run_aging_test(self):
        """Komple yaşlanma testini çalıştır"""
        try:
            # Bağlan
            if not self.connect():
                raise Exception("Cihaza bağlanılamadı!")
            
            # Yapılandır
            self.configure_battery_test()
            
            # CSV'yi yükle
            df = self.load_current_profile()
            if df is None:
                raise Exception("CSV dosyası okunamadı!")
            
            # Test öncesi ölçümler
            print("\n" + "="*60)
            initial_evoc = self.measure_evoc("TEST ÖNCESİ")
            health_before = self.get_battery_health_metrics()
            
            # Güvenlik onayı
            print("\n" + "!"*60)
            print("DİKKAT: Test başlamak üzere!")
            print(f"- Tahmini süre: {df['time'].max()/60:.1f} dakika")
            print("- Batarya bağlantılarını kontrol edin")
            print("- Test sırasında bağlantılara dokunmayın")
            print("!"*60)
            
            input("\nDevam etmek için ENTER (İptal için Ctrl+C)...")
            
            # Akım profilini uygula
            self.apply_current_profile(df)
            
            # Test sonrası ölçümler
            time.sleep(2)  # Stabilizasyon için bekle
            final_evoc = self.measure_evoc("TEST SONRASI")
            health_after = self.get_battery_health_metrics()
            
            # Buffer verilerini dışa aktar
            self.export_buffer_data()
            
            # Rapor oluştur ve kaydet
            self.save_test_report(initial_evoc, final_evoc, health_before, health_after)
            
            print("\n✅ TEST BAŞARIYLA TAMAMLANDI!")
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Test kullanıcı tarafından iptal edildi.")
        except Exception as e:
            print(f"\n\n❌ Test hatası: {e}")
        finally:
            self.cleanup()


def main():
    """Ana program"""
    print("="*60)
    print("Keithley 2281S Batarya Yaşlanma Testi")
    print("="*60)
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # CSV dosyasını kontrol et
    csv_file = 'keithley_hücre_test2.csv'
    if not Path(csv_file).exists():
        print(f"\n❌ HATA: '{csv_file}' dosyası bulunamadı!")
        print("CSV dosyasının bu script ile aynı dizinde olduğundan emin olun.")
        sys.exit(1)
    
    # Testi başlat
    test = BatteryAgingTest(csv_file)
    test.run_aging_test()


if __name__ == "__main__":
    main()
