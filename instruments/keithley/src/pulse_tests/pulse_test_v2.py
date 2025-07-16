#!/usr/bin/env python3
# pulse_discharge_2281s_v2.3.py
import pyvisa, time, csv, datetime

PULSES, ON_S, OFF_S = 4, 600, 600      # 10 dk darbe / 10 dk dinlenme
STEP,  I_LIM_A, V_CUT = 5, 1.0, 3.0    # 5 s örnekleme

rm   = pyvisa.ResourceManager('@py')
inst = rm.open_resource('USB0::1510::8833::4587429::0::INSTR')
inst.read_termination = inst.write_termination = '\n'
inst.timeout = 8000                    # 8 s güvenli pay

def w(c): inst.write(c); print('[W]', c)
def q(c): r = inst.query(c).strip(); print('[Q]', c, '=>', r); return r

def last_IV():
    v, i, t = map(float,
        q(':BATT:DATA:DATA? "VOLT,CURR,TIME",LAST').split(','))
    return v, i, t                # Volt   Amp   cihaz REL-time (s)

try:
    #———— Cihazı ayarla ——————————————————————————
    w('*CLS');             w('SYST:REM')
    inst.write(':ENTR:FUNC TEST') 
    w(':BATT:TEST:MODE DIS')
    w(f':BATT:TEST:CURR:LIM:SOUR {I_LIM_A}')
    w(f':BATT:TEST:VOLT {V_CUT}')
    w(':BATT:TEST:SENS:SAMP:INT 5')   # 5 s örnekleme
    w(':BATT:DATA:CLE')

    fname = f"pulse_discharge_{datetime.date.today()}.csv"
    with open(fname,'w',newline='',buffering=1) as f:
        wr = csv.writer(f); wr.writerow(['elapsed_s','volt_v','curr_a'])
        t0 = time.time()

        for n in range(1, PULSES+1):
            print(f'>>> {n}. darbe – {I_LIM_A} A sink')
            w(':BATT:OUTP ON')
            tend = time.time()+ON_S
            while time.time()<tend:
                time.sleep(STEP)
                V,I,_ = last_IV()
                wr.writerow([f'{time.time()-t0:.1f}', f'{V:.6f}', f'{I:.6f}'])

            print(f'>>> dinlenme {OFF_S}s')
            w(':BATT:OUTP OFF')
            tend = time.time()+OFF_S
            while time.time()<tend:
                time.sleep(STEP)
                V,I,_ = last_IV()        # I≈0 A, V toparlanıyor
                wr.writerow([f'{time.time()-t0:.1f}', f'{V:.6f}', f'{I:.6f}'])

    print(f'✓ Test tamam – veriler “{fname}” dosyasında.')

finally:
    w(':BATT:OUTP OFF'); w('SYST:LOC')
    inst.close(); rm.close()
    print('Cihaz local moda alındı, oturum kapatıldı.')
