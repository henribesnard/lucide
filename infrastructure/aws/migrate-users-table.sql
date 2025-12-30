-- Migration pour ajouter les colonnes manquantes à la table users
-- Exécuté le: 2025-12-30

-- Créer les types ENUM s'ils n'existent pas
DO $$ BEGIN
    CREATE TYPE subscriptiontier AS ENUM ('free', 'basic', 'premium', 'enterprise');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE subscriptionstatus AS ENUM ('active', 'inactive', 'cancelled', 'trial');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Ajouter les colonnes manquantes
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100) DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(100) DEFAULT '';

ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN DEFAULT FALSE NOT NULL;

ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier subscriptiontier DEFAULT 'free' NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status subscriptionstatus DEFAULT 'active' NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_end_date TIMESTAMP WITH TIME ZONE;

ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(2) DEFAULT 'fr' NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;

ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token_expires TIMESTAMP WITH TIME ZONE;

ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP WITH TIME ZONE;

-- Supprimer la contrainte NOT NULL sur first_name et last_name
-- (car ces colonnes peuvent être vides si l'utilisateur vient de Telegram uniquement)
ALTER TABLE users ALTER COLUMN first_name DROP NOT NULL;
ALTER TABLE users ALTER COLUMN last_name DROP NOT NULL;

-- Message de confirmation
SELECT 'Migration terminée avec succès!' AS status;
