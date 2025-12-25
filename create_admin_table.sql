-- System Users tablosu zaten var, sadece eksik kolonları ekle
DO $$
BEGIN
    -- user_role kolonu yoksa ekle
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='system_users' AND column_name='user_role') THEN
        ALTER TABLE public.system_users ADD COLUMN user_role VARCHAR(50) DEFAULT 'user';
    END IF;
    
    -- is_active kolonu yoksa ekle
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='system_users' AND column_name='is_active') THEN
        ALTER TABLE public.system_users ADD COLUMN is_active BOOLEAN DEFAULT true;
    END IF;
    
    -- created_at kolonu yoksa ekle
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='system_users' AND column_name='created_at') THEN
        ALTER TABLE public.system_users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    -- last_login kolonu yoksa ekle
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='system_users' AND column_name='last_login') THEN
        ALTER TABLE public.system_users ADD COLUMN last_login TIMESTAMP NULL;
    END IF;
END $$;

-- Mevcut kullanıcıları admin rolü ile güncelle (eğer user_role NULL ise)
UPDATE public.system_users 
SET user_role = 'admin', is_active = true 
WHERE user_role IS NULL OR user_role = '';

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_system_users_email ON public.system_users(email);
CREATE INDEX IF NOT EXISTS idx_system_users_role ON public.system_users(user_role);
CREATE INDEX IF NOT EXISTS idx_system_users_active ON public.system_users(is_active);