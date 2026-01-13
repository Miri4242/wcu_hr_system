-- Test employee categories to find correct counts

-- 1. Administrative: School department HARİÇ + STUDENT/VISITOR/MÜƏLLİM HARİÇ
SELECT 'Administrative' as category, COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM'))
  AND (ad.name IS NULL OR ad.name != 'School');

-- 2. School: Department'i School olan herkes
SELECT 'School' as category, COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE ad.name = 'School';

-- 3. Teachers: Position'u MÜƏLLİM olan ama School department'ından OLMAYAN
SELECT 'Teachers' as category, COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE pp.name ILIKE 'MÜƏLLİM' AND (ad.name IS NULL OR ad.name != 'School');

-- 4. Total check
SELECT 'Total' as category, COUNT(*) as count
FROM public.pers_person p;

-- 5. Position breakdown
SELECT pp.name as position, COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
GROUP BY pp.name
ORDER BY count DESC;

-- 6. Department breakdown
SELECT ad.name as department, COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
GROUP BY ad.name
ORDER BY count DESC;