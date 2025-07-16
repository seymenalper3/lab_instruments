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

# ── Cihaz Bağlantısı ─────────────────────────────────────────────────────────
rm   = pyvisa.ResourceManager('@py')
inst = rm.open_resource('USB0::1510::8833::4587429::0::INSTR')
inst.read_termination  = inst.write_termination = '\n'
inst.timeout           = 5000  # 5 s komut zaman aşımı

# ── Demo Ayarları ────────────────────────────────────────────────────────────
model_name = "DemoModel"
slot       = 6  # İç bellekte saklanacak slot numarası

try:
    # 1) Temiz başlangıç
    w(inst, '*CLS')
    w(inst, 'SYST:REM')
    w(inst, ':TRACe:CLEar')              # Buffer’ı temizler fileciteturn13file7

    # 2) Kısa kısmi deşarj
    w(inst, ':BATT:TEST:MODE DIS')
    w(inst, ':BATT:TEST:VOLT 3.5')
    w(inst, ':BATT:TEST:CURR:END 0.5')
    w(inst, ':BATT:OUTP ON')
    q(inst, '*OPC?')
    w(inst, ':BATT:OUTP OFF')

    # 3) Hızlı AH-ESR ölçüm başlatma
    w(inst, ':BATT:TEST:SENS:AH:VFUL 4.20')
    w(inst, ':BATT:TEST:SENS:AH:ILIM 1.00')
    w(inst, ':BATT:TEST:SENS:AH:ESRInterval S1')
    w(inst, ':BATT:OUTP ON')
    w(inst, ':BATT:TEST:SENS:AH:EXEC STAR')

    # 4) Otomatik durdurma
    print("Demo ölçüm için 15 s bekleniyor…")
    time.sleep(60)
    w(inst, ':BATT:TEST:SENS:AH:EXEC STOP')

    # 5) Model aralığı ve kaydetme
    w(inst, ':BATT:TEST:SENS:AH:GMOD:RANG 3.5,4.10')
    w(inst, f':BATT:TEST:SENS:AH:GMOD:SAVE:INTernal {slot}')
    q(inst, '*OPC?')

    # 6) Buffer’daki nokta sayısı
    points = int(inst.query(':TRACe:POINts:ACTual?').strip())
    print(f"Buffer'da bulunan nokta sayısı: {points}")

    # 7) Model verilerini CSV’e yazma
    csv_filename = f'battery_model_{slot}.csv'
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

finally:
    # Temizlik ve lokal moda dönüş
    w(inst, ':BATT:OUTP OFF')
    w(inst, 'SYST:LOC')
    inst.close(); rm.close()
    print("Demo tamamlandı, cihaz lokal moda alındı.")
