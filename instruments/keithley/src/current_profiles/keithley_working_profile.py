#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keithley 2281S Working Current Profile Application
CSV dosyasından akım profili uygulama - çalışan versiyon
"""

import pyvisa
import pandas as pd
import time
import csv
import warnings
from datetime import datetime
from pathlib import Path

# PyVISA uyarılarını bastır
warnings.filterwarnings("ignore")

# Konfigürasyon
RESOURCE_ADDR = 'USB0::1510::8833::4587429::0::INSTR'
PROFILE_CSV = 'current_profile_for_sourcing.csv'
VOLTAGE_PROTECTION = 4.2  # V
VOLTAGE_NOMINAL = 3.7     # V
OUTPUT_DIR = Path('data')
OUTPUT_DIR.mkdir(exist_ok=True)


class BatteryProfileTester:
    """Batarya akım profili test sistemi"""
    
    def __init__(self, resource_addr, csv_file):
        self.resource_addr = resource_addr
        self.csv_file = csv_file
        self.inst = None
        self.rm = None
        self.test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = OUTPUT_DIR / f'battery_test_{self.test_id}.csv'
        
    def connect(self):
        """Cihaza bağlan"""
        try:
            self.rm = pyvisa.ResourceManager('@py')
            self.inst = self.rm.open_resource(self.resource_addr)
            self.inst.read_termination = '\n'
            self.inst.write_termination = '\n'
            self.inst.timeout = 5000
            
            # Clear
            self.inst.write('*CLS')
            time.sleep(0.5)
            
            idn = self.inst.query('*IDN?').strip()
            print(f"Bağlandı: {idn}")
            return True
            
        except Exception as e:
            print(f"Bağlantı hatası: {e}")
            return False
            
    def _parse_measurement(self, response):
        """
        Ölçüm yanıtını parse et
        Format: '+1.000000E-01A,+3.478012E+00V,+5.982166E+03s'
        """
        try:
            parts = response.strip().split(',')
            
            if len(parts) >= 3:
                # Akım (A birimini kaldır)
                current_str = parts[0].replace('A', '').strip()
                current = float(current_str)
                
                # Voltaj (V birimini kaldır)
                voltage_str = parts[1].replace('V', '').strip()
                voltage = float(voltage_str)
                
                # Zaman (s birimini kaldır)
                time_str = parts[2].replace('s', '').strip()
                time_val = float(time_str)
                
                return {
                    'current': current,
                    'voltage': voltage,
                    'time': time_val
                }
            else:
                print(f"Beklenmeyen format: {response}")
                return None
                
        except Exception as e:
            print(f"Parse hatası: {response} - {e}")
            return None
            
    def setup_instrument(self):
        """Cihazı yapılandır"""
        try:
            print("Cihaz yapılandırılıyor...")
            
            # Reset
            self.inst.write('*RST')
            time.sleep(2)
            self.inst.write('*CLS')
            
            # Temel ayarlar
            self.inst.write(f':VOLT {VOLTAGE_NOMINAL}')
            self.inst.write(f':VOLT:PROT {VOLTAGE_PROTECTION}')
            self.inst.write(f':CURR:PROT 1.5')
            
            # Concurrent ölçüm modu (V+I birlikte)
            self.inst.write(':SENS:FUNC "CONC"')
            time.sleep(0.5)
            
            print("Cihaz hazır")
            return True
            
        except Exception as e:
            print(f"Setup hatası: {e}")
            return False
            
    def load_profile(self):
        """CSV profilini yükle"""
        try:
            df = pd.read_csv(self.csv_file)
            print(f"Profil yüklendi: {len(df)} nokta")
            
            # Akım aralığı
            print(f"Akım aralığı: {df['current_a'].min():.3f} A ile {df['current_a'].max():.3f} A")
            
            return df
            
        except Exception as e:
            print(f"CSV yükleme hatası: {e}")
            return None
            
    def measure_battery_voltage(self):
        """Batarya voltajını ölç (çıkış açıkken)"""
        try:
            # Çıkışı aç, düşük akımla
            self.inst.write(':CURR 0.001')  # 1mA
            self.inst.write(':VOLT 3.0')     # Düşük voltaj
            self.inst.write(':OUTP ON')
            time.sleep(1)
            
            # Ölçüm yap
            response = self.inst.query(':READ?')
            result = self._parse_measurement(response)
            
            # Çıkışı kapat
            self.inst.write(':OUTP OFF')
            
            if result:
                voltage = result['voltage']
                print(f"Batarya voltajı: {voltage:.3f} V")
                return voltage
            else:
                print("Batarya voltajı ölçülemedi, varsayılan kullanılıyor")
                return VOLTAGE_NOMINAL
                
        except Exception as e:
            print(f"Voltaj ölçüm hatası: {e}")
            self.inst.write(':OUTP OFF')
            return VOLTAGE_NOMINAL
            
    def apply_profile(self, df):
        """Profili uygula"""
        print("\nProfil uygulanıyor...")
        
        # Çıktı dosyasını aç
        with open(self.output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['time_s', 'set_current_a', 'measured_voltage_v', 
                           'measured_current_a', 'power_w', 'status'])
            
            # Çıkışı aç
            self.inst.write(':OUTP ON')
            time.sleep(0.5)
            
            start_time = time.time()
            errors_count = 0
            
            try:
                for idx, row in df.iterrows():
                    target_time = row['time_s']
                    set_current = row['current_a']
                    
                    # Akım işaret dönüşümü
                    # Pozitif = Deşarj (cihaz negatif akım çeker)
                    # Negatif = Şarj (cihaz pozitif akım verir)
                    device_current = -set_current
                    
                    # Akım limitini ayarla
                    self.inst.write(f':CURR {abs(device_current):.4f}')
                    
                    # Voltajı ayarla
                    if set_current > 0:  # Deşarj
                        # Bataryadan akım çekmek için voltajı düşük ayarla
                        self.inst.write(f':VOLT {VOLTAGE_NOMINAL - 0.3:.3f}')
                    else:  # Şarj
                        # Bataryaya akım vermek için voltajı yüksek ayarla
                        self.inst.write(f':VOLT {VOLTAGE_NOMINAL + 0.3:.3f}')
                    
                    # Hedef zamana kadar bekle
                    while (time.time() - start_time) < target_time:
                        time.sleep(0.05)
                    
                    # Ölçüm yap
                    time.sleep(0.2)  # Stabilizasyon
                    
                    try:
                        # READ komutu her zaman akım,voltaj,zaman döndürüyor
                        response = self.inst.query(':READ?')
                        result = self._parse_measurement(response)
                        
                        if result:
                            voltage = result['voltage']
                            current = result['current']
                            
                            # İşaret düzeltmesi
                            user_current = -current
                            power = abs(voltage * user_current)
                            
                            # Durum kontrolü
                            status = 'OK'
                            if voltage > VOLTAGE_PROTECTION:
                                status = 'OVERVOLTAGE'
                            elif voltage < 2.5:
                                status = 'UNDERVOLTAGE'
                                
                            # Kaydet
                            elapsed = time.time() - start_time
                            writer.writerow([f"{elapsed:.1f}", f"{set_current:.3f}", 
                                           f"{voltage:.3f}", f"{user_current:.3f}",
                                           f"{power:.3f}", status])
                            
                            # İlerleme
                            if idx % 5 == 0 or idx == 0:
                                print(f"[{idx+1}/{len(df)}] {elapsed:.1f}s | "
                                      f"Set: {set_current:.3f}A | "
                                      f"Ölçülen: V={voltage:.3f}V, I={user_current:.3f}A")
                                
                            errors_count = 0  # Başarılı ölçüm
                            
                            # Güvenlik kontrolü
                            if status != 'OK':
                                print(f"Güvenlik limiti: {status}")
                                if input("Devam? (e/h): ").lower() != 'e':
                                    break
                        else:
                            raise Exception("Parse edilemedi")
                            
                    except Exception as e:
                        errors_count += 1
                        print(f"Ölçüm hatası ({errors_count}): {e}")
                        
                        elapsed = time.time() - start_time
                        writer.writerow([f"{elapsed:.1f}", f"{set_current:.3f}", 
                                       "ERROR", "ERROR", "ERROR", "ERROR"])
                        
                        if errors_count > 3:
                            print("Çok fazla hata, test durduruluyor")
                            break
                            
            except KeyboardInterrupt:
                print("\nTest kullanıcı tarafından durduruldu")
                
            finally:
                # Çıkışı kapat
                self.inst.write(':OUTP OFF')
                elapsed = time.time() - start_time
                print(f"\nToplam süre: {elapsed:.1f} saniye")
                
    def run_test(self):
        """Ana test döngüsü"""
        # Profili yükle
        df = self.load_profile()
        if df is None:
            return False
            
        # Cihazı yapılandır
        if not self.setup_instrument():
            return False
            
        # Batarya voltajını ölç
        battery_v = self.measure_battery_voltage()
        
        # Test parametreleri özeti
        print("\n" + "="*50)
        print("TEST PARAMETRELERİ")
        print("="*50)
        print(f"Profil: {self.csv_file}")
        print(f"Süre: {df['time_s'].max()} saniye")
        print(f"Nokta sayısı: {len(df)}")
        print(f"Batarya voltajı: {battery_v:.3f} V")
        print(f"Voltaj limiti: {VOLTAGE_PROTECTION} V")
        print("\nPozitif akım = Deşarj")
        print("Negatif akım = Şarj")
        print("="*50)
        
        input("\nBatarya bağlı mı? Test başlatmak için Enter...")
        
        # Profili uygula
        self.apply_profile(df)
        
        print(f"\nSonuçlar kaydedildi: {self.output_file}")
        return True
        
    def disconnect(self):
        """Bağlantıyı kapat"""
        if self.inst:
            try:
                self.inst.write(':OUTP OFF')
                self.inst.write('SYST:LOC')
                self.inst.close()
            except:
                pass
                
        if self.rm:
            self.rm.close()
            
        print("Bağlantı kapatıldı")


def main():
    """Ana fonksiyon"""
    print("Keithley 2281S Battery Current Profile Test")
    print("Çalışan Versiyon")
    print("="*50)
    
    tester = BatteryProfileTester(RESOURCE_ADDR, PROFILE_CSV)
    
    try:
        if not tester.connect():
            return
            
        tester.run_test()
        
    except Exception as e:
        print(f"Kritik hata: {e}")
        
    finally:
        tester.disconnect()


if __name__ == "__main__":
    main()
