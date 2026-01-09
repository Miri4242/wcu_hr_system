from db_service import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Pozisyon isimlerini kontrol et
cur.execute("SELECT DISTINCT name FROM pers_position WHERE name LIKE '%əllim%' OR name LIKE '%allim%' OR name LIKE '%eacher%'")
positions = cur.fetchall()
print('Müəllim benzeri pozisyonlar:')
for pos in positions:
    print(f'  - {pos[0]}')

# Tüm pozisyonları say
cur.execute("SELECT name, COUNT(*) FROM pers_person p LEFT JOIN pers_position pp ON p.position_id = pp.id WHERE pp.name IS NOT NULL GROUP BY pp.name ORDER BY COUNT(*) DESC LIMIT 10")
top_positions = cur.fetchall()
print('\nEn çok kişi olan pozisyonlar:')
for pos, count in top_positions:
    print(f'  - {pos}: {count} kişi')

conn.close()