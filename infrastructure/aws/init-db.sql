-- Script d'initialisation de la base de données Lucide
-- Exécuté automatiquement au premier démarrage de PostgreSQL

-- Créer les extensions nécessaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: users
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    username VARCHAR(100) UNIQUE,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_premium BOOLEAN DEFAULT FALSE,

    -- Champs Telegram
    telegram_id INTEGER UNIQUE,
    telegram_username VARCHAR(255),
    telegram_first_name VARCHAR(255),
    telegram_last_name VARCHAR(255),
    telegram_language_code VARCHAR(10),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Table: conversations
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(500),
    context_type VARCHAR(50),
    context_league_id INTEGER,
    context_match_id INTEGER,
    context_team_id INTEGER,
    context_player_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_is_active ON conversations(is_active);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);

-- Table: messages
CREATE TABLE IF NOT EXISTS messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tokens_used INTEGER,
    llm_model VARCHAR(100),
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);

-- Table: match_analyses
CREATE TABLE IF NOT EXISTS match_analyses (
    analysis_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id INTEGER NOT NULL,
    league_id INTEGER,
    home_team_id INTEGER,
    away_team_id INTEGER,
    match_date TIMESTAMP WITH TIME ZONE,

    -- Analyse générée
    summary TEXT,
    key_players JSONB,
    tactical_analysis TEXT,
    predictions JSONB,
    h2h_analysis TEXT,

    -- Métadonnées
    llm_model VARCHAR(100),
    tokens_used INTEGER,
    processing_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_match_analyses_match_id ON match_analyses(match_id);
CREATE INDEX IF NOT EXISTS idx_match_analyses_league_id ON match_analyses(league_id);
CREATE INDEX IF NOT EXISTS idx_match_analyses_expires_at ON match_analyses(expires_at);
CREATE INDEX IF NOT EXISTS idx_match_analyses_created_at ON match_analyses(created_at DESC);

-- Table: match_analysis_accesses
CREATE TABLE IF NOT EXISTS match_analysis_accesses (
    access_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES match_analyses(analysis_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE SET NULL,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_accesses_analysis_id ON match_analysis_accesses(analysis_id);
CREATE INDEX IF NOT EXISTS idx_accesses_user_id ON match_analysis_accesses(user_id);
CREATE INDEX IF NOT EXISTS idx_accesses_accessed_at ON match_analysis_accesses(accessed_at DESC);

-- Fonction pour mettre à jour automatiquement updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_match_analyses_updated_at BEFORE UPDATE ON match_analyses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Afficher les tables créées
DO $$
BEGIN
    RAISE NOTICE 'Database initialization complete!';
    RAISE NOTICE 'Tables created: users, conversations, messages, match_analyses, match_analysis_accesses';
END $$;
