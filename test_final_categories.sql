-- Final kategori testleri

-- 1. Administrative (School HARİÇ, Student/Visitor/Müəllim HARİÇ)
SELECT 'Administrative' as category, COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM'))
  AND (ad.name IS NULL OR ad.name != 'School')

UNION ALL

-- 2. School Department (School departmanındaki herkes - müəllimlər dahil)
SELECT 'School Department' as category, COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE ad.name = 'School'

UNION ALL

-- 3. Teachers (School department HARİÇ müəllimlər)
SELECT 'Teachers (School HARİÇ)' as category, COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE pp.name = 'Müəllim' AND (ad.name IS NULL OR ad.name != 'School')

UNION ALL

-- 4. School'daki müəllimlər (School'da kalacaklar)
SELECT 'School Müəllimlər' as category, COUNT(*) as count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE pp.name = 'Müəllim' AND ad.name = 'School'

UNION ALL

-- 5. Toplam kontrol
SELECT 'TOPLAM' as category, COUNT(*) as count
FROM public.pers_person p

ORDER BY category;