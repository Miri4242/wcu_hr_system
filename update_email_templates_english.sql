-- Email şablonlarını İngilizce güncelle

-- Email konu şablonu
UPDATE public.late_arrival_settings 
SET setting_value = 'Late Arrival Notification - {date}' 
WHERE setting_name = 'email_template_subject';

-- Email içerik şablonu
UPDATE public.late_arrival_settings 
SET setting_value = 'Dear {name},

You were {late_minutes} minutes late on {date}.

Expected arrival time: {expected_time}
Your arrival time: {actual_time}

Please ensure punctuality in the future.

Best regards,
HR Department
Western Caspian University' 
WHERE setting_name = 'email_template_body';

-- Kontrol et
SELECT setting_name, setting_value 
FROM public.late_arrival_settings 
WHERE setting_name IN ('email_template_subject', 'email_template_body');