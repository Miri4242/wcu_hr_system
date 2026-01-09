-- School departmanındaki çalışanları getir
SELECT 
    p.id,
    p.name,
    p.last_name,
    p.email,
    pp.name AS position_name,
    ad.name AS department_name
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE ad.name = 'School'
ORDER BY p.last_name, p.name;

-- Müəllim pozisyonundakileri getir
SELECT 
    p.id,
    p.name,
    p.last_name,
    p.email,
    pp.name AS position_name,
    ad.name AS department_name
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE pp.name = 'Müəllim'
ORDER BY p.last_name, p.name;

-- Aktif çalışanları getir (STUDENT, VISITOR, MÜƏLLİM hariç)
SELECT 
    p.id,
    p.name,
    p.last_name,
    p.email,
    pp.name AS position_name,
    ad.name AS department_name
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM')
ORDER BY p.last_name, p.name;