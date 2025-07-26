-- Script to enable pgvector extension in PostgreSQL
-- Run this as superuser before running migrations

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';