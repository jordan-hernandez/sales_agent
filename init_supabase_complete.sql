-- Script completo para inicializar Supabase con pgvector
-- Ejecuta todo este código en el SQL Editor de Supabase

-- 1. Habilitar la extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Verificar que pgvector está disponible
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 3. Test básico de vector
SELECT '[1,2,3]'::vector;
SELECT vector_dims('[1,2,3,4]'::vector);

-- 4. Crear funciones optimizadas para búsqueda semántica

-- Función para búsqueda de productos
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

-- Función para búsqueda en base de conocimiento
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

-- Función para búsqueda de memorias conversacionales
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

-- 5. Función para analytics de búsqueda
CREATE OR REPLACE FUNCTION get_search_analytics(
  restaurant_id_param integer,
  days_back integer DEFAULT 7
)
RETURNS TABLE (
  total_searches bigint,
  avg_search_time numeric,
  most_common_query text,
  query_count bigint
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH search_stats AS (
    SELECT 
      COUNT(*) as total,
      AVG(search_time_ms) as avg_time
    FROM search_logs 
    WHERE restaurant_id = restaurant_id_param 
      AND created_at > NOW() - INTERVAL '1 day' * days_back
  ),
  top_query AS (
    SELECT query, COUNT(*) as count
    FROM search_logs 
    WHERE restaurant_id = restaurant_id_param
      AND created_at > NOW() - INTERVAL '1 day' * days_back
    GROUP BY query
    ORDER BY count DESC
    LIMIT 1
  )
  SELECT 
    COALESCE(s.total, 0),
    COALESCE(s.avg_time, 0),
    COALESCE(t.query, 'No queries yet'),
    COALESCE(t.count, 0)
  FROM search_stats s
  FULL OUTER JOIN top_query t ON true;
END;
$$;

-- 6. Confirmar instalación
SELECT 'pgvector instalado correctamente!' as status;