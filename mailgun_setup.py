#!/usr/bin/env python3
"""
Mailgun setup for Railway - Gmail SMTP alternatifi
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_email_via_mailgun(to_email, subject, body):
    """Mailgun API ile email gönder"""
    
    # Mailgun ayarları
    api_key = os.getenv('MAILGUN_API_KEY')
    domain = os.getenv('MAILGUN_DOMAIN', 'sandbox-123.mailgun.org')  # Sandbox domain
    
    if not api_key:
        print("❌ MAILGUN_API_KEY bulunamadı")
        return False
    
    url = f"https://api.mailgun.net/v3/{domain}/messages"
    
    auth = ("api", api_key)
    
    data = {
        "from": f"WCU HR System <mailgun@{domain}>",
        "to": [to_email],
        "subject": subject,
        "text": body
    }
    
    try:
        response = requests.post(url, auth=auth, data=data)
        
        if response.status_code == 200:
            print("✅ Mailgun email gönderildi!")
            return True
        else:
            print(f"❌ Mailgun hatası: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Mailgun exception: {e}")
        return False

def test_mailgun():
    """Mailgun'u test et"""
    print("📧 MAILGUN TEST")
    print("=" * 20)
    
    test_email = "miryusifbabayev42@gmail.com"
    subject = "🚀 Railway Mailgun Test - ÇALIŞIYOR!"
    body = """
Tebrikler! 🎉

Railway'de Mailgun API ile email gönderme başarılı!

✅ Gmail SMTP yerine Mailgun API kullanıyoruz
✅ Railway'de HTTP API bloklanmıyor
✅ Ücretsiz 5000 email/ay

Artık Late Arrival System çalışabilir!

---
WCU HR System
Railway + Mailgun
    """
    
    success = send_email_via_mailgun(test_email, subject, body)
    
    if success:
        print(f"🎉 TEST BAŞARILI!")
        print(f"Email gönderildi: {test_email}")
    else:
        print(f"💥 TEST BAŞARISIZ!")
    
    return success

if __name__ == "__main__":
    print("🚀 MAILGUN SETUP FOR RAILWAY")
    print("=" * 35)
    
    print("1. https://mailgun.com'a git")
    print("2. Ücretsiz hesap aç (5000 email/ay)")
    print("3. API Key al")
    print("4. Railway'e environment variables ekle:")
    print("   MAILGUN_API_KEY=your_api_key")
    print("   MAILGUN_DOMAIN=your_domain")
    print()
    
    # Test et
    test_mailgun()