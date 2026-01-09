-- Geçersiz email adreslerini temizle
-- Bu script Railway PostgreSQL'de çalıştırılacak

-- Önce kaç tane geçersiz email var kontrol et
SELECT 
    'Geçersiz Email Sayısı' as durum,
    COUNT(*) as sayi
FROM pers_person 
WHERE email IS NOT NULL 
AND email != '' 
AND email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';

-- Geçersiz email adreslerini NULL yap
UPDATE pers_person 
SET email = NULL 
WHERE email IS NOT NULL 
AND email != '' 
AND email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';

-- Sonucu kontrol et
SELECT 
    'Temizleme Sonrası Geçerli Email' as durum,
    COUNT(*) as sayi
FROM pers_person 
WHERE email IS NOT NULL 
AND email != '' 
AND email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';

-- Hala geçersiz email var mı kontrol et
SELECT 
    'Hala Geçersiz Email' as durum,
    COUNT(*) as sayi
FROM pers_person 
WHERE email IS NOT NULL 
AND email != '' 
AND email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';