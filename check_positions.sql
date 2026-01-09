-- Pozisyonları kontrol et
-- Bu script Railway PostgreSQL'de çalıştırılacak

-- En çok kişi olan pozisyonlar
SELECT 
    pp.name as pozisyon,
    COUNT(*) as kisi_sayisi
FROM pers_person p 
LEFT JOIN pers_position pp ON p.position_id = pp.id 
WHERE pp.name IS NOT NULL 
GROUP BY pp.name 
ORDER BY COUNT(*) DESC
LIMIT 20;

-- Student içeren pozisyonlar
SELECT 
    'STUDENT POZİSYONLARI' as kategori,
    pp.name as pozisyon,
    COUNT(*) as kisi_sayisi
FROM pers_person p 
LEFT JOIN pers_position pp ON p.position_id = pp.id 
WHERE pp.name IS NOT NULL 
AND (pp.name ILIKE '%STUDENT%' OR pp.name ILIKE '%ÖĞRENCİ%' OR pp.name ILIKE '%MÜƏLLİM%')
GROUP BY pp.name 
ORDER BY COUNT(*) DESC;

-- Employee/Staff pozisyonları
SELECT 
    'EMPLOYEE POZİSYONLARI' as kategori,
    pp.name as pozisyon,
    COUNT(*) as kisi_sayisi
FROM pers_person p 
LEFT JOIN pers_position pp ON p.position_id = pp.id 
WHERE pp.name IS NOT NULL 
AND (pp.name ILIKE '%EMPLOYEE%' 
     OR pp.name ILIKE '%ÇALIŞAN%' 
     OR pp.name ILIKE '%STAFF%'
     OR pp.name ILIKE '%PERSONEL%'
     OR pp.name ILIKE '%ADMIN%'
     OR pp.name ILIKE '%MANAGER%'
     OR pp.name ILIKE '%MÜDÜR%'
     OR pp.name ILIKE '%MEMUR%'
     OR pp.name ILIKE '%UZMAN%')
GROUP BY pp.name 
ORDER BY COUNT(*) DESC;