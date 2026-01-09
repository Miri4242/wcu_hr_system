#!/usr/bin/env python3
"""
Email adreslerini kontrol et ve düzelt
"""
import psycopg2
import re
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST'),
    'port': os.environ.get('DB_PORT', '5432')
}

def is_valid_email(email):
    """Email formatını kontrol et"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def check_and_fix_emails():
    """Email adreslerini kontrol et ve raporla"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Tüm email adreslerini getir
        cur.execute("""
            SELECT id, full_name, email 
            FROM pers_person 
            WHERE email IS NOT NULL AND email != ''
            ORDER BY full_name
        """)
        
        all_emails = cur.fetchall()
        valid_emails = []
        invalid_emails = []
        
        print(f"Toplam {len(all_emails)} email adresi kontrol ediliyor...\n")
        
        for emp_id, name, email in all_emails:
            if is_valid_email(email):
                valid_emails.append((emp_id, name, email))
                print(f"✅ GEÇERLI: {name} - {email}")
            else:
                invalid_emails.append((emp_id, name, email))
                print(f"❌ GEÇERSİZ: {name} - {email}")
        
        print(f"\n📊 ÖZET:")
        print(f"Geçerli email: {len(valid_emails)}")
        print(f"Geçersiz email: {len(invalid_emails)}")
        
        if invalid_emails:
            print(f"\n🔧 GEÇERSİZ EMAIL ADRESLERİ:")
            for emp_id, name, email in invalid_emails:
                print(f"ID: {emp_id}, İsim: {name}, Email: {email}")
        
        # Geçersiz emailleri NULL yap
        if invalid_emails:
            print(f"\n🔄 Geçersiz email adreslerini temizliyorum...")
            invalid_ids = [str(emp[0]) for emp in invalid_emails]
            cur.execute(f"""
                UPDATE pers_person 
                SET email = NULL 
                WHERE id IN ({','.join(['%s'] * len(invalid_ids))})
            """, invalid_ids)
            
            conn.commit()
            print(f"✅ {len(invalid_emails)} geçersiz email adresi temizlendi.")
        
        conn.close()
        return len(valid_emails), len(invalid_emails)
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return 0, 0

if __name__ == "__main__":
    print("🔍 Email Adresi Kontrol ve Temizleme Aracı")
    print("=" * 50)
    valid_count, invalid_count = check_and_fix_emails()
    print(f"\n✅ İşlem tamamlandı!")
    print(f"Geçerli: {valid_count}, Temizlenen: {invalid_count}")