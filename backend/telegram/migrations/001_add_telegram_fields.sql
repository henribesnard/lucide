-- Migration: Add Telegram support to users table
-- Description: Adds fields required for Telegram bot authentication
-- Date: 2025-12-29
-- Version: 1.0.0

BEGIN;

-- Add Telegram-specific fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_id BIGINT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_username VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_first_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_last_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_language_code VARCHAR(10);

-- Make email and password optional for Telegram-only users
ALTER TABLE users ALTER COLUMN email DROP NOT NULL;
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

-- Create index for fast telegram_id lookups
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);

-- Add comments for documentation
COMMENT ON COLUMN users.telegram_id IS 'Telegram user ID (unique identifier from Telegram)';
COMMENT ON COLUMN users.telegram_username IS 'Telegram username (@username)';
COMMENT ON COLUMN users.telegram_first_name IS 'User first name from Telegram profile';
COMMENT ON COLUMN users.telegram_last_name IS 'User last name from Telegram profile';
COMMENT ON COLUMN users.telegram_language_code IS 'Language code from Telegram user (e.g., fr, en)';

COMMIT;

-- Verify migration
SELECT
    column_name,
    data_type,
    is_nullable
FROM
    information_schema.columns
WHERE
    table_name = 'users'
    AND column_name LIKE 'telegram%'
ORDER BY
    column_name;
