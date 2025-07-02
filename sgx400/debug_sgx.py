import socket
import time
import threading
from datetime import datetime

class SGXDebugger:
    def __init__(self, ip="169.254.134.194", port=9221):
        self.ip = ip
        self.port = port
        self.socket = None
        
    def debug_print(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {level}: {message}")
        
    def connect_debug(self):
        """Detaylı bağlantı testi"""
        self.debug_print("=== BAĞLANTI DEBUGGİNG ===")
        
        try:
            self.debug_print(f"Socket oluşturuluyor...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            self.debug_print(f"TCP_NODELAY ayarlanıyor...")
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            self.debug_print(f"{self.ip}:{self.port} adresine bağlanılıyor...")
            self.socket.connect((self.ip, self.port))
            
            self.debug_print("✅ Bağlantı başarılı!")
            
            # Socket bilgilerini göster
            local_addr = self.socket.getsockname()
            remote_addr = self.socket.getpeername()
            self.debug_print(f"Yerel adres: {local_addr}")
            self.debug_print(f"Uzak adres: {remote_addr}")
            
            return True
            
        except Exception as e:
            self.debug_print(f"❌ Bağlantı hatası: {e}", "ERROR")
            return False
    
    def test_socket_modes(self):
        """Farklı socket modlarını test et"""
        self.debug_print("\n=== SOCKET MOD TESTLERİ ===")
        
        modes = [
            ("Blocking", None),
            ("1 saniye timeout", 1.0),
            ("5 saniye timeout", 5.0),
            ("10 saniye timeout", 10.0)
        ]
        
        for mode_name, timeout in modes:
            self.debug_print(f"\n--- {mode_name} Testi ---")
            
            try:
                self.socket.settimeout(timeout)
                self.debug_print(f"Timeout: {timeout}")
                
                # IDN komutunu test et
                result = self.raw_query_test("*IDN?")
                self.debug_print(f"Sonuç: {result}")
                
            except Exception as e:
                self.debug_print(f"❌ {mode_name} hatası: {e}", "ERROR")
    
    def raw_query_test(self, command):
        """Ham socket query testi"""
        try:
            # Buffer temizliği
            self.socket.settimeout(0.1)
            try:
                old_data = self.socket.recv(4096)
                if old_data:
                    self.debug_print(f"Buffer'da kalan veri: {old_data}", "WARN")
            except socket.timeout:
                pass
            except Exception as e:
                self.debug_print(f"Buffer temizlik hatası: {e}", "WARN")
            
            # Orijinal timeout'a geri dön
            self.socket.settimeout(5.0)
            
            # Komut gönder
            send_data = (command + '\n').encode()
            self.debug_print(f"Gönderilen: {send_data}")
            
            bytes_sent = self.socket.send(send_data)
            self.debug_print(f"Gönderilen byte sayısı: {bytes_sent}")
            
            # Yanıt bekle
            self.debug_print("Yanıt bekleniyor...")
            response = self.socket.recv(1024)
            self.debug_print(f"Ham yanıt: {response}")
            
            decoded = response.decode().strip()
            self.debug_print(f"Çözümlenmiş yanıt: '{decoded}'")
            
            return decoded
            
        except socket.timeout:
            self.debug_print("❌ Socket timeout!", "ERROR")
            return None
        except Exception as e:
            self.debug_print(f"❌ Query hatası: {e}", "ERROR")
            return None
    
    def test_different_commands(self):
        """Farklı SCPI komutlarını test et"""
        self.debug_print("\n=== KOMUT TESTLERİ ===")
        
        commands = [
            "*IDN?",
            "MEAS:VOLT?", 
            "MEAS:CURR?",
            "OUTP:STAT?",
            "SOUR:VOLT?",
            "SOUR:CURR?"
        ]
        
        for cmd in commands:
            self.debug_print(f"\n--- {cmd} Komutu ---")
            result = self.raw_query_test(cmd)
            if result:
                self.debug_print(f"✅ Başarılı: {result}")
            else:
                self.debug_print(f"❌ Başarısız")
            time.sleep(1)
    
    def test_line_endings(self):
        """Farklı satır sonlandırıcıları test et"""
        self.debug_print("\n=== SATIR SONLANDİRİCİ TESTLERİ ===")
        
        endings = [
            ("\\n", "\n"),
            ("\\r", "\r"), 
            ("\\r\\n", "\r\n"),
            ("\\n\\r", "\n\r")
        ]
        
        for name, ending in endings:
            self.debug_print(f"\n--- {name} Testi ---")
            try:
                send_data = ("*IDN?" + ending).encode()
                self.debug_print(f"Gönderilen: {send_data}")
                
                self.socket.send(send_data)
                time.sleep(1)
                
                self.socket.settimeout(2.0)
                response = self.socket.recv(1024)
                decoded = response.decode().strip()
                
                self.debug_print(f"✅ Yanıt: {decoded}")
                
            except Exception as e:
                self.debug_print(f"❌ {name} hatası: {e}", "ERROR")
    
    def monitor_traffic(self, duration=10):
        """Socket trafiğini izle"""
        self.debug_print(f"\n=== {duration} SANİYE TRAFİK İZLEME ===")
        
        def traffic_monitor():
            start_time = time.time()
            while time.time() - start_time < duration:
                try:
                    self.socket.settimeout(0.5)
                    data = self.socket.recv(1024)
                    if data:
                        self.debug_print(f"Gelen veri: {data}", "TRAFFIC")
                except socket.timeout:
                    continue
                except Exception as e:
                    self.debug_print(f"İzleme hatası: {e}", "ERROR")
                    break
        
        monitor_thread = threading.Thread(target=traffic_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Test komutları gönder
        test_commands = ["*IDN?", "MEAS:VOLT?", "MEAS:CURR?"]
        for cmd in test_commands:
            self.debug_print(f"Test komutu gönderiliyor: {cmd}")
            try:
                self.socket.send((cmd + '\n').encode())
                time.sleep(2)
            except Exception as e:
                self.debug_print(f"Komut gönderme hatası: {e}", "ERROR")
        
        monitor_thread.join(timeout=duration)
        self.debug_print("Trafik izleme tamamlandı")
    
    def disconnect(self):
        if self.socket:
            self.socket.close()
            self.debug_print("🔌 Bağlantı kapatıldı")

def main():
    debugger = SGXDebugger()
    
    try:
        # Bağlantı testi
        if not debugger.connect_debug():
            print("❌ Bağlantı kurulamadı!")
            return
        
        # Farklı testleri çalıştır
        debugger.test_socket_modes()
        
        debugger.test_line_endings()
        
        debugger.test_different_commands()
        
        debugger.monitor_traffic(duration=15)
        
        print("\n" + "="*50)
        print("🔍 DEBUG RAPORU:")
        print("1. Web arayüzü çalışıyor = Cihaz OK")
        print("2. Socket bağlantısı kuruluyor = Network OK") 
        print("3. Yanıt alamıyorsak = Protocol sorunu")
        print("4. Yukarıdaki testleri inceleyin")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n⚠️ Debug kullanıcı tarafından durduruldu!")
    except Exception as e:
        print(f"❌ Debug hatası: {e}")
    finally:
        debugger.disconnect()

if __name__ == "__main__":
    main()
