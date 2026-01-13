-- Attendance fonksiyonundaki tam sorguyu test et

-- 1. Administrative çalışanları (attendance fonksiyonundaki gibi)
SELECT COUNT(*) as attendance_administrative_count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM'))
  AND (ad.name IS NULL OR ad.name != 'School');

-- 2. Employees API'sindeki active çalışanları (karşılaştırma)
SELECT COUNT(*) as employees_active_count
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
WHERE pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM');

-- 3. Fark nerede? School department çalışanları
SELECT COUNT(*) as school_department_count
FROM public.pers_person p
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE ad.name = 'School';

-- 4. Detaylı kontrol - hangi çalışanlar eksik?
-- Employees'da var ama Attendance'da yok olanlar
SELECT p.name, p.last_name, pp.name as position, ad.name as department
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM'))
  AND ad.name = 'School'
ORDER BY p.last_name, p.name;