#!/usr/bin/env python3
"""
Keithley 2281S - Battery Test Mode ile Akım Profili
Battery test mode her iki yön için optimize edilmiş
"""

import pyvisa
import pandas as pd
import time
import csv
import re

RESOURCE = 'USB0::1510::8833::4587429::0::INSTR'
CSV_FILE = 'keithley_hücre_test2.csv'
LOG_FILE = 'battery_current_profile_battery_mode.csv'

# Sayısal değer çıkarma için regex
num_re = re.compile(r'([-+0-9.]+E[+-]\d+|[-+0-9.]+)')

def parse_float(text):
    """String'den float değer çıkar"""
    match = num_re.match(text)
    return float(match.group(0)) if match else 0.0

def setup_battery_mode(inst):
    """Battery test mode'a geç"""
    print("Battery test mode hazırlanıyor...")
    
    # Önce mevcut testleri durdur
    try:
        inst.write(':BATT:TEST:ABORT')
        time.sleep(1)
    except:
        pass
    
    # Tüm çıkışları kapat
    inst.write(':OUTP OFF')
    inst.write(':BATT:OUTP OFF')
    time.sleep(1)
    
    # Battery function mode'a geç
    inst.write('*CLS')
    inst.write(':FUNC BATT')  # Battery mode
    time.sleep(1)
    
    # Battery test konfigürasyonu
    inst.write(':BATT:TYPE LI')  # Lithium ion
    inst.write(':BATT:CAP 1.0')  # 1Ah capacity (örnek)
    inst.write(':BATT:VOLT:TERM 2.5')  # Terminal voltage
    inst.write(':BATT:VOLT:MIN 2.0')   # Minimum voltage
    inst.write(':BATT:VOLT:MAX 4.2')   # Maximum voltage
    
    # Current limits
    inst.write(':BATT:CURR:DIS:MAX 2.0')  # Max discharge 2A
    inst.write(':BATT:CURR:CHAR:MAX 2.0') # Max charge 2A
    
    print("  - Battery mode konfigüre edildi")

def apply_current_battery_mode(inst, current_value):
    """Battery mode ile akım uygula"""
    
    if current_value > 0:
        # Pozitif akım: DEŞARJ
        inst.write(':BATT:TEST:STOP')  # Mevcut testi durdur
        time.sleep(0.2)
        
        # Discharge test başlat
        inst.write(f':BATT:CURR:DIS {current_value:.6f}')
        inst.write(':BATT:TEST:TYPE DISC')  # Discharge test
        inst.write(':BATT:TEST:START')
        
        mode = f'BATT_DISCHARGE({current_value:.3f}A)'
        
    else:
        # Negatif akım: ŞARJ  
        charge_current = abs(current_value)
        inst.write(':BATT:TEST:STOP')  # Mevcut testi durdur
        time.sleep(0.2)
        
        # Charge test başlat
        inst.write(f':BATT:CURR:CHAR {charge_current:.6f}')
        inst.write(':BATT:TEST:TYPE CHAR')  # Charge test
        inst.write(':BATT:TEST:START')
        
        mode = f'BATT_CHARGE({charge_current:.3f}A)'
    
    return mode

def get_battery_measurement(inst):
    """Battery mode ölçüm al"""
    try:
        # Battery test specific measurements
        voltage = float(inst.query(':BATT:MEAS:VOLT?'))
        current = float(inst.query(':BATT:MEAS:CURR?'))
        return voltage, current
    except:
        try:
            # Fallback to standard measurements
            voltage = float(inst.query(':MEAS:VOLT?'))
            current = float(inst.query(':MEAS:CURR?'))
            return voltage, current
        except:
            try:
                # Son fallback
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
    inst.timeout = 10000  # Battery mode için daha uzun timeout

    # CSV dosyasını yükle
    df = pd.read_csv(CSV_FILE)
    
    print(f"CSV yüklendi: {len(df)} veri noktası")
    print(f"Akım aralığı: {df['current'].min():.3f} A - {df['current'].max():.3f} A")
    print("BATTERY MODE: + akım = DEŞARJ, - akım = ŞARJ")

    # Kullanıcı seçimi
    choice = input("Test türü: (1) İlk 30 satır, (2) İlk 100 satır, (3) Tüm CSV: ")
    if choice == '1':
        df = df.head(30)
        print(f"İlk 30 satır seçildi")
    elif choice == '2':
        df = df.head(100)
        print(f"İlk 100 satır seçildi")
    else:
        print(f"Tüm {len(df)} satır işlenecek")

    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time', 'target_current', 'measured_current', 'measured_voltage', 'mode', 'battery_action'])

        try:
            # Battery mode setup
            setup_battery_mode(inst)
            
            # Battery output aç
            inst.write(':BATT:OUTP ON')
            time.sleep(2)  # Battery mode için daha uzun başlangıç

            t0 = time.time()
            
            for idx, row in df.iterrows():
                target_current = row['current']
                
                # Battery mode ile akım uygula
                mode = apply_current_battery_mode(inst, target_current)
                time.sleep(1.0)  # Battery test stabilizasyonu

                # Battery measurement al
                voltage, current = get_battery_measurement(inst)
                
                elapsed = time.time() - t0
                
                # Batarya perspektifinden işaretleme
                if target_current > 0:
                    # Pozitif hedef = deşarj
                    battery_current = abs(current)
                    action = "DEŞARJ"
                else:
                    # Negatif hedef = şarj
                    battery_current = -abs(current)
                    action = "ŞARJ"
                
                writer.writerow([elapsed, target_current, battery_current, voltage, mode, action])
                
                # Progress
                if (idx + 1) % 50 == 0:
                    print(f"İşlenen: {idx+1}/{len(df)} satır")
                
                # Hassasiyet hesabı
                if target_current != 0:
                    if target_current > 0:
                        accuracy = abs(battery_current - target_current) / abs(target_current) * 100
                    else:
                        accuracy = abs(abs(battery_current) - abs(target_current)) / abs(target_current) * 100
                else:
                    accuracy = 0.0
                
                print(f"{idx+1:3d}: {mode:25s} | Hedef {target_current:7.4f} A → Ölçülen {battery_current:7.4f} A ({action}), {voltage:.3f} V, Hata: {accuracy:.1f}%")

                time.sleep(1.0)  # 1 Hz

        except KeyboardInterrupt:
            print("\nTest kullanıcı tarafından durduruldu.")
        except Exception as e:
            print(f"Hata: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                # Battery mode cleanup
                inst.write(':BATT:TEST:STOP')
                inst.write(':BATT:TEST:ABORT')
                inst.write(':BATT:OUTP OFF')
                inst.write(':OUTP OFF')
                inst.write('SYST:LOC')
            except:
                pass
            inst.close()
            rm.close()
            print("Cihaz güvenli durumda kapatıldı.")
            print(f"Sonuçlar kaydedildi: {LOG_FILE}")

if __name__ == "__main__":
    main() 