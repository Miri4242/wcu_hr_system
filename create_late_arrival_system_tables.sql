-- Gecikme Takip Sistemi Database Tabloları
-- Bu tablolar pers_person tablosuna bağlı olarak çalışır

-- 1. Gecikme Kayıtları Tablosu
CREATE TABLE IF NOT EXISTS public.employee_late_arrivals (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(255) NOT NULL,
    late_date DATE NOT NULL,
    expected_arrival_time TIME DEFAULT '09:00:00',
    actual_arrival_time TIME,
    late_minutes INTEGER NOT NULL DEFAULT 0,
    late_reason TEXT,
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- pers_person tablosuna referans (soft reference - string olarak)
    CONSTRAINT unique_employee_late_date UNIQUE(employee_id, late_date)
);

-- 2. Email Geçmişi Tablosu
CREATE TABLE IF NOT EXISTS public.late_arrival_emails (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(255) NOT NULL,
    late_arrival_id INTEGER REFERENCES public.employee_late_arrivals(id) ON DELETE CASCADE,
    employee_name VARCHAR(500),
    employee_email VARCHAR(255),
    email_subject VARCHAR(500),
    email_body TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_status VARCHAR(50) DEFAULT 'sent', -- sent, failed, pending
    error_message TEXT
);

-- 3. Gecikme Sistemi Ayarları Tablosu
CREATE TABLE IF NOT EXISTS public.late_arrival_settings (
    id SERIAL PRIMARY KEY,
    setting_name VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255) DEFAULT 'admin'
);

-- 4. Gecikme İstatistikleri Tablosu (Aylık özet)
CREATE TABLE IF NOT EXISTS public.employee_late_statistics (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_late_days INTEGER DEFAULT 0,
    total_late_minutes INTEGER DEFAULT 0,
    average_late_minutes DECIMAL(5,2) DEFAULT 0.00,
    max_late_minutes INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_employee_month_stats UNIQUE(employee_id, year, month)
);

-- Index'ler
CREATE INDEX IF NOT EXISTS idx_late_arrivals_employee_date 
ON public.employee_late_arrivals(employee_id, late_date);

CREATE INDEX IF NOT EXISTS idx_late_arrivals_date 
ON public.employee_late_arrivals(late_date);

CREATE INDEX IF NOT EXISTS idx_late_arrivals_email_status 
ON public.employee_late_arrivals(email_sent, late_date);

CREATE INDEX IF NOT EXISTS idx_late_statistics_employee_period 
ON public.employee_late_statistics(employee_id, year, month);

CREATE INDEX IF NOT EXISTS idx_late_emails_employee 
ON public.late_arrival_emails(employee_id);

CREATE INDEX IF NOT EXISTS idx_late_emails_date 
ON public.late_arrival_emails(sent_at);

-- Varsayılan sistem ayarları
INSERT INTO public.late_arrival_settings (setting_name, setting_value, setting_description) VALUES
('work_start_time', '09:00:00', 'Günlük çalışma başlangıç saati'),
('late_threshold_minutes', '15', 'Gecikme sayılacak minimum dakika'),
('email_enabled', 'true', 'Email gönderimi aktif/pasif'),
('check_interval_minutes', '30', 'Gecikme kontrolü yapılma aralığı (dakika)'),
('smtp_server', '', 'SMTP sunucu adresi'),
('smtp_port', '587', 'SMTP port numarası'),
('smtp_username', '', 'SMTP kullanıcı adı'),
('smtp_password', '', 'SMTP şifre'),
('from_email', 'hr@company.com', 'Gönderen email adresi'),
('email_template_subject', 'Gecikme Bildirimi - {date}', 'Email konu şablonu'),
('email_template_body', 'Sayın {name},\n\n{date} tarihinde {late_minutes} dakika geç geldiniz.\nBeklenen saat: {expected_time}\nGeldiğiniz saat: {actual_time}\n\nİyi çalışmalar.', 'Email içerik şablonu'),
('auto_check_enabled', 'true', 'Otomatik gecikme kontrolü aktif/pasif'),
('weekend_check_enabled', 'false', 'Hafta sonu gecikme kontrolü'),
('holiday_check_enabled', 'false', 'Tatil günleri gecikme kontrolü')
ON CONFLICT (setting_name) DO NOTHING;

-- Yorumlar
COMMENT ON TABLE public.employee_late_arrivals IS 'Çalışan gecikme kayıtları tablosu';
COMMENT ON TABLE public.late_arrival_emails IS 'Gecikme bildirimi email geçmişi';
COMMENT ON TABLE public.late_arrival_settings IS 'Gecikme sistemi ayarları';
COMMENT ON TABLE public.employee_late_statistics IS 'Aylık gecikme istatistikleri';

COMMENT ON COLUMN public.employee_late_arrivals.employee_id IS 'pers_person tablosundaki çalışan ID (string)';
COMMENT ON COLUMN public.employee_late_arrivals.late_minutes IS 'Gecikme süresi (dakika)';
COMMENT ON COLUMN public.employee_late_arrivals.email_sent IS 'Email gönderildi mi?';
COMMENT ON COLUMN public.late_arrival_emails.email_status IS 'Email durumu: sent, failed, pending';

-- Test verisi ekleme (isteğe bağlı - yorumdan çıkarabilirsin)
/*
-- Örnek gecikme kaydı
INSERT INTO public.employee_late_arrivals 
(employee_id, late_date, expected_arrival_time, actual_arrival_time, late_minutes, email_sent) 
VALUES 
('test-employee-1', CURRENT_DATE, '09:00:00', '09:25:00', 25, false);

-- Örnek email kaydı
INSERT INTO public.late_arrival_emails 
(employee_id, late_arrival_id, employee_name, employee_email, email_subject, email_body, email_status) 
VALUES 
('test-employee-1', 1, 'Test Employee', 'test@company.com', 'Gecikme Bildirimi', 'Test email content', 'sent');
*/