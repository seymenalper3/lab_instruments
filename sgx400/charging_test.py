import socket
import time
import csv
from datetime import datetime

class SGXController:
    def __init__(self, ip="169.254.134.194", port=9221):
        self.ip = ip
        self.port = port
        self.socket = None
        
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))
        # Socket timeout ekle
        self.socket.settimeout(15.0)
        
    def send_command(self, command):
        self.socket.send((command + '\n').encode())
        time.sleep(0.2)  # Kısa bekleme
        
    def query(self, command):
        self.socket.send((command + '\n').encode())
        time.sleep(0.3)  # Komut işlenmesi için bekle
        response = self.socket.recv(1024).decode().strip()
        return response
        
    def disconnect(self):
        if self.socket:
            self.socket.close()

def safety_check(sgx):
    print("=== GÜVENLİK KONTROLÜ ===")
    
    try:
        # Cihaz bilgilerini al
        device_info = sgx.query("*IDN?")
        print(f"Cihaz: {device_info}")
        
        # Çıkışın kapalı olduğunu kontrol et
        output_state = sgx.query("OUTP:STAT?")
        print(f"Çıkış durumu: {'AÇIK' if output_state == '1' else 'KAPALI'}")
        
        # Mevcut voltaj/akım kontrolü
        current_volt = float(sgx.query("MEAS:VOLT?"))
        current_curr = float(sgx.query("MEAS:CURR?"))
        print(f"Mevcut V: {current_volt}V, I: {current_curr}A")
        
        # Ayarlanan değerleri kontrol et
        set_volt = float(sgx.query("SOUR:VOLT?"))
        set_curr = float(sgx.query("SOUR:CURR?"))
        print(f"Ayarlanan V: {set_volt}V, I: {set_curr}A")
        
        print("=" * 25)
        
        # Güvenlik onayı
        if output_state == '1':
            print("⚠️  UYARI: Çıkış şu anda AÇIK!")
            return False
        else:
            print("✅ Güvenlik kontrolü: TAMAM")
            return True
            
    except Exception as e:
        print(f"❌ Güvenlik kontrolü hatası: {e}")
        return False

def charging_experiment(sgx, voltage, current_limit, duration_minutes):
    # CSV dosyası hazırlığı
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"charging_test_{timestamp}.csv"
    
    print(f"\n=== ŞARJ TESTİ BAŞLATILIYOR ===")
    print(f"Hedef Voltaj: {voltage}V")
    print(f"Akım Limiti: {current_limit}A")
    print(f"Test Süresi: {duration_minutes} dakika ({duration_minutes * 60} saniye)")
    print(f"CSV Dosyası: {filename}")
    print("-" * 50)
    
    try:
        # Test parametrelerini ayarla
        sgx.send_command(f"SOUR:VOLT {voltage}")
        sgx.send_command(f"SOUR:CURR {current_limit}")
        
        # CSV dosyası oluştur ve başlıkları yaz
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Time(s)', 'Voltage(V)', 'Current(A)', 'Power(W)', 'Timestamp'])
        
        print("Parametreler ayarlandı, 2 saniye sonra çıkış açılacak...")
        time.sleep(2)
        
        sgx.send_command("OUTP:STAT ON")  # Çıkışı aç
        print("✅ Çıkış AÇILDI - Test başladı!")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        measurement_count = 0
        
        while time.time() < end_time:
            current_time = time.time() - start_time
            
            try:
                # Ölçüm al
                voltage_read = float(sgx.query("MEAS:VOLT?"))
                current_read = float(sgx.query("MEAS:CURR?"))
                power_read = voltage_read * current_read
                timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                
                # Terminal çıktısı
                print(f"T:{current_time:6.1f}s | V:{voltage_read:6.3f}V | I:{current_read:6.3f}A | P:{power_read:6.3f}W")
                
                # CSV'ye kaydet
                with open(filename, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([round(current_time, 1), voltage_read, current_read, power_read, timestamp_str])
                
                measurement_count += 1
                
            except Exception as e:
                print(f"❌ Ölçüm hatası: {e}")
            
            time.sleep(1)  # 1 saniye aralıklarla ölçüm
            
        print(f"\n✅ Test süresi tamamlandı! Toplam {measurement_count} ölçüm alındı.")
            
    except KeyboardInterrupt:
        print("\n⚠️  Test kullanıcı tarafından durduruldu!")
    
    except Exception as e:
        print(f"❌ Test hatası: {e}")
    
    finally:
        # Güvenlik için çıkışı kapat
        try:
            sgx.send_command("OUTP:STAT OFF")
            print("✅ Çıkış KAPATILDI.")
        except:
            print("❌ Çıkış kapatma hatası!")
        
        print(f"📁 Veriler kaydedildi: {filename}")

# Kullanım örneği
if __name__ == "__main__":
    sgx = SGXController()
    
    try:
        sgx.connect()
        print("✅ SGX bağlantısı kuruldu!")
        
        # Güvenlik kontrolü
        if not safety_check(sgx):
            print("❌ Güvenlik kontrolü başarısız! Test durduruluyor.")
            exit()
        
        # Test parametreleri - daha uzun test için
        voltage = 50.0       # Düşük voltaj ile başla
        current_limit = 5 # Düşük akım limiti
        duration = 1      # 6 saniye test (0.1 dakika)
        
        print(f"\nTest parametreleri:")
        print(f"Voltaj: {voltage}V, Akım Limiti: {current_limit}A, Süre: {duration} dakika")
        
        # Otomatik test başlatma
        charging_experiment(sgx, voltage, current_limit, duration)
        
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        # Son güvenlik kontrolü
        try:
            sgx.send_command("OUTP:STAT OFF")  # Çıkışı kapat
            print("🔒 Güvenlik: Çıkış kapatıldı.")
        except:
            pass
        sgx.disconnect()
        print("🔌 Bağlantı kapatıldı.")
