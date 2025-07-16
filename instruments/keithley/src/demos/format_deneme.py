#!/usr/bin/env python3
"""Test measurement format with output ON"""

import pyvisa
import time

rm = pyvisa.ResourceManager('@py')
inst = rm.open_resource('USB0::1510::8833::4587429::0::INSTR')
inst.read_termination = '\n'
inst.write_termination = '\n'
inst.timeout = 5000

print("Device ID:", inst.query('*IDN?').strip())

# Reset ve temel ayarlar
inst.write('*RST')
time.sleep(2)
inst.write('*CLS')

# Temel ayarlar
inst.write(':VOLT 3.7')
inst.write(':CURR 0.1')
inst.write(':VOLT:PROT 4.2')
inst.write(':CURR:PROT 1.5')

# Farklı ölçüm fonksiyonlarını test et
print("\n1. Testing with output OFF:")
inst.write(':OUTP OFF')
time.sleep(0.5)

# Sadece voltaj ölçmeyi dene
inst.write(':SENS:FUNC "VOLT"')
time.sleep(0.5)
try:
    response = inst.query(':MEAS:VOLT?')
    print(f"VOLT mode, MEAS:VOLT? -> {repr(response)}")
except Exception as e:
    print(f"VOLT mode, MEAS:VOLT? -> ERROR: {e}")

print("\n2. Testing with output ON:")
inst.write(':OUTP ON')
time.sleep(1)

# Tek tek modları test et
modes = [
    ('VOLT', ':MEAS:VOLT?'),
    ('CURR', ':MEAS:CURR?'),
    ('CONC', ':MEAS?'),
    ('CONC', ':MEAS:VOLT?'),
    ('CONC', ':MEAS:CURR?'),
    ('CONC', ':READ?')
]

for mode, cmd in modes:
    try:
        inst.write(f':SENS:FUNC "{mode}"')
        time.sleep(0.5)
        response = inst.query(cmd)
        print(f"{mode} mode, {cmd} -> {repr(response)}")
    except Exception as e:
        print(f"{mode} mode, {cmd} -> ERROR: {type(e).__name__}")

# Format elemanlarını test et
print("\n3. Testing format settings:")
inst.write(':SENS:FUNC "CONC"')
time.sleep(0.5)

# Format elemanlarını kontrol et
try:
    format_resp = inst.query(':FORM:ELEM?')
    print(f"Current format elements: {format_resp}")
except:
    pass

# Farklı format ayarları dene
formats = ['READ', 'VOLT', 'CURR', 'TIME', 'ALL']
for fmt in formats:
    try:
        inst.write(f':FORM:ELEM {fmt}')
        time.sleep(0.2)
        response = inst.query(':READ?')
        print(f"Format {fmt}: {repr(response)}")
    except Exception as e:
        print(f"Format {fmt}: ERROR")

# Çıkışı kapat
inst.write(':OUTP OFF')
inst.close()
rm.close()
