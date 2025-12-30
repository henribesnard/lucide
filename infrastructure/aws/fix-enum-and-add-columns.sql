-- Corriger les enums et ajouter les colonnes subscription
-- Les enums doivent être en minuscules pour correspondre à SQLAlchemy

-- Supprimer les enums existants (en majuscules)
DROP TYPE IF EXISTS subscriptiontier CASCADE;
DROP TYPE IF EXISTS subscriptionstatus CASCADE;

-- Créer les enums avec les bonnes valeurs (minuscules)
CREATE TYPE subscriptiontier AS ENUM ('free', 'basic', 'premium', 'enterprise');
CREATE TYPE subscriptionstatus AS ENUM ('active', 'inactive', 'cancelled', 'trial');

-- Ajouter les colonnes subscription
ALTER TABLE users ADD COLUMN subscription_tier subscriptiontier DEFAULT 'free' NOT NULL;
ALTER TABLE users ADD COLUMN subscription_status subscriptionstatus DEFAULT 'active' NOT NULL;

-- Confirmation
SELECT 'Enums corrigés et colonnes ajoutées avec succès!' AS status;
