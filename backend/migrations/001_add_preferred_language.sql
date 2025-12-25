-- Migration: Add preferred_language column to users table
-- Date: 2025-12-25
-- Description: Adds language preference support (FR/EN) for multilingual responses

-- Add preferred_language column with default 'fr'
ALTER TABLE users
ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(2) NOT NULL DEFAULT 'fr';

-- Add check constraint to ensure only 'fr' or 'en' values
ALTER TABLE users
ADD CONSTRAINT check_preferred_language
CHECK (preferred_language IN ('fr', 'en'));

-- Create index for performance (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_users_preferred_language
ON users(preferred_language);

-- Update existing users to have 'fr' as default if NULL
UPDATE users
SET preferred_language = 'fr'
WHERE preferred_language IS NULL;

-- Verify migration
SELECT COUNT(*) as total_users,
       preferred_language,
       COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
FROM users
GROUP BY preferred_language;
