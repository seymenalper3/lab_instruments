#!/usr/bin/env python3
# demo_pulse_trace_60s.py
#
# 2281S – Trace tamponu “ALW” modunda 6 × (5 s darbe + 5 s dinlenme)

import pyvisa, time, csv, datetime, re, sys

# ——— AYARLAR ———
PULSES      = 6          # 6 darbe-dinlenme çifti ≈ 60 s
PULSE_ON    = 5          # s – darbe süresi
PULSE_OFF   = 5          # s – dinlenme süresi
STEP_PRINT  = 1          # s – terminalde son örneği gösterme aralığı
I_LIM       = 1.0        # A – deşarj akım sınırı
SAMP_INT    = 0.5        # s – dahili örnekleme aralığı
TRACE_SIZE  = 300        # tampon kapasitesi (gerektiğinde 2-2500)

# ——— VISA ———
rm   = pyvisa.ResourceManager('@py')
inst = rm.open_resource('USB0::1510::8833::4587429::0::INSTR')   # adresinizi güncelleyin
inst.read_termination = inst.write_termination = '\n'
inst.timeout = 5000

def w(cmd): print('[W]', cmd); inst.write(cmd)
def q(cmd): r = inst.query(cmd).strip(); print('[Q]', cmd, '⇒', r); return r

num_re = re.compile(r'([-+0-9.E]+)')           # birimleri soy
def num(tok): m = num_re.match(tok); return float(m.group(1)) if m else float('nan')

# ——— CİHAZ HAZIRLIĞI ———
w('*CLS'); w('SYST:REM')
w(':FUNC TEST'); w(':BATT:TEST:MODE DIS')          # Batarya-test deşarj
w(f':BATT:TEST:CURR:LIM:SOUR {I_LIM}')
w(f':BATT:TEST:SENS:SAMP:INT {SAMP_INT}')
w(':SYST:AZER OFF')                                # hızlı okuma

w(':FORM:ELEM READ,MODE,REL')                      # I, V, Mode, t  seç :contentReference[oaicite:0]{index=0}

# — Trace tamponu —                                          ▼ kılavuz 7-191 → SENS
w(':TRAC:CLE')                                     # temizle
w(f':TRAC:POIN {TRACE_SIZE}')                      # kapasiteyi ayarla (isteğe bağlı) :contentReference[oaicite:1]{index=1}
w(':TRAC:FEED SENS')                               # ölçümleri tamponla :contentReference[oaicite:2]{index=2}
w(':TRAC:FEED:CONT ALW')                           # sürekli yaz (“ALW”) :contentReference[oaicite:3]{index=3}

# — Test döngüsü —
t0 = time.time()
for n in range(1, PULSES+1):
    # DARBE
    print(f'\n>>> {n}. DARBE — {PULSE_ON}s')
    w(':BATT:OUTP ON')
    t_end = time.time() + PULSE_ON
    while time.time() < t_end:
        time.sleep(STEP_PRINT)
        last = q(':TRAC:DATA:SEL? -1,-1,"READ,MODE,REL"')        # son örneği göster :contentReference[oaicite:4]{index=4}
    # DİNLENME
    w(':BATT:OUTP OFF')
    print(f'>>> Dinlenme — {PULSE_OFF}s')
    time.sleep(PULSE_OFF)

# ——— VERİYİ ÇEK & CSV’YE YAZ ———
data_raw = q(':TRAC:DATA? "READ,MODE,REL"')                       # tüm tamponu al :contentReference[oaicite:5]{index=5}
tokens   = [tok.strip() for tok in data_raw.split(',') if tok.strip()]

records = []
i = 0
while i + 3 < len(tokens):
    curr_tok, volt_tok, mode_tok, rel_tok = tokens[i:i+4]
    curr = num(curr_tok); volt = num(volt_tok); mode = mode_tok
    t_rel = num(rel_tok)
    records.append((t_rel, mode, volt, curr))
    i += 4

fname = f'demo_trace_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv'
with open(fname, 'w', newline='') as f:
    wr = csv.writer(f)
    wr.writerow(['elapsed_s', 'mode', 'volt_v', 'curr_a'])
    for row in records:
        wr.writerow([f'{row[0]:.3f}', row[1], f'{row[2]:.6f}', f'{row[3]:.6f}'])

print(f'\n✔ Trace tamponu {len(records)} satırla “{fname}” dosyasına aktarıldı.')

# — Temizlik —
w(':BATT:OUTP OFF'); w('SYST:LOC')
inst.close(); rm.close()
