-- pers_person tablosunun yapısını kontrol et
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'pers_person' 
  AND table_schema = 'public'
ORDER BY ordinal_position;

-- İlk birkaç kaydı göster
SELECT id, name, last_name 
FROM public.pers_person 
LIMIT 5;