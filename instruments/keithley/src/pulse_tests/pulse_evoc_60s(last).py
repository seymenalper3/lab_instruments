#sorunsuz çalışıyor. parametreler değiştirilip gerçek test yapılabilir
#!/usr/bin/env python3
# demo_pulse_evoc_60s.py  – 2281S Battery-Test / DIS
# 2 × (30 s pulse + 30 s rest)  →  iki CSV  (ortak zaman)

import pyvisa, time, csv, datetime, re, sys

# —— parametreler ——
PULSES, PULSE_T, REST_T  = 2, 30, 30
# Keithley 2281S Battery Test mode: discharges at ~1A, no variable discharge current
I_PULSE, I_REST          = 1.0, 0.0001                  # A  
SAMP_INT, STEP, EVOC_DLY = 0.5, 0.5, 0.05
num = re.compile(r'[-+0-9.E]+'); fnum = lambda t: float(num.match(t).group())

# —— VISA ——
rm  = pyvisa.ResourceManager('@py')
inst= rm.open_resource('USB0::1510::8833::4587429::0::INSTR')
inst.read_termination = inst.write_termination = '\n'; inst.timeout = 5000
w = lambda c:(inst.write(c),print('[W]',c))
def q(c):
    r = inst.query(c).strip()
    print('[Q]',c,'⇒',r)
    return r

# —— hazırlık ——
w('*CLS'); w('SYST:REM')
w(':FUNC TEST');                         w(':BATT:TEST:MODE DIS')
w(f':BATT:TEST:SENS:SAMP:INT {SAMP_INT}')
w(f':BATT:TEST:SENS:EVOC:DELA {EVOC_DLY}')
w(':FORM:UNITS OFF');                    w(':SYST:AZER OFF')

# data logger
w(':BATT:DATA:CLE');                     w(':BATT:DATA:STAT ON')
w(':BATT:TEST:EXEC STAR')

# —— yardımcı ——
def last_vi():
    """tam tamponu al, son (V,I,REL) değerlerini döndür"""
    buf = q(':BATT:DATA:DATA? "VOLT,CURR,REL"')
    if not buf:              # boş dizge
        return None, None, None
    vals = list(map(float, buf.split(',')[-3:]))  # son üç sayı
    v, i, rel = vals
    return v, i, rel

# —— CSV dosyaları ——
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
fpulse = open(f'pulse_bt_{stamp}.csv','w',newline=''); wp = csv.writer(fpulse)
frest  = open(f'rest_evoc_{stamp}.csv','w',newline=''); wr = csv.writer(frest)
wp.writerow(['t_rel_s','volt_v','curr_a'])
wr.writerow(['t_rel_s','voc_v','esr_ohm'])
t0 = time.time()                           # ortak referans

try:
    for cyc in range(1, PULSES+1):

        # —— PULSE (Direct on/off for Keithley 2281S) ——
        # Keithley 2281S Battery Test mode discharges at ~1A regardless of current setting
        w(f':BATT:TEST:CURR:LIM:SOUR {I_PULSE}')
        w(':BATT:OUTP ON')
        print(f'>>> {cyc}. PULSE — {PULSE_T}s @ ~1A (Battery Test mode)')
        end = time.time()+PULSE_T
        while time.time()<end:
            v,i,rel = last_vi()
            if v is not None: wp.writerow([f'{rel:.3f}',f'{v:.6f}',f'{i:.6f}']); fpulse.flush()
            time.sleep(STEP)

        # —— REST + EVOC ——
        w(':BATT:OUTP OFF');   w(f':BATT:TEST:CURR:LIM:SOUR {I_REST}')
        print(f'>>> Dinlenme — {REST_T}s')
        end = time.time()+REST_T
        while time.time()<end:
            esr,voc = map(float,q(':BATT:TEST:MEAS:EVOC?').split(','))
            wr.writerow([f'{time.time()-t0:.3f}',f'{voc:.6f}',f'{esr:.6f}']); frest.flush()
            time.sleep(STEP)

finally:
    w(':BATT:OUTP OFF'); w('SYST:LOC')
    fpulse.close(); frest.close()
    inst.close(); rm.close()

print('\n✔ PULSE CSV →', fpulse.name)
print('✔ REST  CSV →', frest.name)
