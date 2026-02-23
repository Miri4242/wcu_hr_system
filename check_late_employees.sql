-- Check late employees functionality

-- 1. Check if pers_attribute_ext table exists
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'pers_attribute_ext' AND table_schema = 'public'
ORDER BY ordinal_position;

-- 2. Check attr_value4 data (expected working hours)
SELECT COUNT(*) as total_records,
       COUNT(CASE WHEN attr_value4 IS NOT NULL THEN 1 END) as with_attr_value4
FROM public.pers_attribute_ext;

-- 3. Sample attr_value4 data
SELECT person_id, attr_value4 
FROM public.pers_attribute_ext 
WHERE attr_value4 IS NOT NULL 
LIMIT 10;

-- 4. Check today's transactions
SELECT COUNT(*) as today_transactions
FROM public.acc_transaction 
WHERE DATE(create_time) = CURRENT_DATE;

-- 5. Check reader patterns
SELECT DISTINCT reader_name, COUNT(*) as count
FROM public.acc_transaction 
WHERE DATE(create_time) = CURRENT_DATE
GROUP BY reader_name
ORDER BY count DESC;

-- 6. Test late employees query for today
SELECT 
    p.name, p.last_name, p.id as person_id,
    MIN(t.create_time) as first_in_time,
    pae.attr_value4 as expected_time
FROM public.acc_transaction t
JOIN public.pers_card c ON t.card_no = c.card_no
JOIN public.pers_person p ON c.person_id = p.id
LEFT JOIN public.pers_attribute_ext pae ON p.id = pae.person_id
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
WHERE DATE(t.create_time) = CURRENT_DATE
  AND pae.attr_value4 IS NOT NULL
  AND t.reader_name IN (
        'Building A-1-In', 'Building A-2-In', 'Building B-1-In', 'Building B-2-In', 
        'İcerisheher-1-In', 'İcerisheher-2-In', 'BuldingA1-1-In', 
        'Filologiya-1-Dış', 'Filologiya-2-İçinde',
        'BuildingA-1', 'BuildingA-2', 'Collage-1', 'Collage-2',
        'BuildingA-1-In', 'BuildingA-2-In', 'College-1-In', 'College-2-In',
        'College-1', 'College-2'
    )
  AND (pp.name IS NULL OR (pp.name NOT ILIKE 'student' AND pp.name NOT ILIKE 'visitor' AND pp.name NOT ILIKE 'müəllim'))
GROUP BY p.name, p.last_name, p.id, pae.attr_value4
HAVING MIN(t.create_time) IS NOT NULL
ORDER BY p.last_name, p.name
LIMIT 10;