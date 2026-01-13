#!/usr/bin/env python3
"""
Final fix for employees categories
"""

# Doğru SQL sorguları:

# 1. Administrative (149 olmalı):
administrative_query = """
SELECT COUNT(*) 
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE (ad.name IS NULL OR ad.name != 'School')
  AND (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM'))
"""

# 2. School (35 olmalı):
school_query = """
SELECT COUNT(*) 
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE ad.name = 'School'
  AND (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR'))
"""

# 3. Teachers (199 olmalı):
teachers_query = """
SELECT COUNT(*) 
FROM public.pers_person p
LEFT JOIN public.pers_position pp ON p.position_id = pp.id
LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
WHERE pp.name ILIKE 'MÜƏLLİM' 
  AND (ad.name IS NULL OR ad.name != 'School')
  AND pp.name NOT ILIKE 'STUDENT' 
  AND pp.name NOT ILIKE 'VISITOR'
"""

print("Bu sorguları app.py'deki api_employees_list fonksiyonunda kullan:")
print("1. Administrative:", administrative_query)
print("2. School:", school_query) 
print("3. Teachers:", teachers_query)