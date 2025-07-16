#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keithley 2281S Simple Current Profile Application
Basit döngü bazlı akım profili uygulaması
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
OUTPUT_DIR = Path('data')
OUTPUT_DIR.mkdir(exist_ok=True)


def connect_instrument(resource):
    """Cihaza bağlan"""
    try:
        rm = pyvisa.ResourceManager('@py')
        inst = rm.open_resource(resource)
        inst.read_termination = '\n'
        inst.write_termination = '\n'
        inst.timeout = 10000  # 10 saniye
        
        # Clear ve reset
        inst.write('*CLS')
        time.sleep(0.5)
        
        print("Bağlandı:", inst.query('*IDN?').strip())
        return inst, rm
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None, None


def measure_initial_voltage(inst):
    """Başlangıç voltajını ölç"""
    try:
        inst.write(':OUTP OFF')
        time.sleep(0.5)
        voltage = float(inst.query(':MEAS:VOLT?'))
        print(f"Başlangıç voltajı: {voltage:.3f} V")
        return voltage
    except:
        print("Voltaj ölçülemedi")
        return 3.7  # Varsayılan


def apply_simple_profile(inst, csv_file):
    """Basit döngü ile profili uygula"""
    # CSV'yi yükle
    df = pd.read_csv(csv_file)
    print(f"Profil yüklendi: {len(df)} nokta")
    
    # Reset
    inst.write('*RST')
    time.sleep(2)
    inst.write('*CLS')
    
    # Temel ayarlar
    inst.write(f':VOLT {3.7}')  # Nominal voltaj
    inst.write(f':VOLT:PROT {VOLTAGE_PROTECTION}')
    inst.write(f':CURR:PROT {1.5}')
    print("Koruma limitleri ayarlandı")
    
    # Çıktı dosyası
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f'battery_test_simple_{timestamp}.csv'
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time_s', 'set_current_a', 'measured_voltage_v', 
                        'measured_current_a'])
        
        # Çıkışı aç
        inst.write(':OUTP ON')
        print("Test başlatıldı...")
        
        start_time = time.time()
        
        try:
            for idx, row in df.iterrows():
                target_time = row['time_s']
                set_current = row['current_a']
                
                # Cihaz mantığına dönüştür (işaret ters)
                device_current = -set_current
                
                # Akımı ayarla
                inst.write(f':CURR {abs(device_current):.4f}')
                
                # Voltajı akım yönüne göre ayarla
                if set_current > 0:  # Deşarj
                    inst.write(':VOLT 3.5')  # Bataryadan düşük
                else:  # Şarj
                    inst.write(':VOLT 3.9')  # Bataryadan yüksek
                
                # Hedef zamana kadar bekle
                while (time.time() - start_time) < target_time:
                    time.sleep(0.1)
                
                # Ölçüm yap
                try:
                    time.sleep(0.2)  # Stabilizasyon
                    voltage = float(inst.query(':MEAS:VOLT?'))
                    current = float(inst.query(':MEAS:CURR?'))
                    
                    # Kullanıcı mantığına dönüştür
                    user_current = -current
                    
                    elapsed = time.time() - start_time
                    writer.writerow([f"{elapsed:.1f}", f"{set_current:.3f}", 
                                   f"{voltage:.3f}", f"{user_current:.3f}"])
                    
                    # İlerleme göster
                    if idx % 5 == 0:
                        print(f"Zaman: {elapsed:.1f}s | Set: {set_current:.3f}A | "
                              f"Ölçülen: V={voltage:.3f}V, I={user_current:.3f}A")
                        
                except Exception as e:
                    print(f"Ölçüm hatası: {e}")
                    writer.writerow([target_time, set_current, "ERROR", "ERROR"])
                    
                # Voltaj kontrolü
                if 'voltage' in locals() and (voltage > VOLTAGE_PROTECTION or voltage < 2.5):
                    print(f"Voltaj limiti aşıldı: {voltage}V - Test durduruluyor")
                    break
                    
        except KeyboardInterrupt:
            print("\nTest iptal edildi")
            
        finally:
            # Çıkışı kapat
            inst.write(':OUTP OFF')
            print(f"\nTest tamamlandı. Sonuçlar: {output_file}")


def main():
    """Ana fonksiyon"""
    print("Keithley 2281S Simple Current Profile Test")
    print("=" * 50)
    
    # Bağlan
    inst, rm = connect_instrument(RESOURCE_ADDR)
    if not inst:
        return
        
    try:
        # Başlangıç voltajı
        initial_v = measure_initial_voltage(inst)
        
        # Test parametreleri
        print(f"\nCSV Dosyası: {PROFILE_CSV}")
        print(f"Voltaj Limiti: {VOLTAGE_PROTECTION} V")
        print("Pozitif akım = Deşarj, Negatif akım = Şarj")
        
        input("\nBataryayı bağlayın ve Enter'a basın...")
        
        # Profili uygula
        apply_simple_profile(inst, PROFILE_CSV)
        
    except Exception as e:
        print(f"Test hatası: {e}")
        
    finally:
        if inst:
            inst.write(':OUTP OFF')
            inst.write('SYST:LOC')
            inst.close()
        if rm:
            rm.close()


if __name__ == "__main__":
    main()
