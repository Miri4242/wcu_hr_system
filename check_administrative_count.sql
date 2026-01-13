-- Administrative çalışan sayısını kontrol et
-- School department HARİÇ, Student HARİÇ, Visitor HARİÇ, Müəllim HARİÇ

SELECT COUNT(*) as administrative_count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM'))
  AND (ad.name IS NULL OR ad.name != 'School');

-- Detaylı breakdown
SELECT 
    'Total Employees' as category,
    COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id

UNION ALL

SELECT 
    'Administrative (School HARİÇ, Student/Visitor/Müəllim HARİÇ)' as category,
    COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM'))
  AND (ad.name IS NULL OR ad.name != 'School')

UNION ALL

SELECT 
    'School Department' as category,
    COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE ad.name = 'School'

UNION ALL

SELECT 
    'Teachers (Müəllim)' as category,
    COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
WHERE pp.name = 'Müəllim'

UNION ALL

SELECT 
    'Students' as category,
    COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
WHERE pp.name ILIKE 'STUDENT'

UNION ALL

SELECT 
    'Visitors' as category,
    COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
WHERE pp.name ILIKE 'VISITOR'

ORDER BY category;

-- Employees sayfasındaki Active kategorisi (karşılaştırma için)
SELECT 
    'Employees Active Category' as category,
    COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
WHERE pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM');