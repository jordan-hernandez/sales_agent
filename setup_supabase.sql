-- Script to setup pgvector functionality in Supabase
-- Run this in the Supabase SQL Editor

-- Enable the pgvector extension (already enabled in Supabase by default)
-- This is just for reference - Supabase has it pre-installed
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Verify pgvector is available
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Create a test vector to verify functionality  
SELECT '[1,2,3]'::vector;

-- Test vector operations
SELECT vector_dims('[1,2,3,4]'::vector);
SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector as l2_distance;
SELECT '[1,2,3]'::vector <=> '[1,2,4]'::vector as cosine_distance;

-- Enable Row Level Security (RLS) for vector tables if needed
-- This will be done after creating tables via migrations

-- Create custom vector search functions for better performance
CREATE OR REPLACE FUNCTION match_products(
  query_embedding vector(384),
  restaurant_id_param integer,
  match_threshold float DEFAULT 0.3,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  product_id integer,
  name text,
  description text,
  price real,
  category text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    pe.product_id,
    p.name,
    p.description,
    p.price,
    p.category,
    1 - (pe.embedding <=> query_embedding) as similarity
  FROM product_embeddings pe
  JOIN products p ON pe.product_id = p.id
  WHERE pe.restaurant_id = restaurant_id_param
    AND p.available = true
    AND 1 - (pe.embedding <=> query_embedding) > match_threshold
  ORDER BY pe.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Create function for knowledge base search
CREATE OR REPLACE FUNCTION match_knowledge(
  query_embedding vector(384),
  restaurant_id_param integer,
  match_threshold float DEFAULT 0.4,
  match_count int DEFAULT 3
)
RETURNS TABLE (
  id integer,
  question text,
  answer text,
  category text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    kb.id,
    kb.question,
    kb.answer,
    kb.category,
    1 - (kb.embedding <=> query_embedding) as similarity
  FROM knowledge_base kb
  WHERE kb.restaurant_id = restaurant_id_param
    AND kb.active = true
    AND 1 - (kb.embedding <=> query_embedding) > match_threshold
  ORDER BY kb.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Create function for memory search
CREATE OR REPLACE FUNCTION match_memories(
  query_embedding vector(384),
  customer_phone_param text,
  restaurant_id_param integer,
  match_count int DEFAULT 3
)
RETURNS TABLE (
  id integer,
  memory_type text,
  content text,
  summary text,
  importance_score real,
  similarity float,
  created_at timestamptz
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    cm.id,
    cm.memory_type,
    cm.content,
    cm.summary,
    cm.importance_score,
    1 - (cm.embedding <=> query_embedding) as similarity,
    cm.created_at
  FROM conversation_memories cm
  WHERE cm.customer_phone = customer_phone_param
    AND cm.restaurant_id = restaurant_id_param
  ORDER BY 
    cm.importance_score DESC,
    cm.embedding <=> query_embedding,
    cm.created_at DESC
  LIMIT match_count;
END;
$$;

-- Create indexes for better performance (run after creating tables)
-- These will be created after running the migrations

-- Notifications for real-time updates (optional)
-- You can enable these if you want real-time notifications when embeddings are updated
-- ALTER TABLE product_embeddings ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversation_memories ENABLE ROW LEVEL SECURITY;