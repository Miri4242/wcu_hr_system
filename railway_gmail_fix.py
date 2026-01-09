#!/usr/bin/env python3
"""
Railway'de Gmail SMTP'yi çalıştırmanın yolları
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import socket

load_dotenv()

def test_gmail_smtp_methods():
    """Gmail SMTP'nin farklı yöntemlerini test et"""
    print("🔧 GMAIL SMTP FIX METHODS")
    print("=" * 35)
    
    test_email = "miryusifbabayev42@gmail.com"
    username = "wcuhrsystem@gmail.com"
    password = "gxhz ichg ppdp wgea"
    
    # Test edilecek konfigürasyonlar
    configs = [
        {
            'name': 'Gmail SMTP Standard (587)',
            'server': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'use_ssl': False
        },
        {
            'name': 'Gmail SMTP SSL (465)',
            'server': 'smtp.gmail.com',
            'port': 465,
            'use_tls': False,
            'use_ssl': True
        },
        {
            'name': 'Gmail SMTP Alternative (25)',
            'server': 'smtp.gmail.com',
            'port': 25,
            'use_tls': True,
            'use_ssl': False
        },
        {
            'name': 'Gmail SMTP IP Direct',
            'server': '74.125.133.108',  # Gmail IP
            'port': 587,
            'use_tls': True,
            'use_ssl': False
        }
    ]
    
    for config in configs:
        print(f"\n🧪 Testing: {config['name']}")
        print(f"   Server: {config['server']}:{config['port']}")
        
        try:
            # Port erişilebilirlik testi
            sock = socket.create_connection((config['server'], config['port']), timeout=10)
            sock.close()
            print(f"   ✅ Port {config['port']} accessible")
            
            # Email gönderme testi
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = test_email
            msg['Subject'] = f"🧪 Railway Test - {config['name']}"
            
            body = f"""
Test email from Railway using {config['name']}

Configuration:
- Server: {config['server']}
- Port: {config['port']}
- TLS: {config['use_tls']}
- SSL: {config['use_ssl']}

If you receive this, this configuration works on Railway!
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SMTP bağlantısı
            if config['use_ssl']:
                server = smtplib.SMTP_SSL(config['server'], config['port'])
            else:
                server = smtplib.SMTP(config['server'], config['port'])
                if config['use_tls']:
                    server.starttls()
            
            server.login(username, password)
            server.send_message(msg)
            server.quit()
            
            print(f"   ✅ EMAIL SENT SUCCESSFULLY!")
            print(f"   🎉 USE THIS CONFIG IN RAILWAY!")
            
            return config  # İlk başarılı olanı döndür
            
        except socket.timeout:
            print(f"   ❌ Connection timeout - Port might be blocked")
        except socket.error as e:
            print(f"   ❌ Socket error: {e}")
        except smtplib.SMTPAuthenticationError as e:
            print(f"   ❌ Authentication error: {e}")
        except smtplib.SMTPConnectError as e:
            print(f"   ❌ Connection error: {e}")
        except Exception as e:
            print(f"   ❌ General error: {e}")
    
    print(f"\n💥 All Gmail SMTP methods failed!")
    return None

def check_railway_network():
    """Railway network kısıtlamalarını kontrol et"""
    print(f"\n🚂 RAILWAY NETWORK CHECK")
    print("=" * 30)
    
    # Yaygın SMTP portları
    smtp_tests = [
        ('smtp.gmail.com', 25),
        ('smtp.gmail.com', 587),
        ('smtp.gmail.com', 465),
        ('smtp-mail.outlook.com', 587),
        ('smtp.mail.yahoo.com', 587)
    ]
    
    for host, port in smtp_tests:
        try:
            sock = socket.create_connection((host, port), timeout=5)
            sock.close()
            print(f"✅ {host}:{port} - ACCESSIBLE")
        except Exception as e:
            print(f"❌ {host}:{port} - BLOCKED ({e})")

def suggest_alternatives():
    """Alternatif çözümler öner"""
    print(f"\n💡 ALTERNATIF ÇÖZÜMLER")
    print("=" * 25)
    
    print("1. 🔧 Gmail App Password Yenile:")
    print("   - Google Account > Security > 2-Step Verification")
    print("   - App passwords > Generate new password")
    print("   - Railway'de SMTP_PASSWORD'u güncelle")
    
    print("\n2. 🌐 Outlook/Hotmail Kullan:")
    print("   - Outlook hesabı aç")
    print("   - SMTP: smtp-mail.outlook.com:587")
    print("   - Daha az kısıtlama var")
    
    print("\n3. 🚀 Railway SMTP Relay:")
    print("   - Railway'in kendi SMTP servisi olabilir")
    print("   - Railway docs'u kontrol et")
    
    print("\n4. 📧 Basit SMTP Servisi:")
    print("   - Mailgun (ücretsiz 5000/ay)")
    print("   - Postmark (ücretsiz 100/ay)")
    print("   - Amazon SES (çok ucuz)")

if __name__ == "__main__":
    # Gmail SMTP yöntemlerini test et
    working_config = test_gmail_smtp_methods()
    
    # Railway network'ü kontrol et
    check_railway_network()
    
    # Alternatif çözümler öner
    suggest_alternatives()
    
    if working_config:
        print(f"\n🎉 WORKING CONFIG FOUND!")
        print(f"Railway environment variables:")
        print(f"SMTP_SERVER={working_config['server']}")
        print(f"SMTP_PORT={working_config['port']}")
        if working_config['use_ssl']:
            print("SMTP_USE_SSL=true")
        if working_config['use_tls']:
            print("SMTP_USE_TLS=true")
    else:
        print(f"\n💥 Gmail SMTP doesn't work on Railway")
        print("Try alternative email services or check Railway docs")