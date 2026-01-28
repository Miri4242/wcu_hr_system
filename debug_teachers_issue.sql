-- Check transaction count for Könül Əhmədova
SELECT COUNT(*) 
FROM public.acc_transaction 
WHERE (LOWER(name) = 'könül' AND LOWER(last_name) = 'əhmədova')
   OR pin IN (SELECT pin FROM public.pers_person WHERE LOWER(name) = 'könül' AND LOWER(last_name) = 'əhmədova');

-- Check total transactions for Teachers category in the last year
SELECT COUNT(*)
FROM public.acc_transaction t
JOIN public.pers_person p ON (t.pin = p.pin OR (t.name = p.name AND t.last_name = p.last_name))
JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE pp.name = 'Müəllim' 
  AND (ad.name IS NULL OR ad.name != 'School')
  AND t.create_time > CURRENT_DATE - INTERVAL '1 year';