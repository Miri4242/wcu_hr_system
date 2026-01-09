#!/usr/bin/env python3
"""
Railway'de Gmail SMTP'yi zorla çalıştır
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

def force_gmail_smtp():
    """Gmail SMTP'yi Railway'de zorla çalıştır"""
    print("🔧 GMAIL SMTP FORCE MODE")
    print("=" * 30)
    
    test_email = "miryusifbabayev42@gmail.com"
    username = "wcuhrsystem@gmail.com"
    password = "gxhz ichg ppdp wgea"
    
    # Railway için özel Gmail SMTP konfigürasyonları
    configs = [
        {
            'name': 'Gmail Direct IP (587)',
            'server': '74.125.133.108',  # Gmail IP
            'port': 587,
            'method': 'tls'
        },
        {
            'name': 'Gmail Direct IP (465)',
            'server': '74.125.133.108',
            'port': 465,
            'method': 'ssl'
        },
        {
            'name': 'Gmail Alternative IP (587)',
            'server': '142.250.191.108',  # Alternatif Gmail IP
            'port': 587,
            'method': 'tls'
        },
        {
            'name': 'Gmail Standard (587) - Force',
            'server': 'smtp.gmail.com',
            'port': 587,
            'method': 'tls_force'
        },
        {
            'name': 'Gmail SSL (465) - Force',
            'server': 'smtp.gmail.com',
            'port': 465,
            'method': 'ssl_force'
        }
    ]
    
    for config in configs:
        print(f"\n🧪 Testing: {config['name']}")
        
        try:
            # Port erişilebilirlik testi
            print(f"   🔌 Testing port {config['port']}...")
            sock = socket.create_connection((config['server'], config['port']), timeout=15)
            sock.close()
            print(f"   ✅ Port {config['port']} accessible")
            
            # Email gönderme testi
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = test_email
            msg['Subject'] = f"🚀 Railway Gmail Force Test - {config['name']}"
            
            body = f"""
BAŞARILI! 🎉

Railway'de Gmail SMTP çalışıyor!

Konfigürasyon: {config['name']}
Server: {config['server']}:{config['port']}
Method: {config['method']}

Bu konfigürasyonu kullan!
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SMTP bağlantısı - farklı yöntemler
            if config['method'] == 'ssl':
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(config['server'], config['port'], context=context)
            elif config['method'] == 'ssl_force':
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                server = smtplib.SMTP_SSL(config['server'], config['port'], context=context)
            elif config['method'] == 'tls_force':
                server = smtplib.SMTP(config['server'], config['port'])
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                server.starttls(context=context)
            else:  # tls
                server = smtplib.SMTP(config['server'], config['port'])
                server.starttls()
            
            print(f"   🔑 Logging in...")
            server.login(username, password)
            
            print(f"   📤 Sending email...")
            server.send_message(msg)
            server.quit()
            
            print(f"   🎉 SUCCESS! Email sent with {config['name']}")
            
            # Başarılı konfigürasyonu döndür
            return config
            
        except socket.timeout:
            print(f"   ❌ Timeout - Railway might be blocking this port")
        except socket.gaierror:
            print(f"   ❌ DNS resolution failed")
        except smtplib.SMTPAuthenticationError as e:
            print(f"   ❌ Authentication failed: {e}")
        except smtplib.SMTPConnectError as e:
            print(f"   ❌ Connection failed: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n💥 All Gmail SMTP methods failed on Railway")
    return None

def check_railway_environment():
    """Railway environment'ını kontrol et"""
    print(f"\n🚂 RAILWAY ENVIRONMENT CHECK")
    print("=" * 35)
    
    # Environment variables
    env_vars = ['RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID', 'PORT']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    # Network testi
    print(f"\n🌐 Network connectivity test:")
    test_hosts = [
        ('google.com', 80),
        ('smtp.gmail.com', 587),
        ('smtp.gmail.com', 465),
        ('74.125.133.108', 587)
    ]
    
    for host, port in test_hosts:
        try:
            sock = socket.create_connection((host, port), timeout=10)
            sock.close()
            print(f"✅ {host}:{port} - Reachable")
        except Exception as e:
            print(f"❌ {host}:{port} - Blocked ({e})")

if __name__ == "__main__":
    # Railway environment kontrol
    check_railway_environment()
    
    # Gmail SMTP force test
    working_config = force_gmail_smtp()
    
    if working_config:
        print(f"\n🎉 WORKING GMAIL SMTP CONFIG:")
        print(f"Server: {working_config['server']}")
        print(f"Port: {working_config['port']}")
        print(f"Method: {working_config['method']}")
        print(f"\nRailway environment variables:")
        print(f"SMTP_SERVER={working_config['server']}")
        print(f"SMTP_PORT={working_config['port']}")
        print(f"SMTP_METHOD={working_config['method']}")
    else:
        print(f"\n💥 Gmail SMTP doesn't work on Railway")
        print("Railway is blocking SMTP ports or Gmail is rejecting Railway IPs")