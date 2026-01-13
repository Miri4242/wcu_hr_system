#!/usr/bin/env python3
"""
Quick test for category counts
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432)
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def test_category_counts():
    conn = get_db_connection()
    if not conn:
        return
    
    cur = conn.cursor()
    
    print("🔍 Testing category counts (same as API)...")
    
    # Active count - Administrative çalışanlar (MÜƏLLİM HARİÇ)
    cur.execute("""
        SELECT COUNT(*) 
        FROM public.pers_person p
        LEFT JOIN public.pers_position pp ON p.position_id = pp.id
        LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
        WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM'))
          AND (ad.name IS NULL OR ad.name != 'School')
    """)
    active_count = cur.fetchone()[0]
    
    # School count
    cur.execute("""
        SELECT COUNT(*) 
        FROM public.pers_person p
        LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
        WHERE ad.name = 'School'
    """)
    school_count = cur.fetchone()[0]
    
    # Teachers count
    cur.execute("""
        SELECT COUNT(*) 
        FROM public.pers_person p
        LEFT JOIN public.pers_position pp ON p.position_id = pp.id
        LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
        WHERE pp.name ILIKE 'MÜƏLLİM' AND (ad.name IS NULL OR ad.name != 'School')
    """)
    teachers_count = cur.fetchone()[0]
    
    print(f"Active (Administrative): {active_count}")
    print(f"School: {school_count}")
    print(f"Teachers: {teachers_count}")
    print(f"Total: {active_count + school_count + teachers_count}")
    
    print("\n🎯 Expected vs Actual:")
    print(f"  Administrative - Expected: 149, Actual: {active_count}")
    print(f"  School - Expected: 35, Actual: {school_count}")
    print(f"  Teachers - Expected: 199, Actual: {teachers_count}")
    
    if active_count == 149 and school_count == 35 and teachers_count == 199:
        print("✅ All counts match!")
    else:
        print("❌ Counts don't match")
    
    conn.close()

if __name__ == "__main__":
    test_category_counts()