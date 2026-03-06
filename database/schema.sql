-- Sybil-OS Database Schema
-- PostgreSQL with pgvector extension for vector similarity search

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Citizens table (main entity)
CREATE TABLE IF NOT EXISTS citizens (
    -- Primary key
    id SERIAL PRIMARY KEY,
    
    -- Identifiers
    user_id VARCHAR(255) UNIQUE NOT NULL,
    external_identity VARCHAR(255),
    
    -- Cognitive dimensions (0.0 - 1.0)
    logic_depth DOUBLE PRECISION NOT NULL CHECK (logic_depth >= 0 AND logic_depth <= 1),
    empathy_level DOUBLE PRECISION NOT NULL CHECK (empathy_level >= 0 AND empathy_level <= 1),
    stress_resilience DOUBLE PRECISION NOT NULL CHECK (stress_resilience >= 0 AND stress_resilience <= 1),
    creative_entropy DOUBLE PRECISION NOT NULL CHECK (creative_entropy >= 0 AND creative_entropy <= 1),
    social_cohesion DOUBLE PRECISION NOT NULL CHECK (social_cohesion >= 0 AND social_cohesion <= 1),
    
    -- Personality embedding vector (1536 dimensions)
    vector_summary vector(1536) NOT NULL,
    
    -- Assignment metadata
    assigned_job VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying

-- Index on user_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_citizens_user_id ON citizens(user_id);

-- Index on external_identity
CREATE INDEX IF NOT EXISTS idx_citizens_external_identity ON citizens(external_identity);

-- Index on assigned_job for filtering
CREATE INDEX IF NOT EXISTS idx_citizens_assigned_job ON citizens(assigned_job);

-- Vector index for similarity search (Cosine distance)
-- Using HNSW index for approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS idx_citizens_vector_summary 
ON citizens USING hnsw (vector_summary vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Composite index for recent updates
CREATE INDEX IF NOT EXISTS idx_citizens_updated_at ON citizens(updated_at DESC);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to update timestamp on any row update
CREATE TRIGGER update_citizens_updated_at
    BEFORE UPDATE ON citizens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE citizens IS 'Core table storing digital soul profiles of citizens';
COMMENT ON COLUMN citizens.vector_summary IS '1536-dimensional personality embedding for similarity search';
COMMENT ON INDEX idx_citizens_vector_summary IS 'HNSW index for cosine similarity search on personality vectors';
