#!/usr/bin/env python3
"""
Railway Email Fix - SendGrid API kullan
Gmail SMTP Railway'de çalışmıyor olabilir
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_email_via_sendgrid(to_email, subject, body):
    """SendGrid API ile email gönder"""
    
    # SendGrid API key (ücretsiz hesap açılabilir)
    api_key = os.getenv('SENDGRID_API_KEY')
    
    if not api_key:
        print("❌ SENDGRID_API_KEY not found")
        return False
    
    url = "https://api.sendgrid.com/v3/mail/send"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": subject
            }
        ],
        "from": {"email": "wcuhrsystem@gmail.com", "name": "WCU HR System"},
        "content": [
            {
                "type": "text/plain",
                "value": body
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 202:
            print("✅ SendGrid email sent successfully!")
            return True
        else:
            print(f"❌ SendGrid error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ SendGrid exception: {e}")
        return False

def send_email_via_mailgun(to_email, subject, body):
    """Mailgun API ile email gönder"""
    
    api_key = os.getenv('MAILGUN_API_KEY')
    domain = os.getenv('MAILGUN_DOMAIN')
    
    if not api_key or not domain:
        print("❌ MAILGUN_API_KEY or MAILGUN_DOMAIN not found")
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
            print("✅ Mailgun email sent successfully!")
            return True
        else:
            print(f"❌ Mailgun error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Mailgun exception: {e}")
        return False

def test_api_email_services():
    """API tabanlı email servislerini test et"""
    print("🌐 API EMAIL SERVICES TEST")
    print("=" * 35)
    
    test_email = "miryusifbabayev42@gmail.com"
    subject = "🧪 Railway API Email Test"
    body = """
Merhaba!

Bu email Railway'den API tabanlı email servisi ile gönderildi.

SMTP yerine HTTP API kullanıyoruz çünkü Railway'de SMTP portları bloklanmış olabilir.

Test başarılı! 🎉
    """
    
    # SendGrid test
    print("\n📧 Testing SendGrid...")
    sendgrid_success = send_email_via_sendgrid(test_email, subject, body)
    
    # Mailgun test
    print("\n📧 Testing Mailgun...")
    mailgun_success = send_email_via_mailgun(test_email, subject, body)
    
    if sendgrid_success or mailgun_success:
        print(f"\n✅ API email service works!")
        return True
    else:
        print(f"\n❌ No API email service works")
        return False

if __name__ == "__main__":
    test_api_email_services()
    
    print(f"\n💡 RAILWAY EMAIL ÇÖZÜMÜ:")
    print("1. SendGrid hesabı aç (ücretsiz): https://sendgrid.com")
    print("2. API key al")
    print("3. Railway'e SENDGRID_API_KEY environment variable ekle")
    print("4. SMTP yerine SendGrid API kullan")