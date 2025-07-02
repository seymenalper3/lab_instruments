#timeout yok, bloklama kullanıyor, henüz denemedim
#!/usr/bin/env python3
import time, pyvisa, csv

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

# ── Parametreler ─────────────────────────────────────────────────────────────
DISCH_VOL       = 3.00    # V-empty (deşarj sonu)
DISCH_CURR_END  = 1.00    # Deşarj sonu akımı (A)
AH_VFULL        = 4.20    # V-full (şarj üst sınırı)
AH_ILIMIT       = 1.00    # Şarj akım limiti (A)
AH_ESR_INTERVAL = 30      # ESR ölçüm aralığı (s)
MODEL_SLOT      = 4       # Internal’e kaydedilecek slot
CSV_FILE        = f'battery_model_{MODEL_SLOT}.csv'

try:
    # 1) Cihazı sıfırla
    w(inst, '*CLS')
    w(inst, 'SYST:REM')
    w(inst, ':BATT1:DATA:CLEar')

    # 2) Tam deşarj → SOC=0%
    w(inst, ':BATT:TEST:MODE DIS')
    w(inst, f':BATT:TEST:VOLT {DISCH_VOL}')
    w(inst, f':BATT:TEST:CURR:END {DISCH_CURR_END}')
    w(inst, ':BATT:OUTP ON')
    q(inst, ':STAT:OPER:INST:ISUM:COND?')    # Deşarj bitene kadar bloklar
    w(inst, ':BATT:OUTP OFF')

    # 3) Tam şarj + A-H/ESR ölçümü → SOC 0→100%
    w(inst, f':BATT:TEST:SENS:AH:VFUL {AH_VFULL}')
    w(inst, f':BATT:TEST:SENS:AH:ILIM {AH_ILIMIT}')
    w(inst, f':BATT:TEST:SENS:AH:ESRInterval S{AH_ESR_INTERVAL}')
    w(inst, ':BATT:TEST:SENS:AH:EXEC STAR')
    q(inst, ':STAT:OPER:INST:ISUM:COND?')    # Ölçüm bitene kadar bloklar

    # 4) Model aralığı belirle & kaydet
    w(inst, f':BATT:TEST:SENS:AH:GMOD:RANG {DISCH_VOL},{AH_VFULL}')    # Voc aralığı :contentReference[oaicite:0]{index=0}
    w(inst, f':BATT:TEST:SENS:AH:GMOD:SAVE:INTernal {MODEL_SLOT}')   # Internal’e kaydet :contentReference[oaicite:1]{index=1}
    q(inst, '*OPC?')

    # 5) Model verilerini CSV’e dışa aktar
    #   – Önce buffer’da kaç nokta var sorgula
    points = int(q(inst, ':TRACe:POINts:ACTual?'))  # Mevcut nokta sayısı :contentReference[oaicite:2]{index=2}

    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['SOC (%)', 'VOLT (V)', 'ESR (Ω)'])
        for i in range(points):
            resp = q(inst, f':BATTery:MODel{MODEL_SLOT}:ROW{i}?')  # Her satır için Voc,ESR :contentReference[oaicite:3]{index=3}
            voc, esr = map(float, resp.split(','))
            soc = i * 100.0 / (points - 1)
            writer.writerow([soc, voc, esr])
    print(f"Model verileri '{CSV_FILE}' dosyasına kaydedildi.")

finally:
    # Temizlik ve lokal moda dönüş
    w(inst, ':BATT:OUTP OFF')
    w(inst, 'SYST:LOC')
    inst.close()
    rm.close()
    print("İşlem tamamlandı, cihaz lokal moda alındı.")
