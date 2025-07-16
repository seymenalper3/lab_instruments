import pyvisa

# PyVISA-py backend kullanılarak ResourceManager oluşturuluyor.
rm = pyvisa.ResourceManager('@py')

# Cihazın VISA kaynak ismini belirtin (önceden test ettiğimiz kaynak).
resource_string = 'USB0::1510::8833::4587429::0::INSTR'
instrument = rm.open_resource(resource_string)

# Okuma ve yazma terminatörlerini ayarla (genellikle '\n' kullanılır).
instrument.read_termination = '\n'
instrument.write_termination = '\n'

# Cihazın durumu sıfırlanabilir (opsiyonel)
instrument.write("*CLS")

# Cihazı remote moda almak için SYST:REM komutunu gönderin.
instrument.write("SYST:REM")

# Cihazın remote modda olduğunu doğrulamak için kimlik sorgulaması yapın.
idn = instrument.query("*IDN?")
print("Cihaz Kimliği:", idn)

