-- Employee Daily Notes tablosunu oluştur
-- Bu tablo attendance sayfasında günlük notları saklamak için kullanılır

CREATE TABLE IF NOT EXISTS public.employee_daily_notes (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(255) NOT NULL,
    note_date DATE NOT NULL,
    note_text TEXT,
    created_by VARCHAR(255) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, note_date)
);

-- Index'ler
CREATE INDEX IF NOT EXISTS idx_employee_daily_notes_employee_date 
ON public.employee_daily_notes(employee_id, note_date);

CREATE INDEX IF NOT EXISTS idx_employee_daily_notes_date 
ON public.employee_daily_notes(note_date);

-- Yorum ekle
COMMENT ON TABLE public.employee_daily_notes IS 'Çalışanlar için günlük notlar tablosu';
COMMENT ON COLUMN public.employee_daily_notes.employee_id IS 'pers_person tablosundaki çalışan ID';
COMMENT ON COLUMN public.employee_daily_notes.note_date IS 'Notun ait olduğu tarih';
COMMENT ON COLUMN public.employee_daily_notes.note_text IS 'Not metni';
COMMENT ON COLUMN public.employee_daily_notes.created_by IS 'Notu oluşturan kullanıcı';

-- Test verisi (isteğe bağlı)
-- INSERT INTO public.employee_daily_notes (employee_id, note_date, note_text, created_by) 
-- VALUES (1, CURRENT_DATE, 'Test notu', 'admin');