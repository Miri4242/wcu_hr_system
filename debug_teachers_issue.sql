-- Teachers sorunu debug etmek için SQL sorguları

-- 1. pers_position tablosundaki tüm pozisyonları görelim
SELECT id, name, COUNT(*) as person_count
FROM pers_position pp
LEFT JOIN pers_person p ON p.position_id = pp.id
GROUP BY pp.id, pp.name
ORDER BY pp.name;

-- 2. Müəllim pozisyonundaki kişileri görelim
SELECT p.id, p.name, p.last_name, pp.name as position_name
FROM pers_person p
LEFT JOIN pers_position pp ON p.position_id = pp.id
WHERE pp.name = 'Müəllim' OR pp.name = 'Müallim'
ORDER BY p.last_name, p.name;

-- 3. Müəllim pozisyonunun ID'sini bulalım
SELECT id, name FROM pers_position WHERE name LIKE '%əllim%' OR name LIKE '%allim%';

-- 4. Tüm pozisyonları alfabetik sırayla görelim
SELECT DISTINCT name FROM pers_position ORDER BY name;

-- 5. Teachers count'u kontrol edelim
SELECT COUNT(*) as teachers_count
FROM pers_person p
LEFT JOIN pers_position pp ON p.position_id = pp.id
WHERE pp.name = 'Müəllim' OR pp.name = 'Müallim';