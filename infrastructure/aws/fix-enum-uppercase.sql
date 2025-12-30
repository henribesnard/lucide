-- Corriger les enums pour utiliser les noms en majuscules
-- SQLAlchemy envoie les noms des enums, pas leurs valeurs

-- Supprimer les colonnes qui utilisent les enums
ALTER TABLE users DROP COLUMN IF EXISTS subscription_tier;
ALTER TABLE users DROP COLUMN IF EXISTS subscription_status;

-- Supprimer les enums existants
DROP TYPE IF EXISTS subscriptiontier;
DROP TYPE IF EXISTS subscriptionstatus;

-- Créer les enums avec les noms en majuscules (comme SQLAlchemy les envoie)
CREATE TYPE subscriptiontier AS ENUM ('FREE', 'BASIC', 'PREMIUM', 'ENTERPRISE');
CREATE TYPE subscriptionstatus AS ENUM ('ACTIVE', 'INACTIVE', 'CANCELLED', 'TRIAL');

-- Re-créer les colonnes avec les bons enums
ALTER TABLE users ADD COLUMN subscription_tier subscriptiontier DEFAULT 'FREE' NOT NULL;
ALTER TABLE users ADD COLUMN subscription_status subscriptionstatus DEFAULT 'ACTIVE' NOT NULL;

-- Confirmation
SELECT 'Enums corrigés avec valeurs en majuscules!' AS status;
