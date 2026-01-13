-- EMAIL SİSTEMİNİ GEÇİCİ OLARAK KAPAT (2026-01-13)
-- Bu script email gönderme özelliğini geçici olarak devre dışı bırakır
-- Gelecekte tekrar aktif edilebilir

-- Email gönderme özelliğini geçici olarak kapat
UPDATE public.late_arrival_settings 
SET setting_value = 'false' 
WHERE setting_name = 'email_enabled';

-- Eğer ayar yoksa ekle
INSERT INTO public.late_arrival_settings (setting_name, setting_value, description)
VALUES ('email_enabled', 'false', 'Email system temporarily disabled - can be re-enabled later')
ON CONFLICT (setting_name) DO UPDATE SET 
    setting_value = 'false',
    description = 'Email system temporarily disabled - can be re-enabled later',
    updated_at = CURRENT_TIMESTAMP;

-- Email ayarları korunuyor (gelecekte kullanmak için)
-- SMTP ayarları değiştirilmiyor, sadece email_enabled = false yapılıyor

-- Kontrol et
SELECT setting_name, setting_value, description 
FROM public.late_arrival_settings 
WHERE setting_name IN ('email_enabled', 'smtp_server', 'smtp_port', 'smtp_username', 'from_email')
ORDER BY setting_name;

-- Gelecekte email sistemini tekrar açmak için:
-- UPDATE public.late_arrival_settings SET setting_value = 'true' WHERE setting_name = 'email_enabled';