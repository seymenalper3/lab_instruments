#model oluşturma başlatmaz. daha önce yapılmış ölçümleri dışa aktarmak için

#!/usr/bin/env python3
import time, csv, pyvisa, sys

RESOURCE   = 'USB0::1510::8833::4587429::0::INSTR'
MODEL_SLOT = 4                        # istediğiniz slot
CSV_FILE   = f"battery_model_{MODEL_SLOT}.csv"
RANGE_LOW, RANGE_HIGH = 2.5, 4.2
POLL_S   = 10                         # ölçüm beklerken anket süresi
TMAX_MEAS_S = 8 * 3600                # ölçüm için maks 8 saat

# ── I/O kısayolları ───────────────────────────────────────────────────────────
def w(inst, cmd):  inst.write(cmd);  print("[W]", cmd)
def q(inst, cmd):  r = inst.query(cmd).strip(); print("[Q]", cmd, "→", r); return r
def busy(inst):
    """Measurement bit-4 set mi?"""
    return int(q(inst, ':STAT:OPER:INST:ISUM:COND?')) & 0x10

# ── Uzun işlemler için bekleme fonksiyonları ─────────────────────────────────
def wait_measure_finish(inst, tmax):
    t0 = time.time()
    while busy(inst):
        if time.time() - t0 > tmax:
            raise TimeoutError("Measurement süresi aştı.")
        time.sleep(POLL_S)

def wait_opc(inst, note="İşlem"):
    """*OPC? ile 'işlem tamam' bekle – 60 s timeout"""
    inst.timeout = 60000
    done = q(inst, '*OPC?')
    if done != '1':
        raise TimeoutError(f"{note} zaman aşımına uğradı.")
    inst.timeout = 5000

# ── Modeli CSV’ye dışa aktar ─────────────────────────────────────────────────
def export_model(inst, slot, csv_path):
    w(inst, f':BATT:MOD:RCL {slot}')
    rows = []
    for i in range(101):
        resp = q(inst, f':BATT:MOD{slot}:ROW{i}?')
        if resp:
            voc, esr = map(float, resp.split(','))
            rows.append([i, voc, esr])
    if rows:
        with open(csv_path, 'w', newline='') as f:
            csv.writer(f).writerows([['Step', 'Voc (V)', 'ESR (Ω)']] + rows)
        print(f">>> {len(rows)} satır {csv_path} dosyasına yazıldı.")
    else:
        print(">>> Model verisi bulunamadı!")

# ── Ana akış ─────────────────────────────────────────────────────────────────
rm   = pyvisa.ResourceManager('@py')
inst = rm.open_resource(RESOURCE)
inst.read_termination = inst.write_termination = '\n'
inst.timeout          = 5000

try:
    w(inst, 'SYST:REM')                     # uzak kontrol

    # 1) Ölçüm hâlâ sürüyor mu?
    if busy(inst):
        if q(inst, ':OUTP?') == '0':        # PAUSE → devam ettir
            print(">>> Ölçüm duraklatılmış. Devam ediliyor…")
            w(inst, ':BATT:OUTP ON')
            w(inst, ':BATT:TEST:SENS:AH:EXEC CONT')
        else:
            print(">>> Ölçüm zaten çalışıyor. Bekleniyor…")

        wait_measure_finish(inst, TMAX_MEAS_S)
        print(">>> Ölçüm tamamlandı.")

    else:
        print(">>> Ölçüm zaten bitmiş görünüyor.")

    # 2) Modeli kaydet
    w(inst, f':BATT:TEST:SENS:AH:GMOD:RANG {RANGE_LOW},{RANGE_HIGH}')
    w(inst, f':BATT:TEST:SENS:AH:GMOD:SAVE:INT {MODEL_SLOT}')
    wait_opc(inst, "Model kaydetme")        # *OPC? bekle
    print(f">>> Model slot-{MODEL_SLOT} içine kaydedildi.")

    # Slot listesini güvenle sorgula
    slots = q(inst, ':BATT:TEST:SENS:AH:GMOD:CAT?')
    print(">>> Dolular:", slots)

    # 3) Dışa aktar
    export_model(inst, MODEL_SLOT, CSV_FILE)

except Exception as e:
    print("HATA:", e, file=sys.stderr)

finally:
    try:  w(inst, ':BATT:OUTP OFF')
    except pyvisa.VisaIOError: pass
    w(inst, 'SYST:LOC')
    inst.close(); rm.close()
    print(">>> Yerel moda dönüldü, oturum kapatıldı.")
