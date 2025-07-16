import pyvisa

# PyVISA-py backend kullanarak ResourceManager oluşturuyoruz.
rm = pyvisa.ResourceManager('@py')

# Cihazınızın VISA kaynak ismini kullanarak bağlantı açın.
resource_string = 'USB0::1510::8833::4587429::0::INSTR'
instrument = rm.open_resource(resource_string)

# (Daha önce read ve write terminatörleri ayarlanmıştı)
instrument.read_termination = '\n'
instrument.write_termination = '\n'

# Eğer cihaz daha önce remote moda alınmışsa,
# yerel kontrol moduna geçmek için aşağıdaki komutu gönderin:
instrument.write("SYST:LOC")

# Durumu test etmek için tekrar *IDN? komutunu gönderebilirsiniz:
idn = instrument.query("*IDN?")
print("Cihaz Kimliği:", idn)
