-- Mevcut kullanıcıları listele
SELECT id, email, full_name, user_role, is_active 
FROM public.system_users 
ORDER BY id;