-- Eğer şifreler düz metin ise, bunları hash'leyin
-- Örnek: 'admin123' şifresini hash'le
-- Bu örnekte 'admin123' şifresini kullanıyorum, kendi şifrenizi yazın

-- Önce mevcut şifreleri kontrol edin
SELECT id, email, password, LENGTH(password) as password_length 
FROM public.system_users;

-- Eğer şifreler kısa ise (hash'li değilse), güncelleyin
-- Örnek admin kullanıcısı için:
-- UPDATE public.system_users 
-- SET password = 'sha256$' || encode(digest('your_salt_here', 'sha256'), 'hex') || '$' || encode(digest('admin123' || 'your_salt_here', 'sha256'), 'hex')
-- WHERE email = 'your-email@domain.com';

-- Basit çözüm: Geçici olarak düz metin şifre kullanın (güvenli değil, sadece test için)
-- UPDATE public.system_users SET password = 'admin123' WHERE id = 1;