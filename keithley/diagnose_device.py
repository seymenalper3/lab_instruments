#!/usr/bin/env python3
"""
Keithley 2281S Tanı Scripti
Cihazın mevcut durumunu detaylı analiz eder
"""

import pyvisa
import time

RESOURCE = 'USB0::1510::8833::4587429::0::INSTR'

def diagnose():
    rm = pyvisa.ResourceManager('@py')
    inst = rm.open_resource(RESOURCE)
    inst.read_termination = inst.write_termination = '\n'
    inst.timeout = 5000

    try:
        print("=== KEİTHLEY 2281S TANI ===")
        
        # Kimlik
        idn = inst.query('*IDN?').strip()
        print(f"Cihaz: {idn}")
        
        print("\n1. TEMEL DURUM:")
        try:
            func = inst.query(':FUNC?').strip()
            print(f"   Fonksiyon: {func}")
        except:
            print("   Fonksiyon: Sorgulanamadı")
        
        try:
            output = inst.query(':OUTP?').strip()
            print(f"   Ana Çıkış: {'ON' if output == '1' else 'OFF'}")
        except:
            print("   Ana Çıkış: Sorgulanamadı")
        
        try:
            batt_output = inst.query(':BATT:OUTP?').strip()
            print(f"   Batarya Çıkışı: {'ON' if batt_output == '1' else 'OFF'}")
        except:
            print("   Batarya Çıkışı: Sorgulanamadı")
        
        print("\n2. BATARYA TEST DURUMU:")
        try:
            test_mode = inst.query(':BATT:TEST:MODE?').strip()
            print(f"   Test Modu: {test_mode}")
        except:
            print("   Test Modu: Sorgulanamadı")
        
        try:
            status = inst.query(':STAT:OPER:INST:ISUM:COND?').strip()
            status_int = int(status)
            measuring = bool(status_int & 0x10)
            print(f"   Status Register: {status}")
            print(f"   Ölçüm Aktif: {'EVET' if measuring else 'HAYIR'}")
        except:
            print("   Status: Sorgulanamadı")
        
        print("\n3. SOURCE MOD AYARLARI:")
        try:
            sour_func = inst.query(':SOUR:FUNC?').strip()
            print(f"   Source Fonksiyon: {sour_func}")
        except:
            print("   Source Fonksiyon: Sorgulanamadı")
        
        try:
            sour_curr = inst.query(':SOUR:CURR?').strip()
            print(f"   Source Akım: {sour_curr} A")
        except:
            print("   Source Akım: Sorgulanamadı")
        
        try:
            sour_volt = inst.query(':SOUR:VOLT?').strip()
            print(f"   Source Voltaj: {sour_volt} V")
        except:
            print("   Source Voltaj: Sorgulanamadı")
        
        print("\n4. MEVCUT ÖLÇÜMLER:")
        # READ komutu
        try:
            response = inst.query(':READ?').strip()
            parts = response.split(',')
            if len(parts) >= 2:
                current = float(parts[0])
                voltage = float(parts[1])
                print(f"   READ: {current:.4f} A, {voltage:.3f} V")
        except Exception as e:
            print(f"   READ: Hata - {e}")
        
        # Buffer'dan okuma
        try:
            buffer_data = inst.query(':BATT:DATA:DATA:SEL? 1,1,"VOLT,CURR"').strip()
            print(f"   Buffer: {buffer_data}")
        except:
            print("   Buffer: Boş veya ulaşılamaz")
        
        print("\n5. TEST: AKIMI DEĞİŞTİRME")
        print("   Akımı 0.5A yapıyorum...")
        inst.write(':SOUR:CURR 0.5')
        time.sleep(2)
        
        try:
            response = inst.query(':READ?').strip()
            parts = response.split(',')
            if len(parts) >= 2:
                current = float(parts[0])
                voltage = float(parts[1])
                print(f"   Sonuç: {current:.4f} A, {voltage:.3f} V")
                if abs(current - 0.5) < 0.1:
                    print("   ✅ Akım komutu çalışıyor!")
                else:
                    print("   ❌ Akım komutu çalışmıyor!")
        except Exception as e:
            print(f"   Test sonucu: Hata - {e}")
        
        print("\n6. ÖNERİLER:")
        if measuring:
            print("   • Cihaz hâlâ ölçüm modunda, manuel olarak durdurulması gerekebilir")
        if batt_output == '1':
            print("   • Batarya çıkışı açık, kapatılması gerekebilir")
        print("   • Cihazın ön panelinden manuel reset denenebilir")
        print("   • Fiziksel batarya bağlantısı kontrol edilmeli")
        
    except Exception as e:
        print(f"Tanı hatası: {e}")
    finally:
        try:
            inst.write('SYST:LOC')
        except:
            pass
        inst.close()
        rm.close()

if __name__ == "__main__":
    diagnose() 