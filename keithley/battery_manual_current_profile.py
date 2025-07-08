#!/usr/bin/env python3
"""
Keithley 2281S - Bataryaya Manuel Akım Profili Uygulama
Batarya test modunu durdurup, CSV profilini manuel olarak uygular
"""

import pyvisa
import pandas as pd
import time
import csv
import re

RESOURCE = 'USB0::1510::8833::4587429::0::INSTR'
CSV_FILE = 'keithley_hücre_test2.csv'
LOG_FILE = 'battery_manual_profile.csv'

# Sayısal değer çıkarma için regex
num_re = re.compile(r'([-+0-9.]+E[+-]\d+|[-+0-9.]+)')

def parse_float(text):
    """String'den float değer çıkar"""
    match = num_re.match(text)
    return float(match.group(0)) if match else 0.0

def setup_manual_mode(inst):
    """Cihazı manuel kontrol moduna al"""
    print("Cihaz manuel kontrol moduna alınıyor...")
    
    # 1. Tüm testleri durdur
    try:
        inst.write(':BATT:TEST:ABORT')
        print("  - Batarya testi durduruldu")
    except:
        pass
    
    # 2. Tüm çıkışları kapat
    inst.write(':OUTP OFF')
    inst.write(':BATT:OUTP OFF')
    time.sleep(1)
    
    # 3. Manuel source moduna geç
    inst.write('*CLS')
    inst.write(':FUNC SOUR')  # Manuel source mode
    time.sleep(1)
    
    # 4. Akım source olarak ayarla
    inst.write(':SOUR:FUNC CURR')
    inst.write(':SOUR:CURR 0')  # Başlangıçta 0A
    inst.write(':SOUR:VOLT:ILIM 5.0')  # Voltaj limiti
    
    # 5. Ölçüm ayarları
    inst.write(':SENS:FUNC "VOLT"')
    inst.write(':SENS:VOLT:RANG:AUTO ON')
    
    print("  - Manuel mod hazır")

def apply_current(inst, current_value):
    """Belirli bir akım değeri uygula"""
    if current_value >= 0:
        # Pozitif akım: Charge (source mode)
        inst.write(':SOUR:FUNC CURR')
        inst.write(f':SOUR:CURR {current_value:.6f}')
        mode = 'CHARGE'
    else:
        # Negatif akım: Discharge - bu durumda voltaj ile kontrol
        # Düşük voltaj ayarlayarak deşarj sağla
        inst.write(':SOUR:FUNC VOLT')
        # Bataryanın mevcut voltajından düşük bir değer ayarla
        discharge_voltage = 3.0  # Batarya voltajından düşük
        inst.write(f':SOUR:VOLT {discharge_voltage:.3f}')
        inst.write(f':SOUR:CURR:ILIM {abs(current_value):.6f}')
        mode = 'DISCHARGE'
    
    return mode

def get_measurement(inst):
    """Ölçüm al"""
    try:
        # Direct measurement
        voltage = float(inst.query(':MEAS:VOLT?'))
        current = float(inst.query(':MEAS:CURR?'))
        return voltage, current
    except:
        # Eğer MEAS çalışmazsa READ dene
        try:
            response = inst.query(':READ?').strip()
            parts = response.split(',')
            if len(parts) >= 2:
                current = parse_float(parts[0])
                voltage = parse_float(parts[1])
                return voltage, current
        except:
            pass
    return 0.0, 0.0

def main():
    rm = pyvisa.ResourceManager('@py')
    inst = rm.open_resource(RESOURCE)
    inst.read_termination = inst.write_termination = '\n'
    inst.timeout = 5000

    # CSV dosyasını yükle
    df = pd.read_csv(CSV_FILE)
    
    # İlk 20 satırı test et
    df = df.head(20)
    
    print(f"CSV yüklendi: {len(df)} veri noktası")
    print(f"Akım aralığı: {df['current'].min():.3f} A - {df['current'].max():.3f} A")

    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time', 'target_current', 'measured_current', 'measured_voltage', 'mode'])

        try:
            # Cihazı manuel moda al
            setup_manual_mode(inst)
            
            # Çıkışı aç
            inst.write(':OUTP ON')
            time.sleep(1)

            t0 = time.time()
            
            for idx, row in df.iterrows():
                target_current = row['current']
                
                # Akımı uygula
                mode = apply_current(inst, target_current)
                time.sleep(0.3)  # Akımın stabilize olması için bekle

                # Ölçüm al
                voltage, current = get_measurement(inst)
                
                elapsed = time.time() - t0
                writer.writerow([elapsed, target_current, current, voltage, mode])
                
                print(f"{idx+1:2d}: {mode:9s} | Hedef {target_current:7.4f} A, Ölçülen {current:7.4f} A, {voltage:.3f} V")

                # 1 saniye bekle
                time.sleep(0.7)

        except KeyboardInterrupt:
            print("\nTest kullanıcı tarafından durduruldu.")
        except Exception as e:
            print(f"Hata: {e}")
        finally:
            # Temizlik
            try:
                inst.write(':OUTP OFF')
                inst.write(':SOUR:CURR 0')  # Akımı sıfırla
                inst.write('SYST:LOC')
            except:
                pass
            inst.close()
            rm.close()
            print("Cihaz güvenli durumda kapatıldı.")

if __name__ == "__main__":
    main() 