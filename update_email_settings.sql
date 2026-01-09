-- Gmail SMTP ayarlarını güncelle
UPDATE public.late_arrival_settings 
SET setting_value = 'smtp.gmail.com' 
WHERE setting_name = 'smtp_server';

UPDATE public.late_arrival_settings 
SET setting_value = '587' 
WHERE setting_name = 'smtp_port';

UPDATE public.late_arrival_settings 
SET setting_value = 'wcuhrsystem@gmail.com' 
WHERE setting_name = 'smtp_username';

-- BURAYA APP PASSWORD'U YAZ (Gmail'den aldığın 16 haneli şifre)
UPDATE public.late_arrival_settings 
SET setting_value = 'gxhz ichg ppdp wgea' 
WHERE setting_name = 'smtp_password';

UPDATE public.late_arrival_settings 
SET setting_value = 'wcuhrsystem@gmail.com' 
WHERE setting_name = 'from_email';

-- Kontrol et
SELECT setting_name, setting_value 
FROM public.late_arrival_settings 
WHERE setting_name IN ('smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email');