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
        """Cihaza bağlan"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.connect((self.ip, self.port))
        self.socket.settimeout(5.0)  # 5 saniye timeout
        print(f"✅ {self.ip}:{self.port} adresine bağlandı")
        
    def send_command(self, command):
        """Komut gönder (yanıt bekleme)"""
        try:
            # ⚡ ÖNEMLİ: \r\n kullan!
            self.socket.send((command + '\r\n').encode())
            time.sleep(0.1)  # Kısa bekleme
            return True
        except Exception as e:
            print(f"❌ Komut gönderme hatası: {e}")
            return False
    
    def query(self, command, timeout=2.0):
        """Komut gönder ve yanıt al"""
        try:
            # Buffer'ı temizle
            self.socket.settimeout(0.1)
            try:
                while True:
                    self.socket.recv(4096)
            except socket.timeout:
                pass
            
            # Normal timeout'a dön
            self.socket.settimeout(timeout)
            
            # ⚡ ÖNEMLİ: \r\n kullan!
            self.socket.send((command + '\r\n').encode())
            
            # Yanıt al
            response = b""
            while True:
                try:
                    chunk = self.socket.recv(1024)
                    response += chunk
                    # Yanıt \r\n ile bitiyorsa dur
                    if response.endswith(b'\r\n'):
                        break
                except socket.timeout:
                    break
            
            # Decode et ve temizle
            if response:
                return response.decode().strip()
            else:
                return "0.0"
                
        except Exception as e:
            print(f"❌ Query hatası ({command}): {e}")
            return "0.0"
    
    def get_voltage(self):
        """Gerilim ölçümü"""
        try:
            return float(self.query("MEAS:VOLT?"))
        except:
            return 0.0
    
    def get_current(self):
        """Akım ölçümü"""
        try:
            return float(self.query("MEAS:CURR?"))
        except:
            return 0.0
    
    def set_voltage(self, voltage):
        """Gerilim ayarla"""
        return self.send_command(f"SOUR:VOLT {voltage}")
    
    def set_current(self, current):
        """Akım limiti ayarla"""
        return self.send_command(f"SOUR:CURR {current}")
    
    def output_on(self):
        """Çıkışı aç"""
        return self.send_command("OUTP:STAT ON")
    
    def output_off(self):
        """Çıkışı kapat"""
        return self.send_command("OUTP:STAT OFF")
    
    def get_output_status(self):
        """Çıkış durumu"""
        try:
            return int(self.query("OUTP:STAT?"))
        except:
            return 0
    
    def disconnect(self):
        """Bağlantıyı kapat"""
        if self.socket:
            self.socket.close()
            print("🔌 Bağlantı kapatıldı")

def safety_check(sgx):
    """Güvenlik kontrolü"""
    print("\n=== GÜVENLİK KONTROLÜ ===")
    
    # Önce çıkışı kapat
    print("🔒 Güvenlik için çıkış kapatılıyor...")
    sgx.output_off()
    time.sleep(0.5)
    
    # Cihaz kimliği kontrolü
    print("🔍 Cihaz kimliği sorgulanıyor...")
    device_info = sgx.query("*IDN?")
    
    if device_info and ("SORENSEN" in device_info or "SGX" in device_info):
        print(f"✅ Cihaz bulundu: {device_info}")
        
        # Mevcut değerleri oku
        voltage = sgx.get_voltage()
        current = sgx.get_current()
        status = sgx.get_output_status()
        
        print(f"📊 Mevcut durum:")
        print(f"   Gerilim: {voltage:.3f} V")
        print(f"   Akım: {current:.3f} A")
        print(f"   Çıkış: {'AÇIK' if status else 'KAPALI'}")
        
        return True
    else:
        print(f"❌ Cihaz tanınamadı. Yanıt: {device_info}")
        return False

def load_test(sgx, voltage, current_limit, duration_minutes):
    """Yük testi - gelişmiş versiyon"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"load_test_{timestamp}.csv"
    
    print(f"\n=== YÜK TESTİ BAŞLIYOR ===")
    print(f"🔋 Test Gerilimi: {voltage} V")
    print(f"⚡ Akım Limiti: {current_limit} A")
    print(f"⏱️  Test Süresi: {duration_minutes} dakika")
    print(f"💾 Veri Dosyası: {filename}")
    print("=" * 50)
    
    # CSV başlığı oluştur
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Zaman(s)', 'Gerilim(V)', 'Akım(A)', 'Güç(W)', 'Durum', 'Tarih/Saat'])
    
    try:
        # Güvenli başlangıç
        print("\n🔧 Test parametreleri ayarlanıyor...")
        sgx.output_off()
        time.sleep(0.5)
        
        sgx.set_voltage(0)
        time.sleep(0.2)
        sgx.set_current(current_limit)
        time.sleep(0.2)
        
        # OVP ayarla (voltajın %110'u)
        ovp_value = voltage * 1.1
        sgx.send_command(f"SOUR:VOLT:PROT {ovp_value}")
        print(f"🛡️  OVP: {ovp_value:.1f} V")
        
        # Çıkışı aç
        print("🔌 Çıkış açılıyor...")
        sgx.output_on()
        time.sleep(1)
        
        # Voltajı kademeli artır
        print(f"\n📈 Gerilim kademeli olarak {voltage} V'a yükseltiliyor...")
        steps = 10
        for i in range(1, steps + 1):
            target_v = (voltage * i) / steps
            sgx.set_voltage(target_v)
            actual_v = sgx.get_voltage()
            actual_i = sgx.get_current()
            print(f"   Adım {i:2d}/{steps}: Hedef={target_v:6.2f}V, Ölçülen={actual_v:6.3f}V, {actual_i:6.3f}A")
            time.sleep(0.5)
        
        print("\n🚀 Ana test başladı!")
        print("=" * 70)
        print(f"{'Zaman':>8} | {'Gerilim':>10} | {'Akım':>10} | {'Güç':>10} | Durum")
        print("=" * 70)
        
        # Test döngüsü
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        measurement_count = 0
        error_count = 0
        
        while time.time() < end_time:
            loop_start = time.time()
            elapsed_time = loop_start - start_time
            
            # Ölçüm al
            v_measured = sgx.get_voltage()
            i_measured = sgx.get_current()
            p_calculated = v_measured * i_measured
            
            # Durum kontrolü
            if v_measured > 0 and abs(v_measured - voltage) < voltage * 0.1:
                status = "OK"
            elif v_measured == 0:
                status = "NO_OUTPUT"
                error_count += 1
            else:
                status = "WARNING"
            
            # Ekrana yazdır
            print(f"{elapsed_time:8.1f}s | {v_measured:10.3f}V | {i_measured:10.3f}A | {p_calculated:10.2f}W | {status}")
            
            # CSV'ye kaydet
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with open(filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    round(elapsed_time, 1), 
                    round(v_measured, 3), 
                    round(i_measured, 3), 
                    round(p_calculated, 2), 
                    status, 
                    timestamp_str
                ])
            
            measurement_count += 1
            
            # Döngü zamanlaması (1 Hz)
            loop_time = time.time() - loop_start
            if loop_time < 0.5:
                time.sleep(0.5 - loop_time)
        
        print("=" * 70)
        print(f"\n✅ Test başarıyla tamamlandı!")
        print(f"📊 Toplam ölçüm sayısı: {measurement_count}")
        print(f"⚠️  Hata sayısı: {error_count}")
        
        if error_count == 0:
            print("🎉 Hiç hata yok - Mükemmel!")
        elif error_count < measurement_count * 0.01:
            print("👍 Hata oranı %1'den az - Çok iyi!")
        else:
            print(f"⚠️  Hata oranı: {(error_count/measurement_count*100):.1f}%")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test kullanıcı tarafından durduruldu!")
    
    except Exception as e:
        print(f"\n\n❌ Test sırasında hata: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Güvenli kapanış
        print("\n🔄 Güvenli kapanış yapılıyor...")
        
        # Voltajı kademeli düşür
        current_v = sgx.get_voltage()
        if current_v > 0:
            print("📉 Gerilim kademeli olarak düşürülüyor...")
            steps = 5
            for i in range(steps, -1, -1):
                target_v = (current_v * i) / steps
                sgx.set_voltage(target_v)
                print(f"   {target_v:.1f} V")
                time.sleep(0.3)
        
        # Çıkışı kapat
        sgx.output_off()
        print("🔒 Çıkış kapatıldı")
        print(f"💾 Test verileri kaydedildi: {filename}")

# Ana program
if __name__ == "__main__":
    print("🔬 SORENSEN SGX YÜK TEST PROGRAMI")
    print("=" * 40)
    
    sgx = SGXController()
    
    try:
        # Bağlan
        print("🔌 Cihaza bağlanılıyor...")
        sgx.connect()
        
        # Güvenlik kontrolü
        if not safety_check(sgx):
            print("❌ Güvenlik kontrolü başarısız!")
            exit(1)
        
        # TEST PARAMETRELERİ
        print("\n📋 TEST PARAMETRELERİ:")
        print("-" * 30)
        
        voltage = 40.0        # Test gerilimi (V)
        current_limit = 5.0   # Akım limiti (A)
        duration = 1        # Test süresi (dakika) - 30 saniye
        
        print(f"Gerilim: {voltage} V")
        print(f"Akım Limiti: {current_limit} A")
        print(f"Test Süresi: {duration} dakika ({duration*60:.0f} saniye)")
        print(f"Maksimum Güç: {voltage * current_limit} W")
        
        # Onay al
        print("\n⚠️  DİKKAT: Yük bağlı olduğundan emin olun!")
        input("Başlamak için ENTER tuşuna basın...")
        
        # Testi çalıştır
        load_test(sgx, voltage, current_limit, duration)
        
    except Exception as e:
        print(f"\n❌ Program hatası: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Her durumda güvenli kapat
        try:
            sgx.output_off()
            print("\n🔒 Final güvenlik: Çıkış kapatıldı")
        except:
            pass
        
        sgx.disconnect()
        print("\n✨ Program sonlandı")
