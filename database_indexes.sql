-- HR System Performance Optimization - Database Indexes
-- Bu SQL dosyasını PostgreSQL veritabanınızda çalıştırın

-- 1. Employee filtering by position (Dashboard ve Employee lists için)
CREATE INDEX IF NOT EXISTS idx_pers_person_position_id ON public.pers_person(position_id);
CREATE INDEX IF NOT EXISTS idx_pers_position_name_lower ON public.pers_position(LOWER(name));

-- 2. Transaction queries optimization (Dashboard için)
CREATE INDEX IF NOT EXISTS idx_acc_transaction_date ON public.acc_transaction(DATE(create_time));
CREATE INDEX IF NOT EXISTS idx_acc_transaction_name_date ON public.acc_transaction(name, last_name, DATE(create_time));
CREATE INDEX IF NOT EXISTS idx_acc_transaction_reader ON public.acc_transaction(reader_name);
CREATE INDEX IF NOT EXISTS idx_acc_transaction_card_no ON public.acc_transaction(card_no);

-- 3. Employee names for joins (Tüm employee queries için)
CREATE INDEX IF NOT EXISTS idx_pers_person_name ON public.pers_person(name, last_name);

-- 4. Birthday queries optimization
CREATE INDEX IF NOT EXISTS idx_pers_person_birthday_mmdd ON public.pers_person(TO_CHAR(birthday, 'MM-DD'));

-- 5. Employee creation date (Dashboard new employees için)
CREATE INDEX IF NOT EXISTS idx_pers_person_create_time ON public.pers_person(DATE(create_time));

-- 6. Composite index for common employee queries
CREATE INDEX IF NOT EXISTS idx_pers_person_composite ON public.pers_person(position_id, name, last_name) 
WHERE position_id IS NOT NULL;

-- 7. Attendance attribute optimization
CREATE INDEX IF NOT EXISTS idx_pers_attribute_ext_person ON public.pers_attribute_ext(person_id, attr_value4) 
WHERE attr_value4 IS NOT NULL;

-- 8. Transaction reader name optimization
CREATE INDEX IF NOT EXISTS idx_acc_transaction_reader_pattern ON public.acc_transaction(reader_name) 
WHERE reader_name ILIKE '%-in%' OR reader_name ILIKE '%-out%' 
   OR reader_name LIKE 'Building%' OR reader_name LIKE 'Bulding%' OR reader_name LIKE 'İcerisheher%' OR reader_name LIKE 'Filologiya%';

-- 9. Employee search optimization (name + last_name combined)
CREATE INDEX IF NOT EXISTS idx_pers_person_fullname ON public.pers_person(LOWER(name || ' ' || last_name));

-- 10. Photo path optimization (NULL check için)
CREATE INDEX IF NOT EXISTS idx_pers_person_photo ON public.pers_person(photo_path) 
WHERE photo_path IS NOT NULL;

-- Performance monitoring query
-- Bu query'yi çalıştırarak index kullanımını kontrol edebilirsiniz:
/*
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
*/

-- Slow query monitoring
-- Bu query'yi çalıştırarak yavaş sorguları görebilirsiniz:
/*
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
WHERE mean_time > 100  -- 100ms'den yavaş sorgular
ORDER BY mean_time DESC
LIMIT 10;
*/

ANALYZE; -- İstatistikleri güncelle