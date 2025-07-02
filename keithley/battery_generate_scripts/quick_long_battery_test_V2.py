#!/usr/bin/env python3
import time, pyvisa
import csv

# ── Yardımcı fonksiyonlar ────────────────────────────────────────────────────
def w(inst, cmd):
    inst.write(cmd)
    print("[W]", cmd)

def q(inst, cmd):
    r = inst.query(cmd).strip()
    print("[Q]", cmd, "=>", r)
    return r

def wait_measurement_complete(inst, max_hours=8, poll_interval=60):
    """
    Demo'daki gibi ama gerçek ölçüm için: measurement bit kontrol ederek bekle
    """
    max_seconds = max_hours * 3600
    start_time = time.time()
    
    print(f"Ölçüm başladı. Maksimum {max_hours*60:.0f} dakika beklenecek...")
    print("İlerleme durumu raporlanacak.")
    
    # İlk voltaj okuma
    try:
        voltage = float(q(inst, ':BATT:VOLT?'))
        print(f"Başlangıç voltajı: {voltage:.3f}V")
    except:
        print("Başlangıç voltajı okunamadı")
    
    while True:
        # Measurement durumu kontrol et
        cond = int(q(inst, ':STAT:OPER:INST:ISUM:COND?'))
        
        # Mevcut voltajı da göster
        try:
            voltage = float(q(inst, ':BATT:VOLT?'))
            current = float(q(inst, ':BATT:CURR?'))
            print(f"V: {voltage:.3f}V, I: {current:.3f}A, Status: {cond}")
        except:
            pass
            
        if cond & 0x10 == 0:  # bit-4 temizlendi = ölçüm bitti
            elapsed = time.time() - start_time
            print(f"Ölçüm tamamlandı! Toplam süre: {elapsed/60:.1f} dakika")
            return
        
        # Zaman kontrolü
        elapsed = time.time() - start_time
        if elapsed > max_seconds:
            raise TimeoutError(f"Ölçüm {max_hours*60:.0f} dakikayı aştı!")
        
        # İlerleme raporu
        minutes = elapsed / 60
        print(f"Geçen süre: {minutes:.1f} dakika - Ölçüm devam ediyor...")
        
        time.sleep(poll_interval)

# ── Cihaz Bağlantısı ─────────────────────────────────────────────────────────
rm   = pyvisa.ResourceManager('@py')
inst = rm.open_resource('USB0::1510::8833::4587429::0::INSTR')
inst.read_termination  = inst.write_termination = '\n'
inst.timeout           = 5000  # 5 s komut zaman aşımı

# ── Gerçek Test Ayarları ─────────────────────────────────────────────────────
model_name = "QuickTestModel"
slot       = 6  # İç bellekte saklanacak slot numarası

# 10 dakikalık hızlı test parametreleri
discharge_voltage = 3.3    # Daha düşük voltaj (3.5V'dan çok az fark vardı)
discharge_current = 0.5    # Daha düşük akım (pil koruması için)
full_voltage = 4.00        # Daha düşük şarj limiti = daha hızlı şarj
current_limit = 1.00       # Daha yüksek şarj akımı = daha hızlı
esr_interval = 5           # Daha sık ölçüm = daha az bekleme

try:
    # 1) Temiz başlangıç (demo ile aynı)
    w(inst, '*CLS')
    w(inst, 'SYST:REM')
    w(inst, ':TRACe:CLEar')              # Buffer'ı temizler

    # 2) Tam deşarj (demo'daki kısa deşarj yerine)
    print("=== TAM DEŞARJ BAŞLATIYOR ===")
    w(inst, ':BATT:TEST:MODE DIS')
    w(inst, f':BATT:TEST:VOLT {discharge_voltage}')
    w(inst, f':BATT:TEST:CURR:END {discharge_current}')
    w(inst, ':BATT:OUTP ON')
    
    # Deşarj tamamlanana kadar bekle (max 5 dakika)
    wait_measurement_complete(inst, max_hours=0.08, poll_interval=10)
    w(inst, ':BATT:OUTP OFF')
    print("=== DEŞARJ TAMAMLANDI ===")

    # 3) Uzun süreli AH-ESR ölçüm başlatma (demo mantığı ile)
    print("=== AH-ESR KARAKTERIZASYON BAŞLATIYOR ===")
    w(inst, f':BATT:TEST:SENS:AH:VFUL {full_voltage}')
    w(inst, f':BATT:TEST:SENS:AH:ILIM {current_limit}')
    w(inst, f':BATT:TEST:SENS:AH:ESRInterval S{esr_interval}')
    w(inst, ':BATT:OUTP ON')
    w(inst, ':BATT:TEST:SENS:AH:EXEC STAR')

    # Otomatik tamamlanma bekleme (max 7 dakika)
    wait_measurement_complete(inst, max_hours=0.12, poll_interval=20)
    print("=== AH-ESR ÖLÇÜMÜ TAMAMLANDI ===")

    # 5) Model aralığı ve kaydetme (demo ile aynı mantık)
    print("=== MODEL OLUŞTURULUYOR ===")
    w(inst, f':BATT:TEST:SENS:AH:GMOD:RANG {discharge_voltage},{full_voltage}')
    w(inst, f':BATT:TEST:SENS:AH:GMOD:SAVE:INTernal {slot}')
    q(inst, '*OPC?')

    # 6) Buffer'daki nokta sayısı (demo ile aynı)
    points = int(inst.query(':TRACe:POINts:ACTual?').strip())
    print(f"Buffer'da bulunan nokta sayısı: {points}")

    # 7) Model verilerini CSV'e yazma (demo ile tamamen aynı)
    csv_filename = f'battery_model_{slot}_quick.csv'
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Başlık satırı
        writer.writerow(['SOC (%)', 'VOLT (V)', 'ESR (Ω)'])
        # Model her bir row indeksi için: Voc ve Res sorgusu
        for i in range(points):
            resp = inst.query(f':BATT:MOD{slot}:ROW{i}?').strip()
            voc_str, res_str = resp.split(',')
            voc = float(voc_str)
            esr = float(res_str)
            soc = i * 100.0 / (points - 1)
            writer.writerow([soc, voc, esr])
    print(f"Model verileri '{csv_filename}' dosyasına kaydedildi.")
    
    # 8) Özet bilgiler
    print("\n=== TEST ÖZET ===")
    print(f"Slot: {slot}")
    print(f"Deşarj voltajı: {discharge_voltage}V")
    print(f"Şarj voltajı: {full_voltage}V") 
    print(f"Toplam veri noktası: {points}")
    print(f"CSV dosyası: {csv_filename}")

finally:
    # Temizlik ve lokal moda dönüş (demo ile aynı)
    w(inst, ':BATT:OUTP OFF')
    w(inst, 'SYST:LOC')
    inst.close(); rm.close()
    print("Uzun test tamamlandı, cihaz lokal moda alındı.")
