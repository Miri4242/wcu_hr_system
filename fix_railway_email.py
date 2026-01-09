#!/usr/bin/env python3
"""
Railway için email fix - Gmail yerine başka servis dene
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def test_multiple_smtp_services():
    """Farklı SMTP servislerini test et"""
    print("🧪 MULTIPLE SMTP SERVICES TEST")
    print("=" * 40)
    
    test_email = "miryusifbabayev42@gmail.com"
    
    # Test edilecek SMTP servisleri
    smtp_configs = [
        {
            'name': 'Gmail',
            'server': 'smtp.gmail.com',
            'port': 587,
            'username': 'wcuhrsystem@gmail.com',
            'password': 'gxhz ichg ppdp wgea',
            'from_email': 'wcuhrsystem@gmail.com'
        },
        {
            'name': 'Gmail Alternative Port',
            'server': 'smtp.gmail.com',
            'port': 465,
            'username': 'wcuhrsystem@gmail.com',
            'password': 'gxhz ichg ppdp wgea',
            'from_email': 'wcuhrsystem@gmail.com',
            'use_ssl': True
        },
        {
            'name': 'Outlook/Hotmail',
            'server': 'smtp-mail.outlook.com',
            'port': 587,
            'username': 'wcuhrsystem@outlook.com',  # Eğer varsa
            'password': 'your_outlook_password',
            'from_email': 'wcuhrsystem@outlook.com'
        }
    ]
    
    for config in smtp_configs:
        print(f"\n🔍 Testing {config['name']}...")
        print(f"   Server: {config['server']}:{config['port']}")
        
        try:
            # Email oluştur
            msg = MIMEMultipart()
            msg['From'] = config['from_email']
            msg['To'] = test_email
            msg['Subject'] = f"🧪 Railway Test - {config['name']}"
            
            body = f"""
Test email from Railway using {config['name']}

Server: {config['server']}:{config['port']}
From: {config['from_email']}
To: {test_email}

If you receive this, {config['name']} SMTP works on Railway!
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SMTP bağlantısı
            if config.get('use_ssl'):
                server = smtplib.SMTP_SSL(config['server'], config['port'])
            else:
                server = smtplib.SMTP(config['server'], config['port'])
                server.starttls()
            
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            
            print(f"   ✅ {config['name']} - SUCCESS!")
            return config  # İlk başarılı olanı döndür
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"   ❌ {config['name']} - AUTH ERROR: {e}")
        except smtplib.SMTPConnectError as e:
            print(f"   ❌ {config['name']} - CONNECT ERROR: {e}")
        except Exception as e:
            print(f"   ❌ {config['name']} - ERROR: {e}")
    
    print(f"\n💥 All SMTP services failed!")
    return None

def test_railway_specific_issues():
    """Railway'e özel sorunları test et"""
    print(f"\n🚂 RAILWAY SPECIFIC TESTS")
    print("=" * 30)
    
    # 1. Port testi
    import socket
    
    smtp_hosts = [
        ('smtp.gmail.com', 587),
        ('smtp.gmail.com', 465),
        ('smtp-mail.outlook.com', 587)
    ]
    
    for host, port in smtp_hosts:
        try:
            sock = socket.create_connection((host, port), timeout=10)
            sock.close()
            print(f"✅ {host}:{port} - Port accessible")
        except Exception as e:
            print(f"❌ {host}:{port} - Port blocked: {e}")
    
    # 2. DNS testi
    import socket
    try:
        ip = socket.gethostbyname('smtp.gmail.com')
        print(f"✅ DNS Resolution: smtp.gmail.com -> {ip}")
    except Exception as e:
        print(f"❌ DNS Resolution failed: {e}")

if __name__ == "__main__":
    # Test SMTP services
    working_config = test_multiple_smtp_services()
    
    # Test Railway specific issues
    test_railway_specific_issues()
    
    if working_config:
        print(f"\n🎉 WORKING SMTP CONFIG FOUND:")
        print(f"Use this in Railway environment variables:")
        print(f"SMTP_SERVER={working_config['server']}")
        print(f"SMTP_PORT={working_config['port']}")
        print(f"SMTP_USERNAME={working_config['username']}")
        print(f"FROM_EMAIL={working_config['from_email']}")
    else:
        print(f"\n💥 NO WORKING SMTP CONFIG FOUND")
        print("Railway might be blocking SMTP ports or Gmail is rejecting connections.")