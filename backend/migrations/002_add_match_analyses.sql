-- Migration: Add match analyses tables
-- Date: 2025-12-29
-- Description: Replace JSON file-based match context storage with PostgreSQL tables

-- Create match_analyses table
CREATE TABLE match_analyses (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fixture_id INTEGER UNIQUE NOT NULL,
    home_team VARCHAR(255) NOT NULL,
    away_team VARCHAR(255) NOT NULL,
    league VARCHAR(255) NOT NULL,
    season INTEGER NOT NULL,
    match_date TIMESTAMP NOT NULL,
    match_status VARCHAR(10) NOT NULL,
    analyses_data JSONB NOT NULL,
    api_calls_count INTEGER DEFAULT 0,
    version VARCHAR(10) DEFAULT '2.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0
);

-- Create indexes for performance
CREATE INDEX idx_match_status_date ON match_analyses(match_status, match_date);
CREATE INDEX idx_fixture_id ON match_analyses(fixture_id);
CREATE INDEX idx_match_date ON match_analyses(match_date DESC);

-- Create match_analysis_accesses table (audit trail)
CREATE TABLE match_analysis_accesses (
    access_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES match_analyses(analysis_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE SET NULL,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for audit table
CREATE INDEX idx_analysis_accesses_analysis ON match_analysis_accesses(analysis_id);
CREATE INDEX idx_analysis_accesses_accessed_at ON match_analysis_accesses(accessed_at DESC);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_match_analysis_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_match_analysis_timestamp
BEFORE UPDATE ON match_analyses
FOR EACH ROW
EXECUTE FUNCTION update_match_analysis_timestamp();
