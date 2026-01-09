#!/usr/bin/env python3
"""
Environment variables'ları kontrol et
"""
import os
from dotenv import load_dotenv

load_dotenv()

def check_env_vars():
    """Environment variables'ları kontrol et"""
    print("🔍 ENVIRONMENT VARIABLES KONTROLÜ")
    print("=" * 50)
    
    # SMTP ayarları
    smtp_vars = {
        'SMTP_SERVER': os.getenv('SMTP_SERVER'),
        'SMTP_PORT': os.getenv('SMTP_PORT'),
        'SMTP_USERNAME': os.getenv('SMTP_USERNAME'),
        'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD'),
        'FROM_EMAIL': os.getenv('FROM_EMAIL')
    }
    
    print("📧 SMTP AYARLARI:")
    for var_name, var_value in smtp_vars.items():
        if var_value:
            if 'PASSWORD' in var_name:
                print(f"  ✅ {var_name}: {'*' * len(var_value)} (length: {len(var_value)})")
            else:
                print(f"  ✅ {var_name}: {var_value}")
        else:
            print(f"  ❌ {var_name}: NOT SET")
    
    # Database ayarları
    db_vars = {
        'DB_NAME': os.getenv('DB_NAME'),
        'DB_USER': os.getenv('DB_USER'),
        'DB_PASSWORD': os.getenv('DB_PASSWORD'),
        'DB_HOST': os.getenv('DB_HOST'),
        'DB_PORT': os.getenv('DB_PORT')
    }
    
    print(f"\n🗄️  DATABASE AYARLARI:")
    for var_name, var_value in db_vars.items():
        if var_value:
            if 'PASSWORD' in var_name:
                print(f"  ✅ {var_name}: {'*' * min(len(var_value), 10)} (length: {len(var_value)})")
            else:
                print(f"  ✅ {var_name}: {var_value}")
        else:
            print(f"  ❌ {var_name}: NOT SET")
    
    # Eksik olanları say
    missing_smtp = [k for k, v in smtp_vars.items() if not v]
    missing_db = [k for k, v in db_vars.items() if not v]
    
    print(f"\n📊 ÖZET:")
    print(f"SMTP Ayarları: {len(smtp_vars) - len(missing_smtp)}/{len(smtp_vars)} ({'✅' if not missing_smtp else '❌'})")
    print(f"Database Ayarları: {len(db_vars) - len(missing_db)}/{len(db_vars)} ({'✅' if not missing_db else '❌'})")
    
    if missing_smtp:
        print(f"\n❌ EKSIK SMTP AYARLARI:")
        for var in missing_smtp:
            print(f"  - {var}")
    
    if missing_db:
        print(f"\n❌ EKSIK DATABASE AYARLARI:")
        for var in missing_db:
            print(f"  - {var}")
    
    # Railway için öneriler
    if missing_smtp or missing_db:
        print(f"\n🚀 RAILWAY İÇİN ÇÖZÜM:")
        print("1. Railway dashboard'a git")
        print("2. Projenin Variables sekmesine git")
        print("3. Eksik environment variable'ları ekle:")
        
        if missing_smtp:
            print("\n📧 SMTP Variables:")
            print("SMTP_SERVER=smtp.gmail.com")
            print("SMTP_PORT=587")
            print("SMTP_USERNAME=wcuhrsystem@gmail.com")
            print("SMTP_PASSWORD=gxhz ichg ppdp wgea")
            print("FROM_EMAIL=wcuhrsystem@gmail.com")

if __name__ == "__main__":
    check_env_vars()