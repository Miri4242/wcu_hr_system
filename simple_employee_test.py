#!/usr/bin/env python3
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# DB bağlantı
try:
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT', '5432')
    )
    print("✅ DB bağlantısı OK")
    
    cur = conn.cursor()
    
    # 1. Employee sayısı
    cur.execute("SELECT COUNT(*) FROM public.pers_person")
    employee_count = cur.fetchone()[0]
    print(f"📊 Toplam çalışan: {employee_count}")
    
    # 2. Transaction sayısı (son 3 gün)
    cur.execute("""
        SELECT COUNT(*) FROM public.acc_transaction 
        WHERE create_time >= CURRENT_DATE - INTERVAL '3 days'
    """)
    transaction_count = cur.fetchone()[0]
    print(f"📊 Son 3 gün transaction: {transaction_count}")
    
    # 3. Employee dropdown test
    cur.execute("""
        SELECT COUNT(*) FROM public.pers_person p
        LEFT JOIN public.pers_position pp ON p.position_id = pp.id
        WHERE pp.name IS NULL
           OR (pp.name NOT ILIKE 'STUDENT' 
               AND pp.name NOT ILIKE 'VISITOR'
               AND pp.name NOT ILIKE 'MÜƏLLİM')
    """)
    filtered_count = cur.fetchone()[0]
    print(f"📊 Filtrelenmiş çalışan: {filtered_count}")
    
    if filtered_count == 0:
        print("❌ SORUN: Hiç çalışan bulunamadı!")
        print("   Position filtresi çok sıkı olabilir")
    elif transaction_count == 0:
        print("❌ SORUN: Hiç transaction yok!")
        print("   Turnike verileri eksik")
    else:
        print("✅ Veriler mevcut - başka sorun var")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Hata: {e}")