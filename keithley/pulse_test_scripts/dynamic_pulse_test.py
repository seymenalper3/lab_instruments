#!/usr/bin/env python3
import time
import csv
import pyvisa

# --------- Kullanıcıdan Gelen Parametreler ---------
PULSE_CURRENT   = 1.0           # A  (darbe akımı)
VOLTAGE_LIMIT   = 3.0           # V  (gerilim limiti)
PULSE_DURATION  = 5 * 60        # s  (5 dk darbe)
IDLE_DURATION   = 5 * 60        # s  (5 dk bekleme)
NUM_PULSES      = 4             # Toplam darbe sayısı
POLL_INTERVAL   = 1.0           # s  (ölçüm aralığı)
OUTPUT_CSV      = "dynamic_pulse_test.csv"
# ----------------------------------------------------

# VISA üzerinden enstrümana bağlan
rm   = pyvisa.ResourceManager()
inst = rm.open_resource('USB0::1510::8833::4587429::0::INSTR')  # Cihaz IP/port'unu güncelleyin

# 1. Temiz başlangıç ve remote moda geç
inst.write('*CLS; SYST:REM')

# 2. Power-supply (source) moduna al ve darbe parametrelerini ayarla
inst.write('SOUR:FUNC CURR')                       # Kaynak fonksiyonu = Akım
inst.write(f'SOUR:CURR {PULSE_CURRENT}')            # Kaynak akımı = 1 A
inst.write(f'SOUR:VOLT {VOLTAGE_LIMIT}')            # Gerilim limiti = 3 V

# Ölçümlerde hem V hem A sorgulayacağız, bu yüzden ölçüm fonksiyonu ayarı gerek yok

data = []

for pulse_idx in range(1, NUM_PULSES + 1):
    # 3. Darbeyi başlat
    inst.write('OUTP ON')

    # 4. Darbe süresi boyunca ölçüm döngüsü
    t0 = time.time()
    while (time.time() - t0) < PULSE_DURATION:
        elapsed = time.time() - t0
        v = float(inst.query('MEAS:VOLT?'))        # Anlık voltaj
        a = float(inst.query('MEAS:CURR?'))        # Anlık akım
        data.append([pulse_idx, 'pulse', elapsed, v, a])
        time.sleep(POLL_INTERVAL)

    # 5. Darbeyi durdur
    inst.write('OUTP OFF')

    # 6. Bekleme periyodu boyunca ölçüm döngüsü
    t1 = time.time()
    while (time.time() - t1) < IDLE_DURATION:
        elapsed = time.time() - t1
        v = float(inst.query('MEAS:VOLT?'))
        a = float(inst.query('MEAS:CURR?'))
        data.append([pulse_idx, 'idle', elapsed, v, a])
        time.sleep(POLL_INTERVAL)

# 7. Sonuçları CSV dosyasına yaz
with open(OUTPUT_CSV, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Pulse_No', 'Phase', 'Elapsed_s', 'Voltage_V', 'Current_A'])
    writer.writerows(data)

print(f"Test tamamlandı, sonuçlar '{OUTPUT_CSV}' dosyasına kaydedildi.")
