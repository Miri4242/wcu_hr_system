-- Fix photo_path column length for Cloudinary URLs
-- Cloudinary URLs can be very long with transformations

-- Check current column definition
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'pers_person' 
AND column_name = 'photo_path';

-- Increase photo_path column length to handle long Cloudinary URLs
ALTER TABLE public.pers_person 
ALTER COLUMN photo_path TYPE VARCHAR(1000);

-- Verify the change
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'pers_person' 
AND column_name = 'photo_path';