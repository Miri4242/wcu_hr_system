-- Check transaction count for Könül Əhmədova
SELECT COUNT(*) 
FROM public.acc_transaction t
JOIN public.pers_card c ON t.card_no = c.card_no
JOIN public.pers_person p ON c.person_id = p.id
WHERE (LOWER(p.name) = 'könül' AND LOWER(p.last_name) = 'əhmədova');

-- Check total transactions for Teachers category in the last year
SELECT COUNT(*)
FROM public.acc_transaction t
JOIN public.pers_card c ON t.card_no = c.card_no
JOIN public.pers_person p ON c.person_id = p.id
JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE pp.name = 'Müəllim' 
  AND (ad.name IS NULL OR ad.name != 'School')
  AND t.create_time > CURRENT_DATE - INTERVAL '1 year';