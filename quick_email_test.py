#!/usr/bin/env python3
"""
Hızlı email test - Railway'de çalışır mı?
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def quick_test():
    """Hızlı SMTP test"""
    try:
        print("🚀 Railway Email Test Başlıyor...")
        
        # SMTP ayarları
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('FROM_EMAIL')
        
        print(f"SMTP: {smtp_server}:{smtp_port}")
        print(f"From: {from_email}")
        
        # Test emaili
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = from_email  # Kendine gönder
        msg['Subject'] = "🎉 Railway Late Arrival System - ÇALIŞIYOR!"
        
        body = """
TEBRIKLER! 🎉

Railway'deki Late Arrival System email gönderme özelliği çalışıyor!

✅ SMTP bağlantısı başarılı
✅ Email gönderme başarılı
✅ Sistem hazır!

Artık geç kalan çalışanlara otomatik email gönderilecek.
Hashlenmis/geçersiz emailler otomatik olarak atlanacak.

Test Tarihi: {date}
        """.format(date="2026-01-09")
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Gönder
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print("✅ EMAIL BAŞARIYLA GÖNDERİLDİ!")
        print("📬 Emailinizi kontrol edin!")
        return True
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

if __name__ == "__main__":
    quick_test()