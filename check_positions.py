#!/usr/bin/env python3
"""
Pozisyonları kontrol et - hangi pozisyonlar var?
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_positions():
    """Tüm pozisyonları listele"""
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
        
        print("📋 TÜM POZİSYONLAR:")
        print("=" * 50)
        
        # Tüm pozisyonları say
        cur.execute("""
            SELECT pp.name, COUNT(*) as kisi_sayisi
            FROM pers_person p 
            LEFT JOIN pers_position pp ON p.position_id = pp.id 
            WHERE pp.name IS NOT NULL 
            GROUP BY pp.name 
            ORDER BY COUNT(*) DESC
        """)
        
        positions = cur.fetchall()
        
        students = []
        employees = []
        others = []
        
        for pos_name, count in positions:
            pos_lower = pos_name.lower()
            
            if any(word in pos_lower for word in ['student', 'öğrenci', 'müəllim', 'teacher']):
                students.append((pos_name, count))
            elif any(word in pos_lower for word in ['employee', 'çalışan', 'staff', 'personel', 'admin', 'manager', 'müdür', 'memur', 'uzman', 'specialist']):
                employees.append((pos_name, count))
            else:
                others.append((pos_name, count))
        
        print("🎓 STUDENT/TEACHER POZİSYONLARI (ATLANACAK):")
        for pos, count in students:
            print(f"  ❌ {pos}: {count} kişi")
        
        print(f"\n👥 EMPLOYEE POZİSYONLARI (KONTROL EDİLECEK):")
        for pos, count in employees:
            print(f"  ✅ {pos}: {count} kişi")
        
        print(f"\n❓ DİĞER POZİSYONLAR:")
        for pos, count in others:
            print(f"  ⚠️  {pos}: {count} kişi")
        
        total_students = sum(count for _, count in students)
        total_employees = sum(count for _, count in employees)
        total_others = sum(count for _, count in others)
        
        print(f"\n📊 ÖZET:")
        print(f"Student/Teacher: {total_students}")
        print(f"Employee: {total_employees}")
        print(f"Diğer: {total_others}")
        print(f"TOPLAM: {total_students + total_employees + total_others}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    check_positions()