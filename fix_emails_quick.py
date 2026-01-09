#!/usr/bin/env python3
"""
Geçersiz email adreslerini hızlıca temizle
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def fix_invalid_emails():
    """Geçersiz email adreslerini NULL yap"""
    try:
        DB_CONFIG = {
            'dbname': os.environ.get('DB_NAME'),
            'user': os.environ.get('DB_USER'),
            'password': os.environ.get('DB_PASSWORD'),
            'host': os.environ.get('DB_HOST'),
            'port': os.environ.get('DB_PORT', '5432')
        }
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🔧 Geçersiz email adreslerini temizliyorum...")
        
        # Geçersiz email adreslerini NULL yap
        cur.execute("""
            UPDATE pers_person 
            SET email = NULL 
            WHERE email IS NOT NULL 
            AND email != '' 
            AND email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
        """)
        
        affected_rows = cur.rowcount
        conn.commit()
        
        print(f"✅ {affected_rows} geçersiz email adresi temizlendi!")
        
        # Kontrol et
        cur.execute("""
            SELECT COUNT(*) 
            FROM pers_person 
            WHERE email IS NOT NULL 
            AND email != '' 
            AND email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
        """)
        valid_count = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(*) 
            FROM pers_person 
            WHERE email IS NOT NULL 
            AND email != '' 
            AND email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
        """)
        invalid_count = cur.fetchone()[0]
        
        print(f"📊 Sonuç:")
        print(f"Geçerli Email: {valid_count}")
        print(f"Geçersiz Email: {invalid_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Hızlı Email Temizleme")
    print("=" * 30)
    fix_invalid_emails()