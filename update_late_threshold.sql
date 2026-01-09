-- Gecikme threshold'unu 30 dakika yap (09:30'dan sonra gecikme sayılsın)
UPDATE public.late_arrival_settings 
SET setting_value = '30' 
WHERE setting_name = 'late_threshold_minutes';

-- Kontrol et
SELECT setting_name, setting_value 
FROM public.late_arrival_settings 
WHERE setting_name = 'late_threshold_minutes';